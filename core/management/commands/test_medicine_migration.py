import tempfile
import shutil
import os
from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.conf import settings
from django.db import connection
from django.test.utils import override_settings


class Command(BaseCommand):
    help = "Test medicine migrations on a copy of the database"

    def add_arguments(self, parser):
        parser.add_argument(
            "--database-path",
            type=str,
            help="Path to database file to test migrations on (for SQLite)",
        )
        parser.add_argument(
            "--dry-run",
            action="store_true",
            help="Only show what would be done, do not actually test",
        )

    def handle(self, *args, **options):
        if options["dry_run"]:
            self.stdout.write("DRY RUN: Medicine migration test plan")
            self._show_migration_plan()
            return

        # Test migrations on a temporary database copy
        self.stdout.write("Testing medicine migrations...")

        if settings.DATABASES["default"]["ENGINE"] == "django.db.backends.sqlite3":
            self._test_sqlite_migrations(options.get("database_path"))
        else:
            self.stdout.write(
                self.style.WARNING(
                    "Migration testing is currently only supported for SQLite databases"
                )
            )
            self._show_migration_plan()

    def _show_migration_plan(self):
        """Show the migration plan without executing."""
        self.stdout.write("\nMedicine feature migration plan:")

        migrations = [
            (
                "core",
                "0036_medicine",
                "Create Medicine model with fields and validation",
            ),
            (
                "core",
                "0037_alter_medicine_tags",
                "Add TaggableManager for medicine tags",
            ),
            (
                "core",
                "0038_add_medicine_performance_indexes",
                "Add database indexes for performance",
            ),
            (
                "babybuddy",
                "0036_add_medicine_card_hide_threshold",
                "Add user setting for card visibility",
            ),
        ]

        for app, migration, description in migrations:
            self.stdout.write(f"  • {app}.{migration}: {description}")

        self.stdout.write("\nTo test these migrations:")
        self.stdout.write("1. Create a backup of your database")
        self.stdout.write("2. Run: python manage.py migrate --plan")
        self.stdout.write("3. Run: python manage.py migrate")
        self.stdout.write("4. Verify with: python manage.py showmigrations")

    def _test_sqlite_migrations(self, db_path):
        """Test migrations on a SQLite database copy."""

        # Determine source database path
        if db_path:
            source_db = db_path
        else:
            source_db = settings.DATABASES["default"]["NAME"]

        if not os.path.exists(source_db):
            self.stdout.write(self.style.ERROR(f"Database file not found: {source_db}"))
            return

        # Create temporary database copy
        with tempfile.NamedTemporaryFile(suffix=".sqlite3", delete=False) as temp_db:
            temp_db_path = temp_db.name

        try:
            # Copy database
            shutil.copy2(source_db, temp_db_path)
            self.stdout.write(f"Created test database copy: {temp_db_path}")

            # Test migrations on the copy
            with override_settings(
                DATABASES={
                    "default": {
                        "ENGINE": "django.db.backends.sqlite3",
                        "NAME": temp_db_path,
                    }
                }
            ):
                self._run_migration_tests()

        finally:
            # Clean up temporary database
            if os.path.exists(temp_db_path):
                os.unlink(temp_db_path)
                self.stdout.write("Cleaned up test database")

    def _run_migration_tests(self):
        """Run the actual migration tests."""

        try:
            # Show current migration state
            self.stdout.write("\n1. Checking current migration state...")
            call_command("showmigrations", verbosity=0)

            # Run migration plan first
            self.stdout.write("\n2. Running migration plan...")
            call_command("migrate", plan=True, verbosity=1)

            # Apply migrations
            self.stdout.write("\n3. Applying medicine migrations...")
            call_command("migrate", verbosity=1)

            # Verify migrations were applied
            self.stdout.write("\n4. Verifying migration state...")
            call_command("showmigrations", "core", verbosity=0)
            call_command("showmigrations", "babybuddy", verbosity=0)

            # Test model functionality
            self.stdout.write("\n5. Testing Medicine model functionality...")
            self._test_medicine_model()

            self.stdout.write(
                self.style.SUCCESS("\n✓ All migration tests passed successfully!")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"\n✗ Migration test failed: {str(e)}"))
            raise

    def _test_medicine_model(self):
        """Test basic Medicine model functionality."""
        from core.models import Child, Medicine
        from datetime import timedelta
        from django.utils import timezone

        # Create a test child if none exists
        child, created = Child.objects.get_or_create(
            first_name="Test",
            last_name="Migration",
            defaults={"birth_date": timezone.localdate()},
        )

        if created:
            self.stdout.write("   Created test child")

        # Test medicine creation
        medicine = Medicine.objects.create(
            child=child,
            medicine_name="Test Medicine",
            dosage=5.0,
            dosage_unit="ml",
            time=timezone.now(),
            next_dose_interval=timedelta(hours=4),
            notes="Migration test",
        )

        self.stdout.write(f"   Created medicine: {medicine}")

        # Test calculated fields
        self.stdout.write(f"   Next dose time: {medicine.next_dose_time}")
        self.stdout.write(f"   Next dose ready: {medicine.next_dose_ready}")

        # Test validation
        try:
            medicine.full_clean()
            self.stdout.write("   Model validation passed")
        except Exception as e:
            raise Exception(f"Model validation failed: {e}")

        # Test tags
        medicine.tags.add("test", "migration")
        self.stdout.write(f"   Added tags: {list(medicine.tags.names())}")

        # Test model methods
        str_repr = str(medicine)
        self.stdout.write(f"   String representation: {str_repr}")

        # Clean up test data
        medicine.delete()
        if created:
            child.delete()

        self.stdout.write("   Cleaned up test data")

        # Test database indexes (check if they exist)
        with connection.cursor() as cursor:
            # Get table info for SQLite
            cursor.execute("PRAGMA index_list(core_medicine)")
            indexes = cursor.fetchall()

            index_names = [idx[1] for idx in indexes]
            expected_indexes = [
                "medicine_child_time_idx",
                "medicine_next_dose_time_idx",
                "medicine_duplicate_check_idx",
            ]

            found_indexes = [idx for idx in expected_indexes if idx in index_names]
            self.stdout.write(f"   Performance indexes found: {found_indexes}")

            if len(found_indexes) != len(expected_indexes):
                missing = set(expected_indexes) - set(found_indexes)
                self.stdout.write(self.style.WARNING(f"   Missing indexes: {missing}"))
