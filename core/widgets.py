import datetime
from typing import Any, Dict, Optional

from django.forms import RadioSelect, widgets
from django.forms.widgets import MultiWidget, NumberInput, Select

from . import models


class TagsEditor(widgets.Widget):
    """
    Custom widget that provides an alternative editor for tags provided by the
    taggit library.

    The widget makes use of bootstrap v4 and its badge/pill feature and renders
    a list of tags as badges that can be clicked to remove or add a tag to
    the list of set tags. In addition, a user can dynamically add new, custom
    tags, using a text editor.
    """

    class Media:
        js = ("babybuddy/js/tags_editor.js",)

    input_type = "hidden"
    template_name = "core/widget_tag_editor.html"

    @staticmethod
    def __unpack_tag(tag: models.Tag):
        """
        Tiny utility function used to translate a tag to a serializable
        dictionary of strings.
        """
        return {"name": tag.name, "color": tag.color}

    def format_value(self, value: Any) -> Optional[str]:
        """
        Override format_value to provide a list of dictionaries rather than
        a flat, comma-separated list of tags. This allows for the more
        complex rendering of tags provided by this plugin.
        """
        if value is not None and not isinstance(value, str):
            value = [self.__unpack_tag(tag) for tag in value]
        return value

    def build_attrs(self, base_attrs, extra_attrs=None):
        """
        Bootstrap integration adds form-control to the classes of the widget.
        This works only for "plain" input-based widgets however. In addition,
        we need to add a custom class "babybuddy-tags-editor" for the javascript
        file to detect the widget and take control of its contents.
        """
        attrs = super().build_attrs(base_attrs, extra_attrs)
        class_string = attrs.get("class", "")
        class_string = class_string.replace("form-control", "")
        attrs["class"] = class_string + " babybuddy-tags-editor"
        return attrs

    def get_context(self, name: str, value: Any, attrs) -> Dict[str, Any]:
        """
        Adds extra information to the payload provided to the widget's template.

        Specifically:
        - Query a list if "recently used" tags (max 256 to not cause
          DoS issues) from the database to be used for auto-completion. ("most")
        - Query a smaller list of 5 tags to be made available from a quick
          selection widget ("quick").
        """
        most_tags = models.Tag.objects.order_by("-last_used").all()[:256]

        result = super().get_context(name, value, attrs)

        tag_names = set(
            x["name"] for x in (result.get("widget", {}).get("value", None) or [])
        )
        quick_suggestion_tags = [t for t in most_tags if t.name not in tag_names][:5]

        result["widget"]["tag_suggestions"] = {
            "quick": [
                self.__unpack_tag(t)
                for t in quick_suggestion_tags
                if t.name not in tag_names
            ],
            "most": [self.__unpack_tag(t) for t in most_tags],
        }
        return result


class ChildRadioSelect(RadioSelect):
    input_type = "radio"
    template_name = "core/child_radio.html"
    option_template_name = "core/child_radio_option.html"
    attrs = {"class": "btn-check"}

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["class"] += " btn-check"
        return attrs

    def create_option(
        self, name, value, label, selected, index, subindex=None, attrs=None
    ):
        option = super().create_option(
            name, value, label, selected, index, subindex, attrs
        )
        if value != "":
            option["picture"] = value.instance.picture
        return option


class PillRadioSelect(RadioSelect):
    input_type = "radio"
    template_name = "core/pill_radio.html"
    option_template_name = "core/pill_radio_option.html"

    attrs = {"class": "btn-check"}

    def build_attrs(self, base_attrs, extra_attrs=None):
        attrs = super().build_attrs(base_attrs, extra_attrs)
        attrs["class"] += " btn-check"
        return attrs


