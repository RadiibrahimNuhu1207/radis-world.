import json
import urllib.parse
import urllib.request

from django import forms
from django.contrib import admin, messages
from django.utils.html import format_html

from .models import (Artwork, Audiobook, BookChapter, Chapter, Ebook, Comic, ComicPage, HistoryEntry, HistoryTranslation, Narration,
                     PushSubscription, Status, Video)

admin.site.site_header = "Radi's World — Admin"
admin.site.site_title = "Radi's World"
admin.site.index_title = "Stories, history, books, audiobooks, comics and art"


@admin.action(description="Publish selected")
def publish(modeladmin, request, qs):
    qs.update(status=Status.PUBLISHED)


@admin.action(description="Generate cover with AI (up to 3 at a time)")
def ai_cover(modeladmin, request, qs):
    from .ai_cover import AICoverError, make_cover
    done = 0
    for obj in qs[:3]:
        try:
            make_cover(obj); done += 1
        except AICoverError as e:
            modeladmin.message_user(request, f"{obj}: {e}", messages.ERROR)
            break
    if done:
        modeladmin.message_user(request, f"Created {done} new cover(s). Open the item to see it.", messages.SUCCESS)


@admin.action(description="Move selected back to draft")
def unpublish(modeladmin, request, qs):
    qs.update(status=Status.DRAFT)


# ---------------------------------------------------------------- history
class TranslationInline(admin.StackedInline):
    model = HistoryTranslation
    extra = 0
    verbose_name_plural = "Translations — Kiswahili, Français, العربية, 한국어, 日本語, 中文, Español"


class NarrationInline(admin.TabularInline):
    model = Narration
    extra = 0
    verbose_name_plural = "Narrations — upload a voice recording per language (female / male / child)"


@admin.register(HistoryEntry)
class HistoryEntryAdmin(admin.ModelAdmin):
    inlines = [TranslationInline, NarrationInline]
    list_display = ("year_col", "title", "topic", "region", "status", "featured", "langs", "voices")
    list_display_links = ("title",)
    list_editable = ("status", "featured")
    list_filter = ("status", "topic", "region", "featured")
    search_fields = ("title", "text", "place", "slug")
    prepopulated_fields = {"slug": ("title",)}
    actions = [publish, unpublish, ai_cover]
    fieldsets = (
        ("When", {"fields": (("year", "circa", "undated"), ("month", "day"))}),
        ("Story (English)", {"fields": ("title", "slug", "place", "text", "topic", "region", "sources")}),
        ("Publishing", {"fields": ("status", "featured")}),
        ("Artwork", {"fields": ("artwork",)}),
        ("Video", {"fields": (("image_vertical", "image_horizontal"), ("video_vertical", "video_horizontal"))}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).prefetch_related("translations", "narrations")

    @admin.display(description="Year", ordering="year")
    def year_col(self, o):
        y = f"{abs(o.year)} BCE" if o.year < 0 else str(o.year)
        return ("c. " if o.circa else "") + y

    @admin.display(description="Languages")
    def langs(self, o):
        return " ".join(["EN"] + sorted(t.lang.upper() for t in o.translations.all()))

    @admin.display(description="Voices")
    def voices(self, o):
        return ", ".join(f"{n.lang}/{n.voice}" for n in o.narrations.all()) or "—"


# ---------------------------------------------------------------- videos
class VideoForm(forms.ModelForm):
    youtube_id = forms.CharField(label="YouTube link or id", help_text="Paste the full link, e.g. https://youtu.be/abc123XYZ00")

    class Meta:
        model = Video
        fields = "__all__"

    def clean_youtube_id(self):
        vid = Video.extract_id(self.cleaned_data["youtube_id"])
        if not vid:
            raise forms.ValidationError("That doesn't look like a YouTube link.")
        return vid


def oembed_title(video_id):
    """Fetch the video title from YouTube (no API key needed). Returns '' if YouTube can't be reached."""
    try:
        q = urllib.parse.urlencode({"url": f"https://www.youtube.com/watch?v={video_id}", "format": "json"})
        with urllib.request.urlopen(f"https://www.youtube.com/oembed?{q}", timeout=8) as r:
            return json.loads(r.read().decode()).get("title", "")
    except Exception:
        return ""


@admin.register(Video)
class VideoAdmin(admin.ModelAdmin):
    form = VideoForm
    list_display = ("thumb", "title", "kind", "language", "published", "status", "featured")
    list_display_links = ("title",)
    list_editable = ("kind", "status", "featured")
    list_filter = ("kind", "language", "status")
    search_fields = ("title", "description", "youtube_id")
    actions = [publish, unpublish]

    @admin.display(description="")
    def thumb(self, o):
        return format_html('<img src="https://i.ytimg.com/vi/{}/mqdefault.jpg" style="height:45px;border-radius:4px">', o.youtube_id)

    def save_model(self, request, obj, form, change):
        if not obj.title:
            obj.title = oembed_title(obj.youtube_id)
            if not obj.title:
                messages.warning(request, "Couldn't fetch the title from YouTube — please type it in.")
        super().save_model(request, obj, form, change)


# ---------------------------------------------------------------- audiobooks & comics
class ChapterInline(admin.TabularInline):
    model = Chapter
    extra = 1


@admin.register(Audiobook)
class AudiobookAdmin(admin.ModelAdmin):
    inlines = [ChapterInline]
    list_display = ("title", "author", "language", "status", "featured", "chapter_count")
    list_editable = ("status", "featured")
    prepopulated_fields = {"slug": ("title",)}
    actions = [publish, unpublish, ai_cover]

    @admin.display(description="Chapters")
    def chapter_count(self, o):
        return o.chapters.count()


class ComicPageInline(admin.TabularInline):
    model = ComicPage
    extra = 3


@admin.register(Comic)
class ComicAdmin(admin.ModelAdmin):
    inlines = [ComicPageInline]
    list_display = ("title", "language", "status", "featured", "page_count")
    list_editable = ("status", "featured")
    prepopulated_fields = {"slug": ("title",)}
    actions = [publish, unpublish, ai_cover]

    @admin.display(description="Pages")
    def page_count(self, o):
        return o.pages.count()


@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("created", "lang", "topics", "last_sent", "failures")
    readonly_fields = ("endpoint", "p256dh", "auth", "created", "last_sent", "failures")


# ---------------------------------------------------------------- books + art
class BookChapterInline(admin.StackedInline):
    model = BookChapter
    extra = 0


@admin.register(Ebook)
class EbookAdmin(admin.ModelAdmin):
    inlines = [BookChapterInline]
    list_display = ("title", "author", "language", "has_pdf", "status", "featured")
    list_editable = ("status", "featured")
    prepopulated_fields = {"slug": ("title",)}
    actions = [publish, unpublish, ai_cover]

    @admin.display(boolean=True, description="PDF")
    def has_pdf(self, o):
        return bool(o.pdf)


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    list_display = ("title", "kind", "language", "status", "featured", "thumb")
    list_editable = ("status", "featured")
    list_filter = ("kind", "status")
    prepopulated_fields = {"slug": ("title",)}
    actions = [publish, unpublish]

    @admin.display(description="")
    def thumb(self, o):
        return format_html('<img src="{}" style="height:40px;border-radius:4px">', o.image.url) if o.image else ""
