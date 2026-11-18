"""Create the key pair that lets this server send push notifications (run once per server)."""
import base64

from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec
from django.conf import settings
from django.core.management.base import BaseCommand
from pathlib import Path


class Command(BaseCommand):
    help = "Create the VAPID keys for push notifications (once per server)."

    def handle(self, *args, **opts):
        path = Path(settings.VAPID_PRIVATE_KEY_FILE)
        if path.exists():
            key = serialization.load_pem_private_key(path.read_bytes(), password=None)
            self.stdout.write(f"Key already exists: {path}")
        else:
            key = ec.generate_private_key(ec.SECP256R1())
            path.write_bytes(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8,
                                               serialization.NoEncryption()))
            self.stdout.write(self.style.SUCCESS(f"Private key saved: {path} (do NOT put it on GitHub)"))
        pub = key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)
        b64 = base64.urlsafe_b64encode(pub).decode().rstrip("=")
        self.stdout.write("\nAdd this line to .env:\n")
        self.stdout.write(f"VAPID_PUBLIC_KEY={b64}")
