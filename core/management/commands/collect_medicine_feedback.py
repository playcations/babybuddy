#!/usr/bin/env python
# -*- coding: utf-8 -*-

import json
import csv
from datetime import datetime, timedelta
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth.models import User
from django.db.models import Count, Avg, Q
from core.models import Medicine, Child
from babybuddy.models import Settings


class Command(BaseCommand):
    """
    Medicine Feature User Feedback and Usage Analytics Collection

    This command collects usage patterns and prepares data for user feedback
    analysis to help improve the medicine feature.
    """

    help = "Collect medicine feature usage analytics and feedback data"

    def add_arguments(self, parser):
        parser.add_argument(
            "--days",
            type=int,
            default=30,
            help="Number of days to analyze (default: 30)",
        )
        parser.add_argument("--output", type=str, help="Output file for analytics data")
        parser.add_argument(
            "--format",
            choices=["json", "csv"],
            default="json",
            help="Output format (default: json)",
        )
        parser.add_argument(
            "--include-users",
            action="store_true",
            help="Include anonymized user-specific data",
        )

    def handle(self, *args, **options):
        self.days = options["days"]
        self.output_file = options["output"]
        self.format = options["format"]
        self.include_users = options["include_users"]

        self.stdout.write(
            f"Collecting medicine feature analytics for the last {self.days} days..."
        )

        analytics_data = self.collect_analytics()

        if self.output_file:
            self.save_analytics(analytics_data)
        else:
            self.display_analytics(analytics_data)

    def collect_analytics(self):
        """Collect comprehensive analytics about medicine feature usage"""
        end_date = timezone.now()
        start_date = end_date - timedelta(days=self.days)

        analytics = {
            "collection_date": end_date.isoformat(),
            "analysis_period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": self.days,
            },
            "usage_statistics": self._collect_usage_statistics(start_date, end_date),
            "user_behavior": self._collect_user_behavior(start_date, end_date),
            "feature_adoption": self._collect_feature_adoption(),
            "performance_indicators": self._collect_performance_indicators(
                start_date, end_date
            ),
            "feedback_opportunities": self._identify_feedback_opportunities(),
        }

        if self.include_users:
            analytics["user_segments"] = self._collect_user_segments(
                start_date, end_date
            )

        return analytics

    def _collect_usage_statistics(self, start_date, end_date):
        """Collect basic usage statistics"""
        stats = {}

        # Total medicines recorded
        total_medicines = Medicine.objects.filter(
            time__range=[start_date, end_date]
        ).count()
        stats["total_medicines_recorded"] = total_medicines

        # Daily average
        stats["daily_average"] = round(total_medicines / self.days, 2)

        # Active children (children with medicine records)
        active_children = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .values("child")
            .distinct()
            .count()
        )
        stats["active_children"] = active_children

        # Most common medicines
        common_medicines = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .values("medicine_name")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        stats["most_common_medicines"] = list(common_medicines)

        # Most common dosage units
        common_units = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .values("dosage_unit")
            .annotate(count=Count("id"))
            .order_by("-count")
        )
        stats["dosage_unit_distribution"] = list(common_units)

        # Average dosage by unit
        avg_dosages = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .values("dosage_unit")
            .annotate(avg_dosage=Avg("dosage"), count=Count("id"))
            .order_by("-count")
        )
        stats["average_dosages"] = [
            {
                "dosage_unit": item["dosage_unit"],
                "average_dosage": round(item["avg_dosage"], 2),
                "count": item["count"],
            }
            for item in avg_dosages
        ]

        return stats

    def _collect_user_behavior(self, start_date, end_date):
        """Collect user behavior patterns"""
        behavior = {}

        # Time patterns (simplified)
        medicines_by_time = Medicine.objects.filter(
            time__range=[start_date, end_date]
        ).values_list("time", flat=True)

        # Count by hour
        hour_counts = {}
        for medicine_time in medicines_by_time:
            hour = medicine_time.hour
            hour_counts[hour] = hour_counts.get(hour, 0) + 1

        behavior["hourly_distribution"] = [
            {"hour": str(hour).zfill(2), "count": count}
            for hour, count in sorted(hour_counts.items())
        ]

        # Count by day of week
        day_counts = {}
        for medicine_time in medicines_by_time:
            day = medicine_time.weekday()  # 0=Monday, 6=Sunday
            day_counts[day] = day_counts.get(day, 0) + 1

        behavior["day_of_week_distribution"] = [
            {"day_of_week": str(day), "count": count}
            for day, count in sorted(day_counts.items())
        ]

        # Medicine interval usage
        interval_usage = Medicine.objects.filter(
            time__range=[start_date, end_date], next_dose_interval__isnull=False
        ).count()
        total_medicines = Medicine.objects.filter(
            time__range=[start_date, end_date]
        ).count()

        behavior["interval_usage_rate"] = round(
            (interval_usage / total_medicines * 100) if total_medicines > 0 else 0, 2
        )

        # Notes usage
        notes_usage = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .exclude(Q(notes="") | Q(notes__isnull=True))
            .count()
        )

        behavior["notes_usage_rate"] = round(
            (notes_usage / total_medicines * 100) if total_medicines > 0 else 0, 2
        )

        # Tags usage
        medicines_with_tags = (
            Medicine.objects.filter(
                time__range=[start_date, end_date], tags__isnull=False
            )
            .distinct()
            .count()
        )

        behavior["tags_usage_rate"] = round(
            (medicines_with_tags / total_medicines * 100) if total_medicines > 0 else 0,
            2,
        )

        return behavior

    def _collect_feature_adoption(self):
        """Collect feature adoption metrics"""
        adoption = {}

        # Total children vs children who have medicine records
        total_children = Child.objects.count()
        medicine_children = Medicine.objects.values("child").distinct().count()

        adoption["total_children"] = total_children
        adoption["medicine_children"] = medicine_children
        adoption["adoption_rate"] = round(
            (medicine_children / total_children * 100) if total_children > 0 else 0, 2
        )

        # Dashboard card settings usage
        users_with_settings = Settings.objects.exclude(
            medicine_card_hide_threshold__isnull=True
        ).count()

        adoption["users_with_custom_settings"] = users_with_settings
        adoption["settings_customization_rate"] = round(
            (
                (users_with_settings / User.objects.count() * 100)
                if User.objects.count() > 0
                else 0
            ),
            2,
        )

        # Feature completeness (children using advanced features)
        advanced_feature_children = (
            Medicine.objects.filter(
                Q(next_dose_interval__isnull=False)
                | Q(tags__isnull=False)
                | ~Q(notes="")
            )
            .values("child")
            .distinct()
            .count()
        )

        adoption["advanced_feature_children"] = advanced_feature_children
        adoption["advanced_adoption_rate"] = round(
            (
                (advanced_feature_children / medicine_children * 100)
                if medicine_children > 0
                else 0
            ),
            2,
        )

        return adoption

    def _collect_performance_indicators(self, start_date, end_date):
        """Collect performance and quality indicators"""
        indicators = {}

        # Data quality indicators
        complete_entries = Medicine.objects.filter(
            time__range=[start_date, end_date],
            medicine_name__isnull=False,
            dosage__gt=0,
            dosage_unit__isnull=False,
        ).count()

        total_entries = Medicine.objects.filter(
            time__range=[start_date, end_date]
        ).count()

        indicators["data_completeness_rate"] = round(
            (complete_entries / total_entries * 100) if total_entries > 0 else 0, 2
        )

        # Medicine name consistency (potential typos/variations)
        medicine_names = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .values_list("medicine_name", flat=True)
            .distinct()
        )

        indicators["unique_medicine_names"] = len(medicine_names)
        indicators["potential_duplicates"] = self._find_potential_duplicates(
            medicine_names
        )

        # Next dose accuracy (scheduled vs actual)
        overdue_medicines = Medicine.objects.filter(
            next_dose_time__lt=timezone.now(),
            next_dose_time__isnull=False,
            time__range=[start_date, end_date],
        ).count()

        scheduled_medicines = Medicine.objects.filter(
            next_dose_time__isnull=False, time__range=[start_date, end_date]
        ).count()

        indicators["overdue_rate"] = round(
            (
                (overdue_medicines / scheduled_medicines * 100)
                if scheduled_medicines > 0
                else 0
            ),
            2,
        )

        return indicators

    def _find_potential_duplicates(self, medicine_names):
        """Find potential duplicate medicine names (simple similarity check)"""
        duplicates = []
        names_list = list(medicine_names)

        for i, name1 in enumerate(names_list):
            for name2 in names_list[i + 1 :]:
                # Simple similarity check (case-insensitive, stripped)
                if name1.lower().strip() != name2.lower().strip():
                    # Check for potential typos (simple character difference)
                    if abs(len(name1) - len(name2)) <= 2:
                        # Very basic similarity check
                        common_chars = set(name1.lower()) & set(name2.lower())
                        if len(common_chars) >= min(len(name1), len(name2)) * 0.7:
                            duplicates.append([name1, name2])

        return duplicates[:10]  # Limit to first 10 potential duplicates

    def _identify_feedback_opportunities(self):
        """Identify opportunities for user feedback collection"""
        opportunities = []

        # Children with high medicine usage (good candidates for feature feedback)
        high_usage_children = (
            Medicine.objects.values("child")
            .annotate(medicine_count=Count("id"))
            .filter(medicine_count__gte=10)
            .count()
        )

        if high_usage_children > 0:
            opportunities.append(
                {
                    "type": "feature_feedback",
                    "description": f"{high_usage_children} children with high medicine usage - good candidates for feature feedback",
                    "priority": "high",
                }
            )

        # Users who stopped using the feature
        last_30_days = timezone.now() - timedelta(days=30)
        last_60_days = timezone.now() - timedelta(days=60)

        inactive_children = (
            Medicine.objects.filter(time__range=[last_60_days, last_30_days])
            .values("child")
            .exclude(
                child__in=Medicine.objects.filter(time__gte=last_30_days).values(
                    "child"
                )
            )
            .distinct()
            .count()
        )

        if inactive_children > 0:
            opportunities.append(
                {
                    "type": "churn_feedback",
                    "description": f"{inactive_children} children who stopped using medicine feature - candidates for churn feedback",
                    "priority": "medium",
                }
            )

        # Children with incomplete data (might need help/training)
        incomplete_data_children = (
            Medicine.objects.filter(
                Q(medicine_name="") | Q(dosage=0) | Q(dosage_unit="")
            )
            .values("child")
            .distinct()
            .count()
        )

        if incomplete_data_children > 0:
            opportunities.append(
                {
                    "type": "usability_feedback",
                    "description": f"{incomplete_data_children} children with incomplete data - candidates for usability feedback",
                    "priority": "medium",
                }
            )

        return opportunities

    def _collect_user_segments(self, start_date, end_date):
        """Collect anonymized user segment data"""
        segments = {}

        # Segment by usage frequency
        child_medicine_counts = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .values("child")
            .annotate(medicine_count=Count("id"))
            .values_list("medicine_count", flat=True)
        )

        # Create usage segments
        light_usage = sum(1 for count in child_medicine_counts if 1 <= count <= 5)
        moderate_usage = sum(1 for count in child_medicine_counts if 6 <= count <= 20)
        heavy_usage = sum(1 for count in child_medicine_counts if count > 20)

        segments["usage_frequency"] = {
            "light_usage_1_5_entries": light_usage,
            "moderate_usage_6_20_entries": moderate_usage,
            "heavy_usage_20_plus_entries": heavy_usage,
        }

        # Segment by feature usage
        basic_usage = (
            Medicine.objects.filter(
                time__range=[start_date, end_date],
                next_dose_interval__isnull=True,
                tags__isnull=True,
            )
            .filter(Q(notes="") | Q(notes__isnull=True))
            .values("child")
            .distinct()
            .count()
        )

        advanced_usage = (
            Medicine.objects.filter(time__range=[start_date, end_date])
            .filter(
                Q(next_dose_interval__isnull=False)
                | Q(tags__isnull=False)
                | ~Q(notes="")
            )
            .values("child")
            .distinct()
            .count()
        )

        segments["feature_usage"] = {
            "basic_usage": basic_usage,
            "advanced_usage": advanced_usage,
        }

        return segments

    def save_analytics(self, analytics_data):
        """Save analytics data to file"""
        try:
            if self.format == "json":
                with open(self.output_file, "w") as f:
                    json.dump(analytics_data, f, indent=2)
            elif self.format == "csv":
                # Flatten data for CSV
                self._save_as_csv(analytics_data)

            self.stdout.write(
                self.style.SUCCESS(f"Analytics data saved to {self.output_file}")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Failed to save analytics data: {e}"))

    def _save_as_csv(self, analytics_data):
        """Save analytics data as CSV (flattened)"""
        with open(self.output_file, "w", newline="") as csvfile:
            writer = csv.writer(csvfile)

            # Write header
            writer.writerow(["metric", "value", "category"])

            # Flatten and write data
            for category, data in analytics_data.items():
                if isinstance(data, dict):
                    for key, value in data.items():
                        if isinstance(value, (str, int, float)):
                            writer.writerow([key, value, category])
                        elif isinstance(value, list) and value:
                            writer.writerow([key, len(value), category])

    def display_analytics(self, analytics_data):
        """Display analytics data to console"""
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write("MEDICINE FEATURE ANALYTICS REPORT")
        self.stdout.write("=" * 60)

        # Usage Statistics
        usage = analytics_data["usage_statistics"]
        self.stdout.write(f"\n📊 USAGE STATISTICS:")
        self.stdout.write(
            f"  Total medicines recorded: {usage['total_medicines_recorded']}"
        )
        self.stdout.write(f"  Daily average: {usage['daily_average']}")
        self.stdout.write(f"  Active children: {usage['active_children']}")

        # Feature Adoption
        adoption = analytics_data["feature_adoption"]
        self.stdout.write(f"\n📈 FEATURE ADOPTION:")
        self.stdout.write(
            f"  Adoption rate: {adoption['adoption_rate']}% ({adoption['medicine_children']}/{adoption['total_children']} children)"
        )
        self.stdout.write(f"  Advanced features: {adoption['advanced_adoption_rate']}%")
        self.stdout.write(
            f"  Custom settings: {adoption['settings_customization_rate']}%"
        )

        # User Behavior
        behavior = analytics_data["user_behavior"]
        self.stdout.write(f"\n👥 USER BEHAVIOR:")
        self.stdout.write(f"  Interval usage rate: {behavior['interval_usage_rate']}%")
        self.stdout.write(f"  Notes usage rate: {behavior['notes_usage_rate']}%")
        self.stdout.write(f"  Tags usage rate: {behavior['tags_usage_rate']}%")

        # Performance Indicators
        performance = analytics_data["performance_indicators"]
        self.stdout.write(f"\n⚡ PERFORMANCE INDICATORS:")
        self.stdout.write(
            f"  Data completeness: {performance['data_completeness_rate']}%"
        )
        self.stdout.write(
            f"  Unique medicine names: {performance['unique_medicine_names']}"
        )
        self.stdout.write(f"  Overdue rate: {performance['overdue_rate']}%")

        # Feedback Opportunities
        opportunities = analytics_data["feedback_opportunities"]
        if opportunities:
            self.stdout.write(f"\n💬 FEEDBACK OPPORTUNITIES:")
            for opp in opportunities:
                self.stdout.write(f"  {opp['type']}: {opp['description']}")

        self.stdout.write("\n" + "=" * 60)
