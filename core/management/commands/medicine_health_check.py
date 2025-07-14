#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import time
from datetime import timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import connection, transaction
from django.contrib.auth.models import User
from core.models import Child, Medicine
from babybuddy.models import Settings


class Command(BaseCommand):
    """
    Medicine Feature Health Check Command

    This command performs comprehensive health checks for the medicine feature
    and can be used for monitoring and alerting systems.
    """

    help = "Perform health checks for the medicine feature"

    def add_arguments(self, parser):
        parser.add_argument(
            "--format",
            choices=["text", "json"],
            default="text",
            help="Output format (default: text)",
        )
        parser.add_argument(
            "--timeout",
            type=int,
            default=30,
            help="Timeout in seconds for health checks (default: 30)",
        )
        parser.add_argument(
            "--verbose", action="store_true", help="Enable verbose output"
        )

    def handle(self, *args, **options):
        self.format = options["format"]
        self.timeout = options["timeout"]
        self.verbose = options["verbose"]

        start_time = time.time()
        health_status = {
            "timestamp": timezone.now().isoformat(),
            "status": "healthy",
            "checks": [],
            "metrics": {},
            "errors": [],
        }

        try:
            # Run all health checks
            self._check_database_connectivity(health_status)
            self._check_medicine_model(health_status)
            self._check_medicine_api(health_status)
            self._check_user_settings(health_status)
            self._check_dashboard_cards(health_status)
            self._check_performance_metrics(health_status)

            # Calculate overall execution time
            execution_time = time.time() - start_time
            health_status["metrics"]["execution_time_seconds"] = round(
                execution_time, 3
            )

            # Determine overall status
            failed_checks = [
                check for check in health_status["checks"] if not check["passed"]
            ]
            if failed_checks:
                health_status["status"] = "unhealthy"
                health_status["failed_checks"] = len(failed_checks)

        except Exception as e:
            health_status["status"] = "error"
            health_status["errors"].append(str(e))

        # Output results
        if self.format == "json":
            self.stdout.write(json.dumps(health_status, indent=2))
        else:
            self._output_text_format(health_status)

        # Exit with appropriate code
        if health_status["status"] != "healthy":
            exit(1)

    def _check_database_connectivity(self, health_status):
        """Check basic database connectivity and medicine table existence"""
        check = {
            "name": "database_connectivity",
            "description": "Database connectivity and medicine table existence",
            "passed": False,
            "details": {},
        }

        try:
            # Test database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                check["details"]["connection"] = "ok"

                # Check if medicine table exists
                cursor.execute(
                    """
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name='core_medicine'
                """
                )
                result = cursor.fetchone()

                if result:
                    check["details"]["medicine_table"] = "exists"

                    # Check table structure
                    cursor.execute("PRAGMA table_info(core_medicine)")
                    columns = cursor.fetchall()
                    column_names = [col[1] for col in columns]

                    required_columns = [
                        "id",
                        "child_id",
                        "medicine_name",
                        "dosage",
                        "dosage_unit",
                        "time",
                        "next_dose_interval",
                        "next_dose_time",
                        "notes",
                    ]

                    missing_columns = [
                        col for col in required_columns if col not in column_names
                    ]
                    if missing_columns:
                        check["details"]["missing_columns"] = missing_columns
                    else:
                        check["details"]["table_structure"] = "valid"
                        check["passed"] = True
                else:
                    check["details"]["medicine_table"] = "missing"

        except Exception as e:
            check["details"]["error"] = str(e)

        health_status["checks"].append(check)

    def _check_medicine_model(self, health_status):
        """Check medicine model functionality"""
        check = {
            "name": "medicine_model",
            "description": "Medicine model CRUD operations and validation",
            "passed": False,
            "details": {},
        }

        try:
            # Test model import
            from core.models import Medicine

            check["details"]["model_import"] = "ok"

            # Get medicine count
            medicine_count = Medicine.objects.count()
            check["details"]["total_medicines"] = medicine_count

            # Test model creation (dry run)
            child = Child.objects.first()
            if child:
                test_medicine = Medicine(
                    child=child,
                    medicine_name="Health Check Test",
                    dosage=1.0,
                    dosage_unit="mg",
                    time=timezone.now(),
                    notes="Health check test entry",
                )

                # Test validation
                test_medicine.full_clean()
                check["details"]["validation"] = "ok"

                # Test calculated properties
                if hasattr(test_medicine, "next_dose_ready"):
                    check["details"]["calculated_properties"] = "ok"

                check["passed"] = True
            else:
                check["details"]["no_children"] = "Cannot test without child records"

        except Exception as e:
            check["details"]["error"] = str(e)

        health_status["checks"].append(check)

    def _check_medicine_api(self, health_status):
        """Check medicine API endpoints"""
        check = {
            "name": "medicine_api",
            "description": "Medicine API endpoint availability",
            "passed": False,
            "details": {},
        }

        try:
            from django.urls import reverse
            from django.test import Client

            # Test URL reverse
            api_url = reverse("api:medicine-list")
            check["details"]["api_url"] = api_url

            # Test endpoint accessibility (without auth)
            client = Client()
            response = client.get(api_url)

            # Should get 401 (unauthorized) which means endpoint exists
            if response.status_code == 401:
                check["details"]["endpoint_status"] = "accessible"
                check["passed"] = True
            elif response.status_code == 404:
                check["details"]["endpoint_status"] = "not_found"
            else:
                check["details"]["endpoint_status"] = f"status_{response.status_code}"

        except Exception as e:
            check["details"]["error"] = str(e)

        health_status["checks"].append(check)

    def _check_user_settings(self, health_status):
        """Check medicine user settings functionality"""
        check = {
            "name": "user_settings",
            "description": "Medicine user settings configuration",
            "passed": False,
            "details": {},
        }

        try:
            # Check if settings model has medicine fields
            settings_fields = [f.name for f in Settings._meta.fields]
            if "medicine_card_hide_threshold" in settings_fields:
                check["details"]["settings_field"] = "exists"

                # Count users with medicine settings
                users_with_settings = Settings.objects.exclude(
                    medicine_card_hide_threshold__isnull=True
                ).count()
                check["details"]["users_with_settings"] = users_with_settings

                check["passed"] = True
            else:
                check["details"]["settings_field"] = "missing"

        except Exception as e:
            check["details"]["error"] = str(e)

        health_status["checks"].append(check)

    def _check_dashboard_cards(self, health_status):
        """Check dashboard card template tags"""
        check = {
            "name": "dashboard_cards",
            "description": "Medicine dashboard card functionality",
            "passed": False,
            "details": {},
        }

        try:
            from dashboard.templatetags.cards import (
                card_medicine_last,
                card_medicine_due,
            )

            check["details"]["template_tags"] = "imported"

            # Test with a child if available
            child = Child.objects.first()
            if child:
                from django.template import Context

                context = Context({"child": child})

                # Test medicine last card
                try:
                    result = card_medicine_last(context, child)
                    check["details"]["medicine_last_card"] = "ok"
                except Exception as e:
                    check["details"]["medicine_last_card"] = f"error: {e}"

                # Test medicine due card
                try:
                    result = card_medicine_due(context, child)
                    check["details"]["medicine_due_card"] = "ok"
                    check["passed"] = True
                except Exception as e:
                    check["details"]["medicine_due_card"] = f"error: {e}"
            else:
                check["details"]["no_children"] = "Cannot test without child records"
                check["passed"] = True  # Consider this ok if no children exist

        except Exception as e:
            check["details"]["error"] = str(e)

        health_status["checks"].append(check)

    def _check_performance_metrics(self, health_status):
        """Check performance-related metrics"""
        check = {
            "name": "performance_metrics",
            "description": "Medicine feature performance indicators",
            "passed": False,
            "details": {},
        }

        try:
            # Database query performance
            start_time = time.time()

            # Test medicine query performance
            with connection.cursor() as cursor:
                # Check if performance indexes exist
                cursor.execute("PRAGMA index_list(core_medicine)")
                indexes = cursor.fetchall()
                index_names = [idx[1] for idx in indexes]

                expected_indexes = [
                    "medicine_child_time_idx",
                    "medicine_next_dose_time_idx",
                    "medicine_duplicate_check_idx",
                ]

                existing_indexes = [
                    idx for idx in expected_indexes if idx in index_names
                ]
                check["details"]["performance_indexes"] = {
                    "expected": len(expected_indexes),
                    "found": len(existing_indexes),
                    "missing": list(set(expected_indexes) - set(existing_indexes)),
                }

            # Measure query time for recent medicines
            query_start = time.time()
            recent_medicines = Medicine.objects.select_related("child").order_by(
                "-time"
            )[:10]
            list(recent_medicines)  # Force query execution
            query_time = time.time() - query_start

            check["details"]["recent_medicines_query_time"] = round(
                query_time * 1000, 2
            )  # ms

            # Count medicines by status
            total_medicines = Medicine.objects.count()
            check["details"]["total_medicines"] = total_medicines

            if total_medicines > 0:
                # Count medicines with next dose times
                with_next_dose = Medicine.objects.exclude(
                    next_dose_time__isnull=True
                ).count()
                check["details"]["medicines_with_next_dose"] = with_next_dose

                # Recent activity (last 7 days)
                week_ago = timezone.now() - timedelta(days=7)
                recent_activity = Medicine.objects.filter(time__gte=week_ago).count()
                check["details"]["recent_activity_7_days"] = recent_activity

            # Consider performance acceptable if query time < 100ms
            if query_time < 0.1:  # 100ms
                check["passed"] = True
            else:
                check["details"][
                    "performance_warning"
                ] = "Query time exceeds 100ms threshold"

        except Exception as e:
            check["details"]["error"] = str(e)

        health_status["checks"].append(check)

        # Add overall metrics
        health_status["metrics"].update(
            {
                "total_checks": len(health_status["checks"]),
                "passed_checks": len(
                    [c for c in health_status["checks"] if c["passed"]]
                ),
            }
        )

    def _output_text_format(self, health_status):
        """Output health status in human-readable text format"""
        status_icon = "✅" if health_status["status"] == "healthy" else "❌"

        self.stdout.write(f"\n{status_icon} Medicine Feature Health Check")
        self.stdout.write(f"Status: {health_status['status'].upper()}")
        self.stdout.write(f"Timestamp: {health_status['timestamp']}")
        self.stdout.write(
            f"Execution Time: {health_status['metrics'].get('execution_time_seconds', 0)}s"
        )

        if health_status.get("errors"):
            self.stdout.write(f"\n❌ ERRORS:")
            for error in health_status["errors"]:
                self.stdout.write(f"   {error}")

        self.stdout.write(f"\n📊 CHECK RESULTS:")
        for check in health_status["checks"]:
            icon = "✅" if check["passed"] else "❌"
            self.stdout.write(f"{icon} {check['name']}: {check['description']}")

            if self.verbose or not check["passed"]:
                for key, value in check["details"].items():
                    self.stdout.write(f"   {key}: {value}")

        # Summary metrics
        total = health_status["metrics"]["total_checks"]
        passed = health_status["metrics"]["passed_checks"]
        self.stdout.write(f"\n📈 SUMMARY: {passed}/{total} checks passed")

        if health_status["status"] != "healthy":
            self.stdout.write(
                f"\n⚠️  RECOMMENDATION: Review failed checks and address issues"
            )
