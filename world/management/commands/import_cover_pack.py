"""Safely import a RADI's World cover-art ZIP.

Extracts every JPG into MEDIA_ROOT/cover-art-library/. It attaches mapped
covers only when the matching HistoryEntry currently has no artwork.
Existing artwork is never overwritten.
"""
from pathlib import Path, PurePosixPath
from zipfile import ZipFile, BadZipFile

from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.core.files.storage import default_storage
from world.models import HistoryEntry

COVER_MAP = {
    "02_swahili-coast.jpg": "swahili-coast-indian-ocean-world",
    "03_kenya-emergency.jpg": "kenya-emergency-mau-mau-1952",
    "04_great-zimbabwe.jpg": "great-zimbabwe",
    "05_benin-kingdom.jpg": "benin-kingdom",
    "06_mansa-musa.jpg": "mansa-musa",
    "07_great-pyramid.jpg": "great-pyramid",
    "08_roman-empire.jpg": "fall-of-rome",
    "10_samurai.jpg": "tokugawa-shogunate",
    "11_aztec-empire.jpg": "fall-of-tenochtitlan",
    "13_kilwa-kisiwani_clean-artwork.jpg": "kilwa-kisiwani-swahili-city",
}

class Command(BaseCommand):
    help = "Safely import RADI's World cover artwork from a ZIP file."

    def add_arguments(self, parser):
        parser.add_argument("zip_file", help="Path to RADIS_World_Cover_Art_Pack_01.zip")

    def handle(self, zip_file, **options):
        archive = Path(zip_file)
        if not archive.is_file():
            raise CommandError(f"ZIP file not found: {archive}")
        try:
            zf = ZipFile(archive)
        except BadZipFile as exc:
            raise CommandError("The supplied file is not a valid ZIP archive.") from exc

        stored = attached = skipped = 0
        missing = []
        with zf:
            for info in zf.infolist():
                if info.is_dir() or not info.filename.lower().endswith(".jpg"):
                    continue
                # Use only the basename; never extract arbitrary archive paths.
                name = PurePosixPath(info.filename).name
                if not name or name.startswith("."):
                    continue
                data = zf.read(info)
                library_path = f"cover-art-library/{name}"
                if not default_storage.exists(library_path):
                    default_storage.save(library_path, File(__import__("io").BytesIO(data)))
                stored += 1

                slug = COVER_MAP.get(name)
                if not slug:
                    continue
                try:
                    entry = HistoryEntry.objects.get(slug=slug)
                except HistoryEntry.DoesNotExist:
                    missing.append(f"{name} -> {slug} (entry not found)")
                    continue
                if entry.artwork:
                    skipped += 1
                    self.stdout.write(f"KEPT existing artwork: {entry.slug}")
                    continue
                entry.artwork.save(name, File(__import__("io").BytesIO(data)), save=True)
                attached += 1
                self.stdout.write(self.style.SUCCESS(f"ATTACHED: {entry.title}"))

        self.stdout.write(self.style.SUCCESS(
            f"Cover pack processed: {stored} images archived, "
            f"{attached} attached, {skipped} existing covers preserved."
        ))
        for item in missing:
            self.stdout.write(self.style.WARNING(item))
