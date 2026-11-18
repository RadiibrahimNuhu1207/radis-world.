"""Radi's World — data models.

Content types: HistoryEntry (with translations + narrations), Video (Radi Stories, from YouTube),
Audiobook (+ chapters), Comic (+ pages). English is the default language.
"""
import re

from django.db import models

LANGUAGES = [
    ("en", "English"),
    ("sw", "Kiswahili"),
    ("fr", "Français"),
    ("ar", "العربية"),
    ("ko", "한국어"),
    ("ja", "日本語"),
    ("zh", "中文"),
    ("es", "Español"),
]
TOPICS = [(c, c) for c in ["Tanzania", "Afrika", "Dunia", "Sayansi", "Michezo", "Bahari"]]
REGIONS = [
    ("tanzania", "Tanzania"), ("east_africa", "East Africa"), ("africa", "Africa"),
    ("europe", "Europe"), ("asia", "Asia"), ("middle_east", "Middle East"),
    ("americas", "Americas"), ("oceania", "Oceania"), ("world", "World"), ("space", "Space"),
]
VOICES = [("female", "Female"), ("male", "Male"), ("child", "Child")]

MONTHS = {
    "en": ["January", "February", "March", "April", "May", "June", "July", "August", "September", "October", "November", "December"],
    "sw": ["Januari", "Februari", "Machi", "Aprili", "Mei", "Juni", "Julai", "Agosti", "Septemba", "Oktoba", "Novemba", "Desemba"],
    "fr": ["janvier", "février", "mars", "avril", "mai", "juin", "juillet", "août", "septembre", "octobre", "novembre", "décembre"],
    "es": ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"],
    "ar": ["يناير", "فبراير", "مارس", "أبريل", "مايو", "يونيو", "يوليو", "أغسطس", "سبتمبر", "أكتوبر", "نوفمبر", "ديسمبر"],
}


def date_label(day, month, lang="en"):
    if lang in ("ja", "zh"):
        return f"{month}月{day}日"
    if lang == "ko":
        return f"{month}월 {day}일"
    if lang == "en":
        return f"{MONTHS['en'][month - 1]} {day}"
    m = MONTHS.get(lang, MONTHS["en"])[month - 1]
    return f"{day} de {m}" if lang == "es" else f"{day} {m}"


class Status(models.TextChoices):
    DRAFT = "draft", "Draft (not visible)"
    PUBLISHED = "published", "Published"


def url(f):
    return f.url if f else ""


# ---------------------------------------------------------------- history
class HistoryEntry(models.Model):
    """One moment in world history. Base text is English; other languages live in translations."""

    slug = models.SlugField(unique=True)
    year = models.IntegerField(help_text="Negative for BCE, e.g. -2560")
    circa = models.BooleanField(default=False, help_text="Approximate year (shown as 'c.')")
    month = models.PositiveSmallIntegerField(null=True, blank=True, help_text="Optional — needed for 'On this day'")
    day = models.PositiveSmallIntegerField(null=True, blank=True)
    title = models.CharField("title (English)", max_length=200)
    place = models.CharField("place (English)", max_length=120, blank=True)
    text = models.TextField("story (English)")
    topic = models.CharField(max_length=20, choices=TOPICS)
    region = models.CharField(max_length=20, choices=REGIONS)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    featured = models.BooleanField(default=False)
    video_vertical = models.FileField(upload_to="history/videos/", blank=True, help_text="9:16 video")
    video_horizontal = models.FileField(upload_to="history/videos/", blank=True, help_text="16:9 video")
    image_vertical = models.ImageField(upload_to="history/images/", blank=True)
    image_horizontal = models.ImageField(upload_to="history/images/", blank=True)
    sources = models.TextField(blank=True, help_text="Where the facts come from (not shown to users)")
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["year", "month", "day"]
        verbose_name_plural = "history entries"

    def __str__(self):
        return f"{self.year} — {self.title}"

    def localized(self, lang):
        for t in self.translations.all():
            if t.lang == lang:
                return t.title or self.title, t.place or self.place, t.text or self.text
        return self.title, self.place, self.text

    def as_dict(self):
        tr = {"en": {"title": self.title, "place": self.place, "text": self.text}}
        tr.update({t.lang: {"title": t.title, "place": t.place, "text": t.text} for t in self.translations.all()})
        return {
            "id": self.slug, "y": self.year, "circa": self.circa,
            "d": f"{self.day:02d}-{self.month:02d}" if self.day and self.month else None,
            "m": self.month, "cat": self.topic, "region": self.region, "featured": self.featured, "tr": tr,
            "v916": url(self.video_vertical), "v169": url(self.video_horizontal),
            "h916": url(self.image_vertical), "h169": url(self.image_horizontal),
            "narr": [{"lang": n.lang, "voice": n.voice, "url": n.audio.url, "by": n.narrator} for n in self.narrations.all() if n.audio],
        }


