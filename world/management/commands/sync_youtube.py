"""Pull your YouTube videos into Radi Stories.

Two ways, chosen automatically:
  * YOUTUBE_API_KEY set in .env  -> uses Google's YouTube Data API (works on PythonAnywhere's free plan,
    imports ALL your uploads). Get a free key: console.cloud.google.com -> APIs -> "YouTube Data API v3" -> Credentials.
  * no key -> the public RSS feed (newest ~15). Blocked on PythonAnywhere's free plan.

Run daily:  python manage.py sync_youtube
"""
import json
import re
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

from world.models import Video


def api_items(cid, key):
    playlist, token = "UU" + cid[2:], ""
    while True:
        url = ("https://www.googleapis.com/youtube/v3/playlistItems?part=snippet&maxResults=50"
               f"&playlistId={playlist}&key={key}" + (f"&pageToken={token}" if token else ""))
        data = json.loads(fetch(url))
        for it in data.get("items", []):
            sn = it["snippet"]; vid = sn.get("resourceId", {}).get("videoId")
            if not vid or sn.get("title") in ("Private video", "Deleted video"):
                continue
            pub = sn.get("publishedAt")
            yield {"id": vid, "title": sn.get("title", ""), "desc": sn.get("description", ""), "short": False,
                   "published": datetime.fromisoformat(pub.replace("Z", "+00:00")) if pub else None}
        token = data.get("nextPageToken")
        if not token:
            break

NS = {"a": "http://www.w3.org/2005/Atom", "yt": "http://www.youtube.com/xml/schemas/2015",
      "media": "http://search.yahoo.com/mrss/"}
UA = {"User-Agent": "Mozilla/5.0 (RadisWorld sync)"}


def fetch(url):
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=15) as r:
        return r.read().decode("utf-8", "replace")


def resolve_channel_id(value):
    value = value.strip()
    if re.fullmatch(r"UC[A-Za-z0-9_-]{22}", value):
        return value
    m = re.search(r"(UC[A-Za-z0-9_-]{22})", value)          # a /channel/UC... link
    if m:
        return m.group(1)
    handle = value.split("youtube.com/")[-1].strip("/")
    if not handle.startswith("@"):
        handle = "@" + handle
    html = fetch(f"https://www.youtube.com/{handle}")
    for pat in (r'"channelId":"(UC[A-Za-z0-9_-]{22})"', r'channel/(UC[A-Za-z0-9_-]{22})', r'"externalId":"(UC[A-Za-z0-9_-]{22})"'):
        m = re.search(pat, html)
        if m:
            return m.group(1)
    raise CommandError(f"Couldn't find the channel id for {value}. Put the UC... id in YOUTUBE_CHANNEL instead.")


def parse_feed(xml_text):
    root = ET.fromstring(xml_text)
    for e in root.findall("a:entry", NS):
        vid = e.findtext("yt:videoId", namespaces=NS)
        title = e.findtext("a:title", namespaces=NS) or ""
        published = e.findtext("a:published", namespaces=NS)
        group = e.find("media:group", NS)
        desc = group.findtext("media:description", namespaces=NS) if group is not None else ""
        link = (e.find("a:link", NS).get("href") if e.find("a:link", NS) is not None else "") or ""
        yield {"id": vid, "title": title, "desc": desc or "", "short": "/shorts/" in link,
               "published": datetime.fromisoformat(published.replace("Z", "+00:00")) if published else None}


class Command(BaseCommand):
    help = "Import the newest videos from the YouTube channel set in YOUTUBE_CHANNEL."

    def add_arguments(self, parser):
        parser.add_argument("--channel", help="Override YOUTUBE_CHANNEL (id, handle or link)")

    def handle(self, *args, **opts):
        channel = opts.get("channel") or settings.YOUTUBE_CHANNEL_ID or settings.YOUTUBE_CHANNEL
        if not channel:
            raise CommandError("Set YOUTUBE_CHANNEL_ID in .env (your channel id UC...).")
        key = getattr(settings, "YOUTUBE_API_KEY", "")
        try:
            cid = resolve_channel_id(channel)
            items = list(api_items(cid, key)) if key else list(parse_feed(fetch(f"https://www.youtube.com/feeds/videos.xml?channel_id={cid}")))
        except Exception as exc:
            raise CommandError(f"Couldn't reach YouTube ({exc}). On PythonAnywhere's free plan add YOUTUBE_API_KEY to .env "
                               "(see the README), or paste video links in Admin -> Videos. The Stories page still shows "
                               "your channel's player either way.")
        added = updated = 0
        for item in items:
            v, created = Video.objects.get_or_create(youtube_id=item["id"], defaults={
                "title": item["title"], "description": item["desc"], "published": item["published"],
                "kind": Video.Kind.SHORT if item["short"] else Video.Kind.STORY,
            })
            if created:
                added += 1
            elif not v.title:
                v.title, v.description = item["title"], item["desc"]
                v.save(update_fields=["title", "description"])
                updated += 1
        self.stdout.write(self.style.SUCCESS(f"Channel {cid}: {added} new videos, {updated} updated."))
