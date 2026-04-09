# Generated migration for simplified Medicine model

import core.models
import django.db.models.deletion
import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0035_recalculate_durations"),
    ]

    operations = [
        migrations.CreateModel(
            name="Medicine",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "name",
                    models.CharField(
                        db_index=True,
                        help_text="Name of the medication administered",
                        max_length=255,
                        verbose_name="Medicine Name",
                    ),
                ),
                (
                    "dosage",
                    models.FloatField(
                        blank=True,
                        null=True,
                        help_text="Amount of medication given",
                        verbose_name="Dosage",
                    ),
                ),
                (
                    "dosage_unit",
                    models.CharField(
                        blank=True,
                        default="",
                        choices=[
                            ("mg", "MG"),
                            ("ml", "ML"),
                            ("tablets", "Tablets"),
                            ("drops", "Drops"),
                            ("tsp", "Teaspoons"),
                            ("tbsp", "Tablespoons"),
                        ],
                        max_length=20,
                        verbose_name="Dosage Unit",
                    ),
                ),
                (
                    "time",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.localtime,
                        verbose_name="Time",
                    ),
                ),
                (
                    "next_dose_interval",
                    models.DurationField(
                        blank=True,
                        null=True,
                        help_text="Time until next dose can be given",
                        verbose_name="Next Dose Interval",
                    ),
                ),
                (
                    "notes",
                    models.TextField(blank=True, null=True, verbose_name="Notes"),
                ),
                (
                    "child",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="medicine",
                        to="core.child",
                        verbose_name="Child",
                    ),
                ),
                (
                    "tags",
                    core.models.TaggableManager(
                        blank=True,
                        help_text="A comma-separated list of tags.",
                        through="core.Tagged",
                        to="core.Tag",
                        verbose_name="Tags",
                    ),
                ),
            ],
            options={
                "verbose_name": "Medicine",
                "verbose_name_plural": "Medicines",
                "ordering": ["-time"],
                "default_permissions": ("view", "add", "change", "delete"),
            },
        ),
    ]