class DoseIntervalWidget(widgets.Widget):
    """
    Custom widget for dose intervals using a select dropdown with common intervals
    and a number input with spinner for custom hours.
    """

    template_name = "core/dose_interval_widget.html"

    def __init__(self, attrs=None):
        super().__init__(attrs)
        self.common_intervals = [
            ("", "-- Select Common Interval --"),
            ("0:0:15", "Every 15 minutes"),
            ("0:0:30", "Every 30 minutes"),
            ("0:0:45", "Every 45 minutes"),
            ("0:1:0", "Every hour"),
            ("0:2:0", "Every 2 hours"),
            ("0:3:0", "Every 3 hours"),
            ("0:4:0", "Every 4 hours"),
            ("0:6:0", "Every 6 hours"),
            ("0:8:0", "Every 8 hours"),
            ("0:12:0", "Every 12 hours (twice daily)"),
            ("1:0:0", "Daily (once per day)"),
            ("2:0:0", "Every 2 days"),
            ("3:0:0", "Every 3 days"),
            ("7:0:0", "Weekly"),
            ("14:0:0", "Every 2 weeks"),
            ("30:0:0", "Monthly"),
            ("custom", "Custom interval..."),
        ]

    def value_from_datadict(self, data, files, name):
        """Convert form data back to timedelta"""
        interval_type = data.get(name + "_type", "")
        custom_days = data.get(name + "_custom_days", "")
        custom_hours = data.get(name + "_custom_hours", "")
        custom_minutes = data.get(name + "_custom_minutes", "")

        try:
            if interval_type == "custom":
                days = int(custom_days) if custom_days else 0
                hours = int(custom_hours) if custom_hours else 0
                minutes = int(custom_minutes) if custom_minutes else 0
            elif interval_type == "":
                return None  # No interval selected
            else:
                # Parse days:hours:minutes format
                if ":" in interval_type:
                    parts = interval_type.split(":")
                    days = int(parts[0]) if len(parts) > 0 else 0
                    hours = int(parts[1]) if len(parts) > 1 else 0
                    minutes = int(parts[2]) if len(parts) > 2 else 0
                else:
                    days = int(interval_type)
                    hours = 0
                    minutes = 0

            if days <= 0 and hours <= 0 and minutes <= 0:
                return None

            return datetime.timedelta(days=days, hours=hours, minutes=minutes)
        except (ValueError, TypeError):
            return None

    def format_value(self, value):
        """Convert timedelta to form data for display"""
        if not value:
            return {
                "type": "",
                "custom_days": "",
                "custom_hours": "",
                "custom_minutes": "",
            }

        if isinstance(value, datetime.timedelta):
            days = value.days
            total_seconds = int(value.total_seconds())
            remaining_seconds = total_seconds - (days * 24 * 3600)
            hours = remaining_seconds // 3600
            minutes = (remaining_seconds % 3600) // 60
        elif isinstance(value, str):
            # Handle string formats
            try:
                if "day" in value:
                    # Format like "1 day, 2:00:00"
                    parts = value.split()
                    days = int(parts[0]) if parts[0].isdigit() else 0
                    if "," in value:
                        time_part = value.split(",")[1].strip()
                        time_parts = time_part.split(":")
                        hours = int(time_parts[0]) if len(time_parts) > 0 else 0
                        minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
                    else:
                        hours = 0
                        minutes = 0
                elif ":" in value:
                    # Format like "04:00:00"
                    time_parts = value.split(":")
                    days = 0
                    hours = int(time_parts[0]) if len(time_parts) > 0 else 0
                    minutes = int(time_parts[1]) if len(time_parts) > 1 else 0
                else:
                    days = 0
                    hours = 0
                    minutes = 0
            except (ValueError, IndexError):
                days = 0
                hours = 0
                minutes = 0
        else:
            days = 0
            hours = 0
            minutes = 0

        # Check if it matches a common interval
        interval_key = f"{days}:{hours}:{minutes}"
        for interval_value, _ in self.common_intervals[1:-1]:  # Skip header and custom
            if interval_value != "custom" and interval_value == interval_key:
                return {
                    "type": interval_value,
                    "custom_days": str(days),
                    "custom_hours": str(hours),
                    "custom_minutes": str(minutes),
                }

        # Custom interval
        return {
            "type": "custom",
            "custom_days": str(days),
            "custom_hours": str(hours),
            "custom_minutes": str(minutes),
        }

    def get_context(self, name, value, attrs):
        """Prepare context for template rendering"""
        context = super().get_context(name, value, attrs)

        # If no value provided, use 12 hours as default
        if not value:
            import datetime

            value = datetime.timedelta(hours=12)

        formatted_value = self.format_value(value)
        context["widget"]["common_intervals"] = self.common_intervals
        context["widget"]["selected_type"] = formatted_value["type"]
        context["widget"]["custom_days"] = formatted_value["custom_days"]
        context["widget"]["custom_hours"] = formatted_value["custom_hours"]
        context["widget"]["custom_minutes"] = formatted_value["custom_minutes"]

        return context
