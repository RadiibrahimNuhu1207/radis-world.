from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("world", "0006_history_illustrations"),
    ]

    operations = [
        migrations.CreateModel(
            name="MusicTrack",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("title", models.CharField(help_text="Name shown on the Music button, e.g. 'Kalimba evening'", max_length=120)),
                ("audio", models.FileField(help_text="MP3 file. Only upload music you own or may use.", upload_to="music/")),
                ("artist", models.CharField(blank=True, max_length=120)),
                ("order", models.PositiveSmallIntegerField(default=1, help_text="Lower numbers play first")),
                ("status", models.CharField(choices=[("draft", "Draft (not visible)"), ("published", "Published")], default="published", max_length=12)),
                ("created", models.DateTimeField(auto_now_add=True)),
            ],
            options={"verbose_name": "music track", "ordering": ["order", "title"]},
        ),
    ]
