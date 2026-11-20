from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("world", "0005_undated_myths"),
    ]

    operations = [
        migrations.CreateModel(
            name="HistoryIllustration",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                ("image", models.ImageField(upload_to="history/illustrations/")),
                ("caption", models.CharField(blank=True, max_length=240)),
                ("alt_text", models.CharField(blank=True, help_text="Describe the image for screen readers.", max_length=240)),
                ("after_heading", models.CharField(blank=True, help_text="Optional exact section heading, without ##. Leave blank to show after the introduction.", max_length=200)),
                ("order", models.PositiveSmallIntegerField(default=1)),
                ("entry", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="illustrations", to="world.historyentry")),
            ],
            options={
                "verbose_name": "article illustration",
                "verbose_name_plural": "article illustrations",
                "ordering": ["order", "id"],
            },
        ),
    ]
