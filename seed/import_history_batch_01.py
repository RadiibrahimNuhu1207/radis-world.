"""
Import Batch 01 long-form English story updates into the existing Django database.

Run from the Django project root:
    python manage.py shell < seed/import_history_batch_01.py

Safety:
- Updates existing HistoryEntry records only; it never creates records.
- Matches by exact slug.
- Changes only the English text field and, if present, the deep flag.
- Leaves translations, artwork, media paths, dates and all other fields untouched.
"""

import json
from pathlib import Path
from django.db import transaction
from world.models import HistoryEntry

batch_path = Path("seed/radisworld_history_expansion_batch_01.json")

if not batch_path.exists():
    raise SystemExit(
        f"Cannot find {batch_path}. Run this command from the folder containing manage.py."
    )

with batch_path.open("r", encoding="utf-8") as file:
    records = json.load(file)

if not isinstance(records, list) or not records:
    raise SystemExit("The batch JSON must contain a non-empty list of story records.")

model_fields = {field.name for field in HistoryEntry._meta.get_fields()}
required_fields = {"slug", "text"}
missing = required_fields - model_fields
if missing:
    raise SystemExit(
        "Safety check failed. HistoryEntry is missing expected model fields: "
        + ", ".join(sorted(missing))
    )

prepared = []
for record in records:
    slug = record.get("slug")
    english = record.get("en") or {}
    new_text = english.get("text")

    if not slug or not isinstance(new_text, str) or not new_text.strip():
        raise SystemExit(f"Invalid story record in batch: {slug!r}")

    matches = HistoryEntry.objects.filter(slug=slug)
    count = matches.count()
    if count != 1:
        raise SystemExit(
            f"Safety check failed for slug {slug!r}: expected exactly 1 existing record, found {count}. "
            "Nothing has been changed."
        )

    prepared.append((slug, new_text, bool(record.get("deep", True))))

print(f"Validated {len(prepared)} existing stories. No records will be created.")

with transaction.atomic():
    for slug, new_text, deep_flag in prepared:
        story = HistoryEntry.objects.get(slug=slug)
        story.text = new_text

        fields_to_save = ["text"]
        if "deep" in model_fields:
            story.deep = deep_flag
            fields_to_save.append("deep")

        story.save(update_fields=fields_to_save)
        print(
            f"UPDATED: {slug} | {len(new_text.split())} words | "
            f"{len(new_text):,} characters"
        )

print("Batch 01 import completed successfully.")
print("Translations, artwork, dates, media references and other fields were not modified.")
