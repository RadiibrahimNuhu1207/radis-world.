import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import (LANGUAGES, REGIONS, TOPICS, Artwork, Audiobook, Comic, Ebook, HistoryEntry, MusicTrack, PushSubscription,
                     Status, Video)

PUB = Status.PUBLISHED


def app_data():
    return {
        "topics": [t for t, _ in TOPICS],
        "regions": [r for r, _ in REGIONS],
        "history": [e.as_dict() for e in HistoryEntry.objects.filter(status=PUB)
                    .prefetch_related("translations", "narrations")],
        "videos": [v.as_dict() for v in Video.objects.filter(status=PUB)],
        "audiobooks": [a.as_dict() for a in Audiobook.objects.filter(status=PUB).prefetch_related("chapters")],
        "comics": [c.as_dict() for c in Comic.objects.filter(status=PUB).prefetch_related("pages")],
        "books": [b.as_dict() for b in Ebook.objects.filter(status=PUB).prefetch_related("chapters")],
        "art": [a.as_dict() for a in Artwork.objects.filter(status=PUB)],
        "music": [m.as_dict() for m in MusicTrack.objects.filter(status=PUB)],
        "channel": settings.YOUTUBE_CHANNEL, "channel_id": settings.YOUTUBE_CHANNEL_ID,
    }


@ensure_csrf_cookie
def home(request):
    return render(request, "world/index.html", {"data": app_data(), "vapid_public_key": settings.VAPID_PUBLIC_KEY})


def share_history(request, slug):
    e = get_object_or_404(HistoryEntry, slug=slug, status=PUB)
    img = e.image_horizontal or e.artwork or e.image_vertical
    return render(request, "world/share.html", {
        "title": e.title, "desc": e.text, "body": e.text, "target": f"/#h-{e.slug}", "kind": "History",
        "image": img.url if img else "", "lang": "en",
    })


def share_book(request, slug):
    b = get_object_or_404(Ebook, slug=slug, status=PUB)
    return render(request, "world/share.html", {
        "title": b.title, "desc": b.description or b.title, "body": b.description, "target": f"/#b-{b.slug}",
        "kind": "Book", "author": b.author, "image": b.cover.url if b.cover else "", "lang": b.language, "tall": True,
    })


def share_comic(request, slug):
    c = get_object_or_404(Comic, slug=slug, status=PUB)
    first = c.pages.first()
    img = c.cover.url if c.cover else (first.image.url if first and first.image else "")
    return render(request, "world/share.html", {
        "title": c.title, "desc": c.description or c.title, "body": c.description, "target": f"/#c-{c.slug}",
        "kind": "Comic", "image": img, "lang": c.language, "tall": True,
    })


def sitemap(request):
    base = f"{request.scheme}://{request.get_host()}"
    rows = [(f"{base}/", None)]
    rows += [(f"{base}/book/{b.slug}/", b.created) for b in Ebook.objects.filter(status=PUB)]
    rows += [(f"{base}/comic/{c.slug}/", c.created) for c in Comic.objects.filter(status=PUB)]
    rows += [(f"{base}/history/{e.slug}/", e.updated) for e in HistoryEntry.objects.filter(status=PUB)]
    rows += [(f"{base}/watch/{v.youtube_id}/", v.created) for v in Video.objects.filter(status=PUB)]
    xml = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for loc, when in rows:
        xml.append(f"<url><loc>{loc}</loc>" + (f"<lastmod>{when:%Y-%m-%d}</lastmod>" if when else "") + "</url>")
    xml.append("</urlset>")
    return HttpResponse("\n".join(xml), content_type="application/xml")


def robots(request):
    base = f"{request.scheme}://{request.get_host()}"
    return HttpResponse(f"User-agent: *\nAllow: /\nDisallow: /admin/\n\nSitemap: {base}/sitemap.xml\n", content_type="text/plain")


def share_video(request, vid):
    v = get_object_or_404(Video, youtube_id=vid, status=PUB)
    return render(request, "world/share.html", {
        "title": v.title, "desc": v.description, "body": v.description, "target": f"/#v-{v.youtube_id}", "kind": "Video",
        "image": f"https://i.ytimg.com/vi/{v.youtube_id}/hqdefault.jpg",
    })


def api_data(request):
    return JsonResponse(app_data(), json_dumps_params={"ensure_ascii": False})


@require_POST
def api_subscribe(request):
    try:
        body = json.loads(request.body)
        sub, keys = body["subscription"], body["subscription"]["keys"]
    except (KeyError, ValueError, TypeError):
        return HttpResponseBadRequest("bad subscription")
    lang = body.get("lang") if body.get("lang") in dict(LANGUAGES) else "en"
    topics = ",".join(t for t in body.get("topics", []) if t in dict(TOPICS))
    PushSubscription.objects.update_or_create(
        endpoint=sub["endpoint"],
        defaults={"p256dh": keys["p256dh"], "auth": keys["auth"], "lang": lang, "topics": topics, "failures": 0})
    return JsonResponse({"ok": True})


@require_POST
def api_unsubscribe(request):
    try:
        endpoint = json.loads(request.body)["endpoint"]
    except (KeyError, ValueError, TypeError):
        return HttpResponseBadRequest("bad request")
    PushSubscription.objects.filter(endpoint=endpoint).delete()
    return JsonResponse({"ok": True})


def manifest(request):
    data = {
        "name": "Radi's World", "short_name": "Radi's World",
        "description": "Stories, history, books, audiobooks, comics and art by Radi the Storyteller.",
        "lang": "en", "start_url": "/", "scope": "/", "display": "standalone", "orientation": "any",
        "background_color": "#0B0F1A", "theme_color": "#0B0F1A",
        "icons": [
            {"src": static("world/icons/icon-192.png"), "sizes": "192x192", "type": "image/png"},
            {"src": static("world/icons/icon-512.png"), "sizes": "512x512", "type": "image/png"},
            {"src": static("world/icons/icon-512.png"), "sizes": "512x512", "type": "image/png", "purpose": "maskable"},
        ],
    }
    return JsonResponse(data, content_type="application/manifest+json", json_dumps_params={"ensure_ascii": False})


@cache_control(no_cache=True)
def service_worker(request):
    shell = [static(f"world/{p}") for p in ("i18n.js", "sfx/flip1.mp3", "sfx/flip2.mp3", "sfx/flip3.mp3",
                                            "sfx/open.mp3", "sfx/close.mp3", "icons/icon-192.png")]
    js = render(request, "world/sw.js", {"shell": shell}).content
    return HttpResponse(js, content_type="application/javascript")
