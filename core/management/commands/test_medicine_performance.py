import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from core.models import Child, Medicine


class Command(BaseCommand):
    help = "Test medicine creation and query performance"

    def add_arguments(self, parser):
        parser.add_argument(
            "--count",
            type=int,
            default=1000,
            help="Number of medicine entries to create for testing",
        )

    def handle(self, *args, **options):
        count = options["count"]

        # Get or create a test child
        child, created = Child.objects.get_or_create(
            first_name="Test",
            last_name="Performance",
            defaults={"birth_date": timezone.localdate()},
        )

        if created:
            self.stdout.write(f"Created test child: {child}")
        else:
            self.stdout.write(f"Using existing test child: {child}")

        # Test bulk creation performance
        self.stdout.write(f"\nCreating {count} medicine entries...")
        start_time = time.time()

        medicines = []
        base_time = timezone.now() - timedelta(days=30)

        for i in range(count):
            medicine = Medicine(
                child=child,
                medicine_name=f"Test Medicine {i % 10}",  # Simulate 10 different medicines
                dosage=5.0 + (i % 20),  # Vary dosage
                dosage_unit="ml",
                time=base_time + timedelta(hours=i),
                notes=f"Performance test entry {i}",
            )
            medicines.append(medicine)

        # Bulk create for better performance
        with transaction.atomic():
            Medicine.objects.bulk_create(medicines, batch_size=100)

        creation_time = time.time() - start_time
        self.stdout.write(f"Created {count} entries in {creation_time:.2f} seconds")
        self.stdout.write(f"Rate: {count/creation_time:.2f} entries/second")

        # Test query performance
        self.stdout.write(f"\nTesting query performance...")

        # Test 1: Get last medicine (dashboard card query)
        start_time = time.time()
        last_medicine = Medicine.objects.filter(child=child).order_by("-time").first()
        query1_time = time.time() - start_time
        self.stdout.write(f"Last medicine query: {query1_time*1000:.2f}ms")

        # Test 2: Get due medicines (dashboard card query)
        start_time = time.time()
        due_medicines = Medicine.objects.filter(
            child=child,
            next_dose_time__lte=timezone.now(),
            next_dose_time__isnull=False,
        ).order_by("next_dose_time")[:3]
        query2_time = time.time() - start_time
        self.stdout.write(f"Due medicines query: {query2_time*1000:.2f}ms")

        # Test 3: Medicine list with pagination (view query)
        start_time = time.time()
        medicine_list = Medicine.objects.filter(child=child).order_by("-time")[:25]
        query3_time = time.time() - start_time
        self.stdout.write(f"Medicine list query (25 items): {query3_time*1000:.2f}ms")

        # Test 4: Medicine frequency report query
        start_time = time.time()
        from django.db.models import Count
        from django.db.models.functions import TruncDate

        frequency_data = (
            Medicine.objects.filter(child=child)
            .annotate(date=TruncDate("time"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        list(frequency_data)  # Force evaluation
        query4_time = time.time() - start_time
        self.stdout.write(f"Frequency report query: {query4_time*1000:.2f}ms")

        # Summary
        total_entries = Medicine.objects.filter(child=child).count()
        self.stdout.write(f"\nSummary:")
        self.stdout.write(f"Total medicine entries for {child}: {total_entries}")
        self.stdout.write(
            f"Average query time: {(query1_time + query2_time + query3_time + query4_time)/4*1000:.2f}ms"
        )

        # Cleanup option
        cleanup = input("\nDelete test data? (y/N): ")
        if cleanup.lower() == "y":
            deleted_count, _ = Medicine.objects.filter(child=child).delete()
            self.stdout.write(f"Deleted {deleted_count} test medicine entries")
            if created:
                child.delete()
                self.stdout.write(f"Deleted test child")
