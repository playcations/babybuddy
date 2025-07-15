"""
Django management command to wait for database to be available.
"""

import time
from django.core.management.base import BaseCommand
from django.db import connections
from django.db.utils import OperationalError


class Command(BaseCommand):
    help = "Wait for database to be available"

    def add_arguments(self, parser):
        parser.add_argument(
            "--timeout", type=int, default=30, help="Timeout in seconds (default: 30)"
        )

    def handle(self, *args, **options):
        timeout = options["timeout"]
        start_time = time.time()

        self.stdout.write("Waiting for database...")

        while True:
            try:
                # Try to get a database connection
                db_conn = connections["default"]
                db_conn.cursor()
                break
            except OperationalError:
                if time.time() - start_time >= timeout:
                    self.stdout.write(
                        self.style.ERROR(
                            f"Database unavailable after {timeout} seconds"
                        )
                    )
                    return

                self.stdout.write("Database unavailable, waiting 1 second...")
                time.sleep(1)

        self.stdout.write(self.style.SUCCESS("Database available!"))
