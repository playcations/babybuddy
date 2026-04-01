#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Medicine Feature Performance Monitor

This script monitors the performance of the medicine feature and can be used
for continuous monitoring, alerting, and performance tracking.

Usage:
    python monitor_medicine_performance.py [options]

Examples:
    python monitor_medicine_performance.py --interval 60 --output metrics.json
    python monitor_medicine_performance.py --alert-threshold 2.0
"""

import json
import time
import argparse
import logging
import signal
import sys
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
from core.models import Medicine, Child
from dashboard.templatetags.cards import card_medicine_last, card_medicine_due
from django.template import Context


class MedicinePerformanceMonitor:
    """Monitor performance metrics for the medicine feature"""

    def __init__(self, alert_threshold=5.0, output_file=None):
        self.alert_threshold = alert_threshold  # seconds
        self.output_file = output_file
        self.running = True

        # Setup logging
        logging.basicConfig(
            level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

        # Handle graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        self.logger.info("Received shutdown signal, stopping monitor...")
        self.running = False

    def measure_database_performance(self):
        """Measure database query performance for medicine operations"""
        metrics = {}

        # Test basic medicine queries
        start_time = time.time()
        medicine_count = Medicine.objects.count()
        metrics["medicine_count_query_time"] = time.time() - start_time
        metrics["total_medicines"] = medicine_count

        # Test recent medicines query (common dashboard operation)
        start_time = time.time()
        recent_medicines = list(
            Medicine.objects.select_related("child").order_by("-time")[:10]
        )
        metrics["recent_medicines_query_time"] = time.time() - start_time
        metrics["recent_medicines_count"] = len(recent_medicines)

        # Test medicine filtering by child (common operation)
        if medicine_count > 0:
            child = Child.objects.first()
            if child:
                start_time = time.time()
                child_medicines = list(Medicine.objects.filter(child=child))
                metrics["child_medicines_query_time"] = time.time() - start_time
                metrics["child_medicines_count"] = len(child_medicines)

        # Test aggregation queries
        start_time = time.time()
        with connection.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*), AVG(dosage) 
                FROM core_medicine 
                WHERE time >= datetime('now', '-7 days')
            """
            )
            result = cursor.fetchone()
        metrics["aggregation_query_time"] = time.time() - start_time
        metrics["recent_activity_count"] = result[0] if result[0] else 0
        metrics["average_dosage"] = float(result[1]) if result[1] else 0.0

        return metrics

    def measure_dashboard_performance(self):
        """Measure dashboard card rendering performance"""
        metrics = {}

        child = Child.objects.first()
        if not child:
            metrics["no_children"] = True
            return metrics

        context = Context({"child": child})

        # Test medicine last card performance
        start_time = time.time()
        try:
            card_medicine_last(context, child)
            metrics["medicine_last_card_time"] = time.time() - start_time
        except Exception as e:
            metrics["medicine_last_card_error"] = str(e)

        # Test medicine due card performance
        start_time = time.time()
        try:
            card_medicine_due(context, child)
            metrics["medicine_due_card_time"] = time.time() - start_time
        except Exception as e:
            metrics["medicine_due_card_error"] = str(e)

        return metrics

    def measure_api_performance(self):
        """Measure API endpoint performance"""
        metrics = {}

        from django.test import Client
        from django.contrib.auth.models import User
        from rest_framework.authtoken.models import Token

        try:
            # Get a test user and token
            user = User.objects.first()
            if user:
                token, created = Token.objects.get_or_create(user=user)
                client = Client()

                # Test medicine list endpoint
                start_time = time.time()
                response = client.get(
                    "/api/medicine/", HTTP_AUTHORIZATION=f"Token {token.key}"
                )
                metrics["medicine_list_api_time"] = time.time() - start_time
                metrics["medicine_list_api_status"] = response.status_code

                if response.status_code == 200:
                    data = response.json()
                    metrics["medicine_list_api_count"] = data.get("count", 0)
            else:
                metrics["no_users"] = True

        except Exception as e:
            metrics["api_error"] = str(e)

        return metrics

    def check_system_health(self):
        """Check overall system health indicators"""
        metrics = {}

        # Database connection health
        start_time = time.time()
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            metrics["db_connection_time"] = time.time() - start_time
            metrics["db_connection_healthy"] = True
        except Exception as e:
            metrics["db_connection_healthy"] = False
            metrics["db_connection_error"] = str(e)

        # Check for recent medicine activity
        week_ago = timezone.now() - timedelta(days=7)
        recent_count = Medicine.objects.filter(time__gte=week_ago).count()
        metrics["recent_activity_7_days"] = recent_count

        # Check for overdue medicines
        now = timezone.now()
        overdue_count = Medicine.objects.filter(
            next_dose_time__lt=now, next_dose_time__isnull=False
        ).count()
        metrics["overdue_medicines"] = overdue_count

        return metrics

    def collect_metrics(self):
        """Collect all performance metrics"""
        timestamp = datetime.now().isoformat()

        metrics = {
            "timestamp": timestamp,
            "database": self.measure_database_performance(),
            "dashboard": self.measure_dashboard_performance(),
            "api": self.measure_api_performance(),
            "system": self.check_system_health(),
        }

        # Calculate overall performance score
        total_time = 0
        time_count = 0

        for category in ["database", "dashboard", "api"]:
            for key, value in metrics[category].items():
                if key.endswith("_time") and isinstance(value, (int, float)):
                    total_time += value
                    time_count += 1

        metrics["overall"] = {
            "total_response_time": total_time,
            "average_response_time": total_time / time_count if time_count > 0 else 0,
            "performance_score": (
                "good" if total_time < self.alert_threshold else "poor"
            ),
        }

        return metrics

    def check_alerts(self, metrics):
        """Check if any metrics exceed alert thresholds"""
        alerts = []

        # Check database performance
        db_metrics = metrics["database"]
        if db_metrics.get("recent_medicines_query_time", 0) > 1.0:
            alerts.append(
                f"Slow medicine query: {db_metrics['recent_medicines_query_time']:.3f}s"
            )

        # Check overall performance
        overall = metrics["overall"]
        if overall["total_response_time"] > self.alert_threshold:
            alerts.append(
                f"Total response time exceeded threshold: {overall['total_response_time']:.3f}s"
            )

        # Check system health
        system = metrics["system"]
        if not system.get("db_connection_healthy", True):
            alerts.append("Database connection unhealthy")

        if system.get("overdue_medicines", 0) > 10:
            alerts.append(
                f"High number of overdue medicines: {system['overdue_medicines']}"
            )

        return alerts

    def log_metrics(self, metrics, alerts):
        """Log metrics and alerts"""
        overall = metrics["overall"]

        self.logger.info(
            f"Performance: {overall['performance_score']} "
            f"(avg: {overall['average_response_time']:.3f}s, "
            f"total: {overall['total_response_time']:.3f}s)"
        )

        if alerts:
            for alert in alerts:
                self.logger.warning(f"ALERT: {alert}")

        # Save to file if specified
        if self.output_file:
            try:
                with open(self.output_file, "a") as f:
                    f.write(json.dumps(metrics) + "\n")
            except Exception as e:
                self.logger.error(f"Failed to write metrics to file: {e}")

    def run_once(self):
        """Run a single monitoring cycle"""
        self.logger.info("Collecting medicine performance metrics...")

        try:
            metrics = self.collect_metrics()
            alerts = self.check_alerts(metrics)
            self.log_metrics(metrics, alerts)

            return metrics, alerts

        except Exception as e:
            self.logger.error(f"Error collecting metrics: {e}")
            return None, [f"Monitoring error: {e}"]

    def run_continuous(self, interval=60):
        """Run continuous monitoring"""
        self.logger.info(
            f"Starting continuous medicine performance monitoring (interval: {interval}s)"
        )

        while self.running:
            self.run_once()

            # Wait for next interval
            for _ in range(interval):
                if not self.running:
                    break
                time.sleep(1)

        self.logger.info("Medicine performance monitoring stopped")


def main():
    parser = argparse.ArgumentParser(description="Monitor medicine feature performance")
    parser.add_argument(
        "--interval",
        type=int,
        default=300,  # 5 minutes
        help="Monitoring interval in seconds (default: 300)",
    )
    parser.add_argument(
        "--alert-threshold",
        type=float,
        default=5.0,
        help="Alert threshold for total response time in seconds (default: 5.0)",
    )
    parser.add_argument(
        "--output", type=str, help="Output file for metrics (JSON lines format)"
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Run once and exit (default: continuous monitoring)",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable verbose logging")

    args = parser.parse_args()

    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    monitor = MedicinePerformanceMonitor(
        alert_threshold=args.alert_threshold, output_file=args.output
    )

    if args.once:
        metrics, alerts = monitor.run_once()
        if alerts:
            print("ALERTS DETECTED:")
            for alert in alerts:
                print(f"  - {alert}")
        sys.exit(1 if alerts else 0)
    else:
        monitor.run_continuous(args.interval)


if __name__ == "__main__":
    main()
