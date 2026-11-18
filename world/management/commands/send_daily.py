"""Daily push notification: today's moment in history, or else the newest upload from the last day.

PythonAnywhere → Tasks → daily at 04:00 UTC (07:00 Tanzania):
    cd ~/radisworld && ~/.virtualenvs/radi/bin/python manage.py send_daily
"""
import json
from datetime import timedelta

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from world.models import Artwork, Audiobook, Comic, Ebook, HistoryEntry, PushSubscription, Status, Video, date_label

NEW = {"en": "New on Radi's World", "sw": "Mpya kwenye Radi's World", "fr": "Nouveau sur Radi's World",
       "ar": "جديد على Radi's World", "ko": "Radi's World 새 콘텐츠", "ja": "Radi's World の新着",
       "zh": "Radi's World 新内容", "es": "Nuevo en Radi's World"}


class Command(BaseCommand):
    help = "Send today's notification to everyone who subscribed."

    def add_arguments(self, parser):
        parser.add_argument("--dry-run", action="store_true")

    def handle(self, *args, **opts):
        from pywebpush import WebPushException, webpush

        today = timezone.localdate()
        history = list(HistoryEntry.objects.filter(status=Status.PUBLISHED, day=today.day, month=today.month)
                       .order_by("-featured", "year").prefetch_related("translations"))
        since = timezone.now() - timedelta(days=1)
        fresh = (list(Video.objects.filter(status=Status.PUBLISHED, created__gte=since)[:1]) +
                 list(Audiobook.objects.filter(status=Status.PUBLISHED, created__gte=since)[:1]) +
                 list(Ebook.objects.filter(status=Status.PUBLISHED, created__gte=since)[:1]) +
                 list(Comic.objects.filter(status=Status.PUBLISHED, created__gte=since)[:1]) +
                 list(Artwork.objects.filter(status=Status.PUBLISHED, created__gte=since)[:1]))
        if not history and not fresh:
            self.stdout.write("Nothing for today — no notification sent.")
            return
        if not settings.VAPID_PUBLIC_KEY:
            self.stderr.write("VAPID_PUBLIC_KEY missing in .env — run: python manage.py vapid_keys")
            return

        sent = removed = 0
        for sub in PushSubscription.objects.exclude(last_sent=today):
            if history:
                wanted = [t for t in sub.topics.split(",") if t]
                e = next((h for h in history if not wanted or h.topic in wanted), history[0])
                title, _, _ = e.localized(sub.lang)
                payload = {"title": f"Radi's World · {date_label(today.day, today.month, sub.lang)}",
                           "body": f"{e.year} — {title}", "url": f"/#h-{e.slug}"}
            else:
                item = fresh[0]
                prefix = {Video: "v", Audiobook: "a", Comic: "c", Ebook: "b", Artwork: "r"}[type(item)]
                anchor = f"{prefix}-{item.youtube_id if isinstance(item, Video) else item.slug}"
                payload = {"title": NEW.get(sub.lang, NEW["en"]), "body": item.title, "url": f"/#{anchor}"}
            if opts["dry_run"]:
                self.stdout.write(f"[dry-run] {sub.lang}: {payload['title']} — {payload['body']}")
                continue
            try:
                webpush(subscription_info={"endpoint": sub.endpoint, "keys": {"p256dh": sub.p256dh, "auth": sub.auth}},
                        data=json.dumps(payload, ensure_ascii=False),
                        vapid_private_key=settings.VAPID_PRIVATE_KEY_FILE,
                        vapid_claims={"sub": settings.VAPID_CLAIM_EMAIL}, ttl=12 * 3600)
                sub.last_sent, sub.failures = today, 0
                sub.save(update_fields=["last_sent", "failures"])
                sent += 1
            except WebPushException as exc:
                status = getattr(exc.response, "status_code", None)
                if status in (404, 410):
                    sub.delete()
                    removed += 1
                else:
                    sub.failures += 1
                    sub.save(update_fields=["failures"])
                    self.stderr.write(f"Failed ({status}): {exc}")
        self.stdout.write(self.style.SUCCESS(f"{today}: sent {sent}, removed {removed}."))