class HistoryTranslation(models.Model):
    entry = models.ForeignKey(HistoryEntry, on_delete=models.CASCADE, related_name="translations")
    lang = models.CharField(max_length=5, choices=LANGUAGES[1:])
    title = models.CharField(max_length=200)
    place = models.CharField(max_length=120, blank=True)
    text = models.TextField()

    class Meta:
        unique_together = ("entry", "lang")
        ordering = ["lang"]


class Narration(models.Model):
    """A recorded (or AI-generated) reading of a history story in one language and voice."""

    entry = models.ForeignKey(HistoryEntry, on_delete=models.CASCADE, related_name="narrations")
    lang = models.CharField(max_length=5, choices=LANGUAGES)
    voice = models.CharField(max_length=10, choices=VOICES)
    audio = models.FileField(upload_to="history/narrations/")
    narrator = models.CharField(max_length=80, blank=True, help_text="e.g. Radi, or the AI voice name")

    class Meta:
        unique_together = ("entry", "lang", "voice")
        ordering = ["lang", "voice"]


# ---------------------------------------------------------------- Radi Stories (YouTube)
YOUTUBE_ID = re.compile(r"(?:v=|youtu\.be/|shorts/|embed/|live/)([A-Za-z0-9_-]{11})")


class Video(models.Model):
    class Kind(models.TextChoices):
        STORY = "story", "Story (hadithi)"
        FEATURE = "feature", "Feature (makala)"
        SHORT = "short", "Short"
        OTHER = "other", "Other"

    youtube_id = models.CharField(max_length=11, unique=True, help_text="Paste a YouTube link — the id is taken from it")
    title = models.CharField(max_length=255, blank=True)
    description = models.TextField(blank=True)
    kind = models.CharField(max_length=10, choices=Kind.choices, default=Kind.STORY)
    language = models.CharField(max_length=5, choices=LANGUAGES, default="sw")
    published = models.DateTimeField(null=True, blank=True)
    featured = models.BooleanField(default=False)
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PUBLISHED)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-published", "-created"]

    def __str__(self):
        return self.title or self.youtube_id

    @staticmethod
    def extract_id(value):
        value = (value or "").strip()
        m = YOUTUBE_ID.search(value)
        if m:
            return m.group(1)
        return value if re.fullmatch(r"[A-Za-z0-9_-]{11}", value) else None

    def as_dict(self):
        return {
            "id": self.youtube_id, "title": self.title, "desc": self.description[:600], "kind": self.kind,
            "lang": self.language, "featured": self.featured,
            "date": self.published.date().isoformat() if self.published else None,
            "thumb": f"https://i.ytimg.com/vi/{self.youtube_id}/hqdefault.jpg",
        }


# ---------------------------------------------------------------- audiobooks
class Audiobook(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120, default="Radi the Storyteller")
    narrator = models.CharField(max_length=120, blank=True)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="audiobooks/covers/", blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGES, default="sw")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def as_dict(self):
        return {
            "id": self.slug, "title": self.title, "author": self.author, "narrator": self.narrator,
            "desc": self.description, "cover": url(self.cover), "lang": self.language, "featured": self.featured,
            "chapters": [{"title": c.title, "url": c.audio.url, "min": c.minutes} for c in self.chapters.all() if c.audio],
        }


