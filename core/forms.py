# -*- coding: utf-8 -*-
from django import forms
from django.forms import widgets
from django.conf import settings
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from taggit.forms import TagField

from babybuddy.widgets import DateInput, DateTimeInput, TimeInput
from core import models
from core.models import Timer
from core.widgets import (
    TagsEditor,
    ChildRadioSelect,
    PillRadioSelect,
    DoseIntervalWidget,
)


def set_initial_values(kwargs, form_type):
    """
    Sets initial value for add forms based on provided kwargs.

    :param kwargs: Keyword arguments.
    :param form_type: Class of the type of form being initialized.
    :return: Keyword arguments with updated "initial" values.
    """

    # Never update initial values for existing instance (e.g. edit operation).
    if kwargs.get("instance", None):
        return kwargs

    # Add the "initial" kwarg if it does not already exist.
    if not kwargs.get("initial"):
        kwargs.update(initial={})

    # Set Child based on `child` kwarg or single Chile database.
    child_slug = kwargs.get("child", None)
    if child_slug:
        kwargs["initial"].update(
            {
                "child": models.Child.objects.filter(slug=child_slug).first(),
            }
        )
    elif models.Child.count() == 1:
        kwargs["initial"].update({"child": models.Child.objects.first()})

    # Set start and end time based on Timer from `timer` kwarg.
    timer_id = kwargs.get("timer", None)
    if timer_id:
        try:
            timer = models.Timer.objects.get(id=timer_id)
            kwargs["initial"].update(
                {"timer": timer, "start": timer.start, "end": timezone.now()}
            )
        except Timer.DoesNotExist:
            pass

    # Set type and method values for Feeding instance based on last feed.
    if form_type == FeedingForm and "child" in kwargs["initial"]:
        last_feeding = (
            models.Feeding.objects.filter(child=kwargs["initial"]["child"])
            .order_by("end")
            .last()
        )
        if last_feeding:
            last_method = last_feeding.method
            last_feed_args = {"type": last_feeding.type}
            if last_method not in ["left breast", "right breast"]:
                last_feed_args["method"] = last_method
            kwargs["initial"].update(last_feed_args)

    # Set default "nap" value for Sleep instances.
    if form_type == SleepForm and "nap" not in kwargs["initial"]:
        try:
            start = timezone.localtime(kwargs["initial"]["start"]).time()
        except KeyError:
            start = timezone.localtime().time()
        nap = (
            models.Sleep.settings.nap_start_min
            <= start
            <= models.Sleep.settings.nap_start_max
        )
        kwargs["initial"].update({"nap": nap})

    # Remove custom kwargs, so they do not interfere with `super` calls.
    for key in ["child", "timer"]:
        try:
            kwargs.pop(key)
        except KeyError:
            pass

    return kwargs


class CoreModelForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        # Set `timer_id` so the Timer can be stopped in the `save` method.
        self.timer_id = kwargs.get("timer", None)
        kwargs = set_initial_values(kwargs, type(self))
        super(CoreModelForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        # If `timer_id` is present, stop the Timer.
        instance = super(CoreModelForm, self).save(commit=False)
        if self.timer_id:
            timer = models.Timer.objects.get(id=self.timer_id)
            timer.stop()
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    @property
    def hydrated_fielsets(self):
        # for some reason self.fields returns defintions and not bound fields
        # so until i figure out a better way we can just create a dict here
        # https://github.com/django/django/blob/main/django/forms/forms.py#L52

        bound_field_dict = {}
        for field in self:
            bound_field_dict[field.name] = field

        hydrated_fieldsets = []

        for fieldset in self.fieldsets:
            hyrdrated_fieldset = {
                "layout": fieldset.get("layout", "default"),
                "layout_attrs": fieldset.get("layout_attrs", {}),
                "fields": [],
            }
            for field_name in fieldset["fields"]:
                hyrdrated_fieldset["fields"].append(bound_field_dict[field_name])

            hydrated_fieldsets.append(hyrdrated_fieldset)

        return hydrated_fieldsets


class TaggableModelForm(forms.ModelForm):
    tags = TagField(
        label=_("Tags"),
        widget=TagsEditor,
        required=False,
        strip=True,
        help_text=_(
            "Click on the tags to add (+) or remove (-) tags or use the text editor to create new tags."
        ),
    )


class BMIForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "bmi", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.BMI
        fields = ["child", "bmi", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class BottleFeedingForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["child", "type", "start", "amount"], "layout": "required"},
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    def clean(self):
        cleaned_data = super().clean()
        # Ensure end time equals start time for bottle feedings
        if "start" in cleaned_data:
            cleaned_data["end"] = cleaned_data["start"]

        # Set instance attributes before model validation runs
        if hasattr(self, "instance") and self.instance and "start" in cleaned_data:
            self.instance.method = "bottle"
            self.instance.end = cleaned_data["start"]

        return cleaned_data

    def save(self, commit=True):
        instance = super(BottleFeedingForm, self).save(commit=False)
        instance.method = "bottle"
        instance.end = instance.start
        if commit:
            instance.save()
            self.save_m2m()
        return instance

    class Meta:
        model = models.Feeding
        fields = ["child", "start", "type", "amount", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "type": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class ChildForm(forms.ModelForm):
    class Meta:
        model = models.Child
        fields = ["first_name", "last_name", "birth_date", "birth_time"]
        if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
            fields.append("picture")
        widgets = {
            "birth_date": DateInput(),
            "birth_time": TimeInput(),
        }


class ChildDeleteForm(forms.ModelForm):
    confirm_name = forms.CharField(max_length=511)

    class Meta:
        model = models.Child
        fields = []

    def clean_confirm_name(self):
        confirm_name = self.cleaned_data["confirm_name"]
        if confirm_name != str(self.instance):
            raise forms.ValidationError(
                _("Name does not match child name."), code="confirm_mismatch"
            )
        return confirm_name

    def save(self, commit=True):
        instance = self.instance
        self.instance.delete()
        return instance


class DiaperChangeForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["child", "time"], "layout": "required"},
        {
            "fields": ["wet", "solid"],
            "layout": "choices",
            "layout_attrs": {"label": "Contents"},
        },
        {"fields": ["color", "amount"]},
        {"layout": "advanced", "fields": ["notes", "tags"]},
    ]

    class Meta:
        model = models.DiaperChange
        fields = ["child", "time", "wet", "solid", "color", "amount", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect(),
            "color": PillRadioSelect(),
            "time": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class FeedingForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["child", "start", "end", "type", "method"], "layout": "required"},
        {"fields": ["amount"]},
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Feeding
        fields = ["child", "start", "end", "type", "method", "amount", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "type": PillRadioSelect(),
            "method": PillRadioSelect(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class HeadCircumferenceForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "head_circumference", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.HeadCircumference
        fields = ["child", "head_circumference", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class HeightForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "height", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Height
        fields = ["child", "height", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class MedicineForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "time", "name", "dosage", "dosage_unit"],
            "layout": "required",
        },
        {"fields": ["is_recurring", "next_dose_interval"]},
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Medicine
        fields = [
            "child",
            "name",
            "dosage",
            "dosage_unit",
            "time",
            "is_recurring",
            "next_dose_interval",
            "notes",
            "tags",
        ]
        widgets = {
            "child": ChildRadioSelect,
            "dosage_unit": PillRadioSelect(),
            "time": DateTimeInput(),
            "next_dose_interval": DoseIntervalWidget(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Set default interval to 12 hours for new medicines
        if not self.instance.pk and not self.initial.get("next_dose_interval"):
            from datetime import timedelta

            self.initial["next_dose_interval"] = timedelta(hours=12)

        # Update field labels and help text based on context
        self.fields["is_recurring"].label = "Recurring Medication"
        self.fields["is_recurring"].help_text = (
            "Check if this medication is given on a schedule (leave unchecked for as-needed relief medications)"
        )

        # Set up dynamic label for interval field - will be updated by JavaScript
        self.fields["next_dose_interval"].label = "Safety Window"
        self.fields["next_dose_interval"].help_text = (
            "Minimum time between doses for safety"
        )


class PumpingForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["child", "start", "end"], "layout": "required"},
        {"fields": ["amount"]},
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Pumping
        fields = ["child", "start", "end", "amount", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class NoteForm(CoreModelForm, TaggableModelForm):
    class Meta:
        model = models.Note
        fields = ["child", "note", "time", "tags"]
        if settings.BABY_BUDDY["ALLOW_UPLOADS"]:
            fields.insert(2, "image")
        widgets = {
            "child": ChildRadioSelect,
            "time": DateTimeInput(),
        }


class SleepForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "start", "end", "nap"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Sleep
        fields = ["child", "start", "end", "nap", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class TagAdminForm(CoreModelForm):
    fieldsets = [
        {
            "fields": ["name", "color"],
            "layout": "required",
        }
    ]

    class Meta:
        model = models.Tag
        fields = ["name", "color"]
        readonly_fields = ["slug"]
        widgets = {
            "color": widgets.TextInput(
                attrs={"type": "color", "class": "form-control-color"}
            )
        }


class TemperatureForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "temperature", "time"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Temperature
        fields = ["child", "temperature", "time", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "time": DateTimeInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }


class TimerForm(CoreModelForm):
    class Meta:
        model = models.Timer
        fields = ["child", "name", "start"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop("user")
        super(TimerForm, self).__init__(*args, **kwargs)

    def save(self, commit=True):
        instance = super(TimerForm, self).save(commit=False)
        instance.user = self.user
        instance.save()
        return instance


class TummyTimeForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {"fields": ["child", "start", "end"], "layout": "required"},
        {"fields": ["milestone"]},
        {"fields": ["tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.TummyTime
        fields = ["child", "start", "end", "milestone", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "start": DateTimeInput(),
            "end": DateTimeInput(),
        }


class WeightForm(CoreModelForm, TaggableModelForm):
    fieldsets = [
        {
            "fields": ["child", "weight", "date"],
            "layout": "required",
        },
        {"fields": ["notes", "tags"], "layout": "advanced"},
    ]

    class Meta:
        model = models.Weight
        fields = ["child", "weight", "date", "notes", "tags"]
        widgets = {
            "child": ChildRadioSelect,
            "date": DateInput(),
            "notes": forms.Textarea(attrs={"rows": 5}),
        }
