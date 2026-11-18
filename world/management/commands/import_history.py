"""Load history entries from a JSON file (e.g. seed/history.json). Existing slugs are updated.

Item: {"slug","year","circa","month","day","topic","region","featured","status",
       "en": {"title","place","text"}, "translations": {"sw": {...}, "fr": {...}},
       "artwork","image_vertical","image_horizontal","video_vertical","video_horizontal"}   (file paths relative to the JSON)
"""
import json
from pathlib import Path

from django.core.files import File
from django.core.management.base import BaseCommand

from world.models import HistoryEntry, HistoryTranslation

FILES = ["artwork", "image_vertical", "image_horizontal", "video_vertical", "video_horizontal"]


class Command(BaseCommand):
    help = "Import history entries from a JSON file."

    def add_arguments(self, parser):
        parser.add_argument("json_file")

    def handle(self, json_file, **opts):
        src = Path(json_file)
        created = updated = 0
        for it in json.loads(src.read_text(encoding="utf-8")):
            en = it["en"]
            entry, is_new = HistoryEntry.objects.update_or_create(slug=it["slug"], defaults={
                "year": it["year"], "circa": it.get("circa", False), "undated": it.get("undated", False), "month": it.get("month"), "day": it.get("day"),
                "topic": it["topic"], "region": it["region"], "featured": it.get("featured", False),
                "status": it.get("status", "published"),
                "title": en["title"], "place": en.get("place", ""), "text": en["text"],
            })
            for f in FILES:
                rel = it.get(f)
                if rel and (src.parent / rel).exists() and not getattr(entry, f):
                    with open(src.parent / rel, "rb") as fh:
                        getattr(entry, f).save(Path(rel).name, File(fh), save=False)
            entry.save()
            for lang, tr in (it.get("translations") or {}).items():
                HistoryTranslation.objects.update_or_create(entry=entry, lang=lang, defaults={
                    "title": tr["title"], "place": tr.get("place", ""), "text": tr["text"]})
            created += is_new
            updated += not is_new
        self.stdout.write(self.style.SUCCESS(f"History: {created} new, {updated} updated."))