class Chapter(models.Model):
    audiobook = models.ForeignKey(Audiobook, on_delete=models.CASCADE, related_name="chapters")
    order = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=200)
    audio = models.FileField(upload_to="audiobooks/audio/")
    minutes = models.PositiveSmallIntegerField(default=0, help_text="Length in minutes (optional)")

    class Meta:
        ordering = ["order"]


# ---------------------------------------------------------------- comics
class Comic(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="comics/covers/", blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGES, default="sw")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created"]

    def __str__(self):
        return self.title

    def as_dict(self):
        pages = [p.image.url for p in self.pages.all() if p.image]
        return {"id": self.slug, "title": self.title, "desc": self.description, "lang": self.language,
                "cover": url(self.cover) or (pages[0] if pages else ""), "featured": self.featured, "pages": pages}


class ComicPage(models.Model):
    comic = models.ForeignKey(Comic, on_delete=models.CASCADE, related_name="pages")
    order = models.PositiveSmallIntegerField(default=1)
    image = models.ImageField(upload_to="comics/pages/")

    class Meta:
        ordering = ["order"]


# ---------------------------------------------------------------- books (e-books)
class Ebook(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=120, default="Radi the Storyteller")
    description = models.TextField(blank=True)
    cover = models.ImageField(upload_to="books/covers/", blank=True)
    pdf = models.FileField(upload_to="books/pdf/", blank=True,
                           help_text="Upload the book as a PDF (Word: File → Save as PDF). Or leave empty and type chapters below.")
    allow_download = models.BooleanField(default=False, help_text="Show a Download button for the PDF")
    language = models.CharField(max_length=5, choices=LANGUAGES, default="sw")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-featured", "-created"]

    def __str__(self):
        return self.title

    def as_dict(self):
        return {"id": self.slug, "title": self.title, "author": self.author, "desc": self.description,
                "cover": url(self.cover), "pdf": url(self.pdf), "dl": self.allow_download and bool(self.pdf),
                "lang": self.language, "featured": self.featured,
                "chapters": [{"title": c.title, "text": c.text} for c in self.chapters.all()]}


class BookChapter(models.Model):
    book = models.ForeignKey(Ebook, on_delete=models.CASCADE, related_name="chapters")
    order = models.PositiveSmallIntegerField(default=1)
    title = models.CharField(max_length=200, blank=True)
    text = models.TextField()

    class Meta:
        ordering = ["order"]


# ---------------------------------------------------------------- art
ART_KINDS = [("illustration", "Illustration"), ("painting", "Painting"), ("poem", "Poem"),
             ("photo", "Photo"), ("design", "Design"), ("other", "Other")]


class Artwork(models.Model):
    slug = models.SlugField(unique=True)
    title = models.CharField(max_length=200)
    kind = models.CharField(max_length=20, choices=ART_KINDS, default="illustration")
    image = models.ImageField(upload_to="art/", blank=True, help_text="The artwork (optional for a poem)")
    text = models.TextField(blank=True, help_text="For poems or written pieces")
    description = models.TextField(blank=True)
    language = models.CharField(max_length=5, choices=LANGUAGES, default="sw")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.DRAFT)
    featured = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-featured", "-created"]

    def __str__(self):
        return self.title

    def as_dict(self):
        return {"id": self.slug, "title": self.title, "kind": self.kind, "image": url(self.image), "text": self.text,
                "desc": self.description, "lang": self.language, "featured": self.featured}


# ---------------------------------------------------------------- notifications
class PushSubscription(models.Model):
    endpoint = models.URLField(max_length=600, unique=True)
    p256dh = models.CharField(max_length=200)
    auth = models.CharField(max_length=100)
    lang = models.CharField(max_length=5, choices=LANGUAGES, default="en")
    topics = models.CharField(max_length=200, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    last_sent = models.DateField(null=True, blank=True)
    failures = models.PositiveSmallIntegerField(default=0)

    def __str__(self):
        return self.endpoint[:60]
