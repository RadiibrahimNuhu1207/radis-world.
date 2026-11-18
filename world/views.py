import json

from django.conf import settings
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.templatetags.static import static
from django.views.decorators.cache import cache_control
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_POST

from .models import (LANGUAGES, REGIONS, TOPICS, Artwork, Audiobook, Comic, Ebook, HistoryEntry, PushSubscription, Status,
                     Video)

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
        "channel": settings.YOUTUBE_CHANNEL, "channel_id": settings.YOUTUBE_CHANNEL_ID,
    }


@ensure_csrf_cookie
def home(request):
    return render(request, "world/index.html", {"data": app_data(), "vapid_public_key": settings.VAPID_PUBLIC_KEY})


def share_history(request, slug):
    e = get_object_or_404(HistoryEntry, slug=slug, status=PUB)
    return render(request, "world/share.html", {
        "title": e.title, "desc": e.text, "target": f"/#h-{e.slug}",
        "image": e.image_horizontal.url if e.image_horizontal else "",
    })


def share_video(request, vid):
    v = get_object_or_404(Video, youtube_id=vid, status=PUB)
    return render(request, "world/share.html", {
        "title": v.title, "desc": v.description, "target": f"/#v-{v.youtube_id}",
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
