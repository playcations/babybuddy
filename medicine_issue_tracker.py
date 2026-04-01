#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Medicine Feature Issue Tracker and Bug Monitor

This script monitors for common issues and potential bugs in the medicine feature
and can be integrated with issue tracking systems.

Usage:
    python medicine_issue_tracker.py [options]

Examples:
    python medicine_issue_tracker.py --check-all
    python medicine_issue_tracker.py --output issues.json
    python medicine_issue_tracker.py --alert-webhook https://hooks.slack.com/...
"""

import json
import sys
import argparse
import logging
import requests
from datetime import datetime, timedelta
from pathlib import Path

# Add the project directory to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Django setup
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "babybuddy.settings.production")
django.setup()

from django.db import connection
from django.utils import timezone
from django.core.exceptions import ValidationError
from core.models import Medicine, Child
from babybuddy.models import Settings
from django.contrib.auth.models import User


class MedicineIssueTracker:
    """Track and monitor issues in the medicine feature"""

    def __init__(self, alert_webhook=None, output_file=None):
        self.alert_webhook = alert_webhook
        self.output_file = output_file

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        self.issues = []

    def check_data_integrity(self):
        """Check for data integrity issues"""
        self.logger.info("Checking medicine data integrity...")

        # Check for invalid dosages
        invalid_dosages = Medicine.objects.filter(dosage__lte=0).count()
        if invalid_dosages > 0:
            self.add_issue(
                "data_integrity",
                "invalid_dosages",
                f"{invalid_dosages} medicine entries with invalid dosages (<=0)",
                "medium",
                {"count": invalid_dosages},
            )

        # Check for missing medicine names
        missing_names = Medicine.objects.filter(medicine_name__in=["", None]).count()
        if missing_names > 0:
            self.add_issue(
                "data_integrity",
                "missing_medicine_names",
                f"{missing_names} medicine entries without names",
                "high",
                {"count": missing_names},
            )

        # Check for future medicine times
        future_medicines = Medicine.objects.filter(time__gt=timezone.now()).count()
        if future_medicines > 0:
            self.add_issue(
                "data_integrity",
                "future_medicine_times",
                f"{future_medicines} medicine entries with future timestamps",
                "low",
                {"count": future_medicines},
            )

        # Check for orphaned medicines (children without valid references)
        try:
            orphaned_medicines = Medicine.objects.filter(child__isnull=True).count()
            if orphaned_medicines > 0:
                self.add_issue(
                    "data_integrity",
                    "orphaned_medicines",
                    f"{orphaned_medicines} medicine entries without valid child references",
                    "high",
                    {"count": orphaned_medicines},
                )
        except Exception as e:
            self.add_issue(
                "system_error",
                "orphaned_check_failed",
                f"Failed to check for orphaned medicines: {e}",
                "medium",
                {"error": str(e)},
            )

    def check_validation_issues(self):
        """Check for validation and constraint violations"""
        self.logger.info("Checking validation issues...")

        # Test a sample of medicine entries for validation errors
        recent_medicines = Medicine.objects.order_by("-time")[:100]
        validation_errors = 0

        for medicine in recent_medicines:
            try:
                medicine.full_clean()
            except ValidationError as e:
                validation_errors += 1
                if validation_errors == 1:  # Report first error details
                    self.add_issue(
                        "validation",
                        "model_validation_errors",
                        f"Medicine validation errors detected",
                        "high",
                        {
                            "sample_error": str(e),
                            "medicine_id": medicine.id,
                            "count": validation_errors,
                        },
                    )

        if validation_errors > 1:
            self.update_issue_details(
                "model_validation_errors", {"count": validation_errors}
            )

    def check_performance_issues(self):
        """Check for performance-related issues"""
        self.logger.info("Checking performance issues...")

        # Check for slow queries
        import time

        # Test medicine list query performance
        start_time = time.time()
        list(Medicine.objects.select_related("child").order_by("-time")[:50])
        query_time = time.time() - start_time

        if query_time > 2.0:  # 2 seconds threshold
            self.add_issue(
                "performance",
                "slow_medicine_queries",
                f"Medicine list queries taking {query_time:.2f}s (threshold: 2.0s)",
                "medium",
                {"query_time": query_time, "threshold": 2.0},
            )

        # Check database size and growth
        with connection.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) FROM core_medicine")
            medicine_count = cursor.fetchone()[0]

            # Check for rapid growth (>1000 entries in last day)
            yesterday = timezone.now() - timedelta(days=1)
            recent_count = Medicine.objects.filter(time__gte=yesterday).count()

            if recent_count > 1000:
                self.add_issue(
                    "performance",
                    "rapid_data_growth",
                    f"{recent_count} medicine entries added in last 24 hours",
                    "low",
                    {"recent_count": recent_count, "total_count": medicine_count},
                )

    def check_feature_usage_anomalies(self):
        """Check for unusual usage patterns that might indicate issues"""
        self.logger.info("Checking feature usage anomalies...")

        # Check for excessive duplicate entries
        from django.db.models import Count

        duplicates = (
            Medicine.objects.values("child", "medicine_name", "time__date")
            .annotate(count=Count("id"))
            .filter(count__gt=10)
        )  # More than 10 same medicines per day

        for duplicate in duplicates:
            self.add_issue(
                "usage_anomaly",
                "excessive_duplicates",
                f'Child has {duplicate["count"]} entries for {duplicate["medicine_name"]} on {duplicate["time__date"]}',
                "low",
                {
                    "child_id": duplicate["child"],
                    "medicine_name": duplicate["medicine_name"],
                    "date": str(duplicate["time__date"]),
                    "count": duplicate["count"],
                },
            )

        # Check for medicine entries with very high dosages (potential typos)
        high_dosages = Medicine.objects.filter(dosage__gt=1000)
        for medicine in high_dosages:
            self.add_issue(
                "usage_anomaly",
                "high_dosage_entry",
                f"Medicine with unusually high dosage: {medicine.dosage} {medicine.dosage_unit}",
                "medium",
                {
                    "medicine_id": medicine.id,
                    "medicine_name": medicine.medicine_name,
                    "dosage": medicine.dosage,
                    "dosage_unit": medicine.dosage_unit,
                },
            )

    def check_system_health(self):
        """Check overall system health for medicine feature"""
        self.logger.info("Checking system health...")

        # Check database connectivity
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
        except Exception as e:
            self.add_issue(
                "system_error",
                "database_connectivity",
                f"Database connectivity issue: {e}",
                "critical",
                {"error": str(e)},
            )

        # Check if medicine table exists and has expected structure
        try:
            with connection.cursor() as cursor:
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
                    self.add_issue(
                        "system_error",
                        "missing_table_columns",
                        f"Medicine table missing columns: {missing_columns}",
                        "critical",
                        {"missing_columns": missing_columns},
                    )
        except Exception as e:
            self.add_issue(
                "system_error",
                "table_structure_check_failed",
                f"Failed to check medicine table structure: {e}",
                "high",
                {"error": str(e)},
            )

        # Check for medicine model import issues
        try:
            from core.models import Medicine

            Medicine.objects.count()
        except Exception as e:
            self.add_issue(
                "system_error",
                "model_import_failure",
                f"Failed to import or use Medicine model: {e}",
                "critical",
                {"error": str(e)},
            )

    def check_user_experience_issues(self):
        """Check for issues that affect user experience"""
        self.logger.info("Checking user experience issues...")

        # Check for medicines with long overdue next doses
        week_ago = timezone.now() - timedelta(days=7)
        overdue_medicines = Medicine.objects.filter(
            next_dose_time__lt=week_ago, next_dose_time__isnull=False
        ).count()

        if overdue_medicines > 100:
            self.add_issue(
                "user_experience",
                "many_overdue_medicines",
                f"{overdue_medicines} medicines overdue by more than a week",
                "low",
                {"count": overdue_medicines},
            )

        # Check for potential medicine name typos/inconsistencies
        medicine_names = Medicine.objects.values_list(
            "medicine_name", flat=True
        ).distinct()
        potential_typos = self.find_potential_medicine_name_typos(medicine_names)

        if len(potential_typos) > 10:
            self.add_issue(
                "user_experience",
                "potential_medicine_name_typos",
                f"Found {len(potential_typos)} potential medicine name typos or inconsistencies",
                "low",
                {"count": len(potential_typos), "examples": potential_typos[:5]},
            )

    def find_potential_medicine_name_typos(self, medicine_names):
        """Find potential typos in medicine names"""
        potential_typos = []
        names_list = list(medicine_names)

        for i, name1 in enumerate(names_list):
            for name2 in names_list[i + 1 :]:
                if self.are_similar_names(name1, name2):
                    potential_typos.append([name1, name2])
                    if (
                        len(potential_typos) >= 20
                    ):  # Limit to prevent performance issues
                        return potential_typos

        return potential_typos

    def are_similar_names(self, name1, name2):
        """Check if two medicine names are similar (potential typos)"""
        if not name1 or not name2:
            return False

        # Skip if exactly the same
        if name1.lower() == name2.lower():
            return False

        # Check length difference
        if abs(len(name1) - len(name2)) > 3:
            return False

        # Simple character overlap check
        set1 = set(name1.lower().replace(" ", ""))
        set2 = set(name2.lower().replace(" ", ""))
        overlap = len(set1 & set2)
        min_len = min(len(set1), len(set2))

        # If significant character overlap, consider similar
        return overlap >= min_len * 0.8 and min_len >= 3

    def add_issue(self, category, issue_type, description, severity, details=None):
        """Add an issue to the tracking list"""
        issue = {
            "timestamp": datetime.now().isoformat(),
            "category": category,
            "type": issue_type,
            "description": description,
            "severity": severity,
            "details": details or {},
        }
        self.issues.append(issue)

        # Log based on severity
        if severity == "critical":
            self.logger.critical(f"CRITICAL: {description}")
        elif severity == "high":
            self.logger.error(f"HIGH: {description}")
        elif severity == "medium":
            self.logger.warning(f"MEDIUM: {description}")
        else:
            self.logger.info(f"LOW: {description}")

    def update_issue_details(self, issue_type, new_details):
        """Update details of an existing issue"""
        for issue in self.issues:
            if issue["type"] == issue_type:
                issue["details"].update(new_details)
                break

    def run_all_checks(self):
        """Run all available checks"""
        self.logger.info("Starting comprehensive medicine feature issue check...")

        self.check_system_health()
        self.check_data_integrity()
        self.check_validation_issues()
        self.check_performance_issues()
        self.check_feature_usage_anomalies()
        self.check_user_experience_issues()

        self.logger.info(f"Issue check completed. Found {len(self.issues)} issues.")

        return self.issues

    def generate_report(self):
        """Generate a comprehensive issue report"""
        report = {
            "timestamp": datetime.now().isoformat(),
            "summary": {
                "total_issues": len(self.issues),
                "critical": len(
                    [i for i in self.issues if i["severity"] == "critical"]
                ),
                "high": len([i for i in self.issues if i["severity"] == "high"]),
                "medium": len([i for i in self.issues if i["severity"] == "medium"]),
                "low": len([i for i in self.issues if i["severity"] == "low"]),
            },
            "issues_by_category": {},
            "issues": self.issues,
        }

        # Group issues by category
        for issue in self.issues:
            category = issue["category"]
            if category not in report["issues_by_category"]:
                report["issues_by_category"][category] = []
            report["issues_by_category"][category].append(issue)

        return report

    def send_alerts(self, report):
        """Send alerts for critical and high severity issues"""
        critical_and_high = [
            i for i in self.issues if i["severity"] in ["critical", "high"]
        ]

        if not critical_and_high:
            self.logger.info("No critical or high severity issues found")
            return

        if self.alert_webhook:
            self.send_webhook_alert(critical_and_high)

        # Log all critical and high issues
        self.logger.warning(
            f"Found {len(critical_and_high)} critical/high severity issues"
        )
        for issue in critical_and_high:
            self.logger.error(f"{issue['severity'].upper()}: {issue['description']}")

    def send_webhook_alert(self, issues):
        """Send webhook alert (e.g., to Slack)"""
        try:
            message = {
                "text": f"🚨 Medicine Feature Issues Detected ({len(issues)} critical/high)",
                "attachments": [
                    {
                        "color": (
                            "danger"
                            if any(i["severity"] == "critical" for i in issues)
                            else "warning"
                        ),
                        "fields": [
                            {
                                "title": f"{issue['severity'].upper()}: {issue['type']}",
                                "value": issue["description"],
                                "short": False,
                            }
                            for issue in issues[:5]  # Limit to first 5 issues
                        ],
                    }
                ],
            }

            response = requests.post(self.alert_webhook, json=message, timeout=10)
            response.raise_for_status()
            self.logger.info("Alert sent successfully")

        except Exception as e:
            self.logger.error(f"Failed to send webhook alert: {e}")

    def save_report(self, report):
        """Save report to file"""
        if self.output_file:
            try:
                with open(self.output_file, "w") as f:
                    json.dump(report, f, indent=2)
                self.logger.info(f"Report saved to {self.output_file}")
            except Exception as e:
                self.logger.error(f"Failed to save report: {e}")

    def display_summary(self, report):
        """Display a summary of found issues"""
        summary = report["summary"]

        print("\n" + "=" * 60)
        print("MEDICINE FEATURE ISSUE TRACKER SUMMARY")
        print("=" * 60)
        print(f"Timestamp: {report['timestamp']}")
        print(f"Total Issues Found: {summary['total_issues']}")
        print(f"  Critical: {summary['critical']}")
        print(f"  High: {summary['high']}")
        print(f"  Medium: {summary['medium']}")
        print(f"  Low: {summary['low']}")

        if summary["total_issues"] > 0:
            print("\nISSUES BY CATEGORY:")
            for category, issues in report["issues_by_category"].items():
                print(f"  {category}: {len(issues)} issues")
                for issue in issues:
                    print(f"    - {issue['severity'].upper()}: {issue['description']}")
        else:
            print("\n✅ No issues detected!")

        print("=" * 60)


def main():
    parser = argparse.ArgumentParser(
        description="Track and monitor medicine feature issues"
    )
    parser.add_argument(
        "--check-all", action="store_true", help="Run all available checks"
    )
    parser.add_argument(
        "--output", type=str, help="Output file for issue report (JSON format)"
    )
    parser.add_argument(
        "--alert-webhook",
        type=str,
        help="Webhook URL for sending alerts (e.g., Slack webhook)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    tracker = MedicineIssueTracker(
        alert_webhook=args.alert_webhook, output_file=args.output
    )

    if args.check_all:
        issues = tracker.run_all_checks()
        report = tracker.generate_report()

        tracker.send_alerts(report)
        tracker.save_report(report)
        tracker.display_summary(report)

        # Exit with error code if critical or high severity issues found
        critical_high = report["summary"]["critical"] + report["summary"]["high"]
        sys.exit(1 if critical_high > 0 else 0)
    else:
        print("Use --check-all to run issue checks")
        sys.exit(1)


if __name__ == "__main__":
    main()
