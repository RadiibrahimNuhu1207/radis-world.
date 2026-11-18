"""'Generate cover with AI' for the admin, using OpenAI's image API (the engine behind ChatGPT images).

Needs OPENAI_API_KEY in .env (a paid OpenAI account: platform.openai.com -> API keys).
"""
import base64
import json
import urllib.error
import urllib.request

from django.conf import settings
from django.core.files.base import ContentFile

STYLE = ("Cinematic painted cover artwork for a storytelling app. Rich detail, dramatic light, "
         "deep navy and warm gold colour palette, respectful and historically grounded. "
         "Absolutely no text, letters, words or logos anywhere in the image.")


class AICoverError(Exception):
    pass


def generate_image(subject, size):
    key = getattr(settings, "OPENAI_API_KEY", "")
    if not key:
        raise AICoverError("Add OPENAI_API_KEY to .env first (see README → AI covers).")
    body = json.dumps({"model": settings.OPENAI_IMAGE_MODEL, "prompt": f"{STYLE}\n\nSubject: {subject}",
                       "size": size, "n": 1}).encode()
    req = urllib.request.Request("https://api.openai.com/v1/images/generations", data=body, headers={
        "Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=170) as r:
            data = json.loads(r.read())
    except urllib.error.HTTPError as e:
        try:
            msg = json.loads(e.read()).get("error", {}).get("message", "")
        except Exception:
            msg = ""
        raise AICoverError(f"OpenAI refused the request ({e.code}). {msg}")
    except Exception as e:
        raise AICoverError(f"Couldn't reach OpenAI: {e}")
    item = data["data"][0]
    if item.get("b64_json"):
        return base64.b64decode(item["b64_json"])
    with urllib.request.urlopen(item["url"], timeout=60) as r:
        return r.read()


# model name -> (image field, size, how to describe the item)
TARGETS = {
    "ebook": ("cover", "1024x1536", lambda o: f"Book cover illustration for a book titled '{o.title}'. {o.description[:500]}"),
    "comic": ("cover", "1024x1536", lambda o: f"Comic book cover illustration for '{o.title}'. {o.description[:500]}"),
    "audiobook": ("cover", "1024x1024", lambda o: f"Square audiobook cover illustration for '{o.title}'. {o.description[:500]}"),
    "historyentry": ("artwork", "1536x1024", lambda o: f"Scene from history: {o.title} ({o.place}). {o.text[:700]}"),
}


def make_cover(obj):
    field, size, describe = TARGETS[obj._meta.model_name]
    png = generate_image(describe(obj), size)
    getattr(obj, field).save(f"{obj.slug}-ai.png", ContentFile(png), save=True)
