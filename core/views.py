# -*- coding: utf-8 -*-
from django.contrib import messages
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import Count
from django.db.models.functions import Lower
from django.forms import Form
from django.http import HttpResponseRedirect
from django.views import View
from django.shortcuts import redirect
from django.urls import reverse, reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext as _
from django.views.generic.base import RedirectView, TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView

from babybuddy.mixins import LoginRequiredMixin, PermissionRequiredMixin
from babybuddy.views import BabyBuddyFilterView, BabyBuddyPaginatedView
from core import filters, forms, models, timeline


def _prepare_timeline_context_data(context, date, child=None):
    date = timezone.datetime.strptime(date, "%Y-%m-%d")
    date = timezone.localtime(timezone.make_aware(date))
    context["timeline_objects"] = timeline.get_objects(date, child)
    context["date"] = date
    context["date_previous"] = date - timezone.timedelta(days=1)
    if date.date() < timezone.localdate():
        context["date_next"] = date + timezone.timedelta(days=1)
    pass


class CoreAddView(PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    def get_success_message(self, cleaned_data):
        cleaned_data["model"] = self.model._meta.verbose_name.title()
        if "child" in cleaned_data:
            self.success_message = _("%(model)s entry for %(child)s added!")
        else:
            self.success_message = _("%(model)s entry added!")
        return self.success_message % cleaned_data

    def get_form_kwargs(self):
        """
        Check for and add "child" and "timer" from request query parameters.
          - "child" may provide a slug for a Child instance.
          - "timer" may provided an ID for a Timer instance.

        These arguments are used in some add views to pre-fill initial data in
        the form fields.

        :return: Updated keyword arguments.
        """
        kwargs = super(CoreAddView, self).get_form_kwargs()
        for parameter in ["child", "timer"]:
            value = self.request.GET.get(parameter, None)
            if value:
                kwargs.update({parameter: value})
        return kwargs


class CoreUpdateView(PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    def get_success_message(self, cleaned_data):
        cleaned_data["model"] = self.model._meta.verbose_name.title()
        if "child" in cleaned_data:
            self.success_message = _("%(model)s entry for %(child)s updated.")
        else:
            self.success_message = _("%(model)s entry updated.")
        return self.success_message % cleaned_data


class CoreDeleteView(PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    def get_success_message(self, cleaned_data):
        return _("%(model)s entry deleted.") % {
            "model": self.model._meta.verbose_name.title()
        }


class BMIList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.BMI
    template_name = "core/bmi_list.html"
    permission_required = ("core.view_bmi",)
    filterset_class = filters.BMIFilter


class BMIAdd(CoreAddView):
    model = models.BMI
    permission_required = ("core.add_bmi",)
    form_class = forms.BMIForm
    success_url = reverse_lazy("core:bmi-list")


class BMIUpdate(CoreUpdateView):
    model = models.BMI
    permission_required = ("core.change_bmi",)
    form_class = forms.BMIForm
    success_url = reverse_lazy("core:bmi-list")


class BMIDelete(CoreDeleteView):
    model = models.BMI
    permission_required = ("core.delete_bmi",)
    success_url = reverse_lazy("core:bmi-list")


class ChildList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Child
    template_name = "core/child_list.html"
    permission_required = ("core.view_child",)
    filterset_fields = ("first_name", "last_name")


class ChildAdd(CoreAddView):
    model = models.Child
    permission_required = ("core.add_child",)
    form_class = forms.ChildForm
    success_url = reverse_lazy("core:child-list")
    success_message = _("%(first_name)s %(last_name)s added!")


class ChildDetail(PermissionRequiredMixin, DetailView):
    model = models.Child
    permission_required = ("core.view_child",)

    def get_context_data(self, **kwargs):
        context = super(ChildDetail, self).get_context_data(**kwargs)
        date = self.request.GET.get("date", str(timezone.localdate()))
        _prepare_timeline_context_data(context, date, self.object)
        return context


class ChildUpdate(CoreUpdateView):
    model = models.Child
    permission_required = ("core.change_child",)
    form_class = forms.ChildForm
    success_url = reverse_lazy("core:child-list")


class ChildDelete(CoreUpdateView):
    model = models.Child
    form_class = forms.ChildDeleteForm
    template_name = "core/child_confirm_delete.html"
    permission_required = ("core.delete_child",)
    success_url = reverse_lazy("core:child-list")

    def get_success_message(self, cleaned_data):
        """This class cannot use `CoreDeleteView` because of the confirmation
        step required so the success message must be overridden."""
        success_message = _("%(model)s entry deleted.") % {
            "model": self.model._meta.verbose_name.title()
        }
        return success_message % cleaned_data


class DiaperChangeList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.DiaperChange
    template_name = "core/diaperchange_list.html"
    permission_required = ("core.view_diaperchange",)
    filterset_class = filters.DiaperChangeFilter


class DiaperChangeAdd(CoreAddView):
    model = models.DiaperChange
    permission_required = ("core.add_diaperchange",)
    form_class = forms.DiaperChangeForm
    success_url = reverse_lazy("core:diaperchange-list")


class DiaperChangeUpdate(CoreUpdateView):
    model = models.DiaperChange
    permission_required = ("core.change_diaperchange",)
    form_class = forms.DiaperChangeForm
    success_url = reverse_lazy("core:diaperchange-list")


class DiaperChangeDelete(CoreDeleteView):
    model = models.DiaperChange
    permission_required = ("core.delete_diaperchange",)
    success_url = reverse_lazy("core:diaperchange-list")


class FeedingList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Feeding
    template_name = "core/feeding_list.html"
    permission_required = ("core.view_feeding",)
    filterset_class = filters.FeedingFilter


class FeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ("core.add_feeding",)
    form_class = forms.FeedingForm
    success_url = reverse_lazy("core:feeding-list")


class BottleFeedingAdd(CoreAddView):
    model = models.Feeding
    permission_required = ("core.add_feeding",)
    form_class = forms.BottleFeedingForm
    success_url = reverse_lazy("core:feeding-list")


class FeedingUpdate(CoreUpdateView):
    model = models.Feeding
    permission_required = ("core.change_feeding",)
    form_class = forms.FeedingForm
    success_url = reverse_lazy("core:feeding-list")


class FeedingDelete(CoreDeleteView):
    model = models.Feeding
    permission_required = ("core.delete_feeding",)
    success_url = reverse_lazy("core:feeding-list")


class HeadCircumferenceList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.HeadCircumference
    template_name = "core/head_circumference_list.html"
    permission_required = ("core.view_head_circumference",)
    filterset_class = filters.HeadCircumferenceFilter


class HeadCircumferenceAdd(CoreAddView):
    model = models.HeadCircumference
    template_name = "core/head_circumference_form.html"
    permission_required = ("core.add_head_circumference",)
    form_class = forms.HeadCircumferenceForm
    success_url = reverse_lazy("core:head-circumference-list")


class HeadCircumferenceUpdate(CoreUpdateView):
    model = models.HeadCircumference
    template_name = "core/head_circumference_form.html"
    permission_required = ("core.change_head_circumference",)
    form_class = forms.HeadCircumferenceForm
    success_url = reverse_lazy("core:head-circumference-list")


class HeadCircumferenceDelete(CoreDeleteView):
    model = models.HeadCircumference
    template_name = "core/head_circumference_confirm_delete.html"
    permission_required = ("core.delete_head_circumference",)
    success_url = reverse_lazy("core:head-circumference-list")


class HeightList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Height
    template_name = "core/height_list.html"
    permission_required = ("core.view_height",)
    filterset_class = filters.HeightFilter


class HeightAdd(CoreAddView):
    model = models.Height
    permission_required = ("core.add_height",)
    form_class = forms.HeightForm
    success_url = reverse_lazy("core:height-list")


class HeightUpdate(CoreUpdateView):
    model = models.Height
    permission_required = ("core.change_height",)
    form_class = forms.HeightForm
    success_url = reverse_lazy("core:height-list")


class HeightDelete(CoreDeleteView):
    model = models.Height
    permission_required = ("core.delete_height",)
    success_url = reverse_lazy("core:height-list")


class MedicineList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Medicine
    template_name = "core/medicine_list.html"
    permission_required = ("core.view_medicine",)
    filterset_class = filters.MedicineFilter


class MedicineAdd(CoreAddView):
    model = models.Medicine
    permission_required = ("core.add_medicine",)
    form_class = forms.MedicineForm
    success_url = reverse_lazy("core:medicine-list")


class MedicineRepeatLast(CoreAddView):
    model = models.Medicine
    permission_required = ("core.add_medicine",)
    form_class = forms.MedicineForm
    success_url = reverse_lazy("core:medicine-list")
    template_name = "core/medicine_form.html"

    def get_initial(self):
        """Pre-populate form with last medicine data for the selected child."""
        initial = super().get_initial()
        child_id = self.request.GET.get("child")

        if child_id:
            try:
                child = models.Child.objects.get(id=child_id)
                last_medicine = (
                    models.Medicine.objects.filter(child=child)
                    .order_by("-time")
                    .first()
                )

                if last_medicine:
                    initial["child"] = child
                    initial["name"] = last_medicine.name
                    initial["dosage"] = last_medicine.dosage
                    initial["dosage_unit"] = last_medicine.dosage_unit
                    initial["next_dose_interval"] = last_medicine.next_dose_interval
                    initial["notes"] = last_medicine.notes
                    # Set time to now for the new entry
                    initial["time"] = timezone.localtime()

                    # Copy tags
                    if hasattr(last_medicine, "tags") and last_medicine.tags.exists():
                        initial["tags"] = ",".join(
                            [tag.name for tag in last_medicine.tags.all()]
                        )
            except (models.Child.DoesNotExist, ValueError):
                pass

        return initial

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["repeat_mode"] = True
        return context


class MedicineUpdate(CoreUpdateView):
    model = models.Medicine
    permission_required = ("core.change_medicine",)
    form_class = forms.MedicineForm
    success_url = reverse_lazy("core:medicine-list")


class MedicineDelete(CoreDeleteView):
    model = models.Medicine
    permission_required = ("core.delete_medicine",)
    success_url = reverse_lazy("core:medicine-list")


class MedicineRepeatDose(PermissionRequiredMixin, View):
    """AJAX endpoint to repeat a medicine dose"""

    permission_required = ("core.add_medicine",)

    def post(self, request, pk):
        from django.http import JsonResponse
        from django.utils import timezone

        try:
            # Get the original medicine
            original = models.Medicine.objects.get(pk=pk)

            # Create a new medicine entry with current time
            new_medicine = models.Medicine(
                child=original.child,
                name=original.name,
                dosage=original.dosage,
                dosage_unit=original.dosage_unit,
                time=timezone.now(),
                next_dose_interval=original.next_dose_interval,
                is_recurring=original.is_recurring,
                last_given_time=timezone.now(),
                is_active=True,
                notes=f"Repeated dose of {original.name}",
            )
            new_medicine.save()

            # Update the original medicine's last_given_time if it's as-needed
            if not original.is_recurring:
                original.last_given_time = timezone.now()
                original.save(update_fields=["last_given_time"])

            return JsonResponse(
                {"status": "success", "message": "Dose repeated successfully"}
            )

        except models.Medicine.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Medicine not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class MedicineRemoveActive(PermissionRequiredMixin, View):
    """AJAX endpoint to remove a medicine from active tracking"""

    permission_required = ("core.change_medicine",)

    def post(self, request, pk):
        from django.http import JsonResponse

        try:
            # Get the medicine and mark as inactive
            medicine = models.Medicine.objects.get(pk=pk)
            medicine.is_active = False
            medicine.save(update_fields=["is_active"])

            return JsonResponse(
                {"status": "success", "message": "Medicine removed from active list"}
            )

        except models.Medicine.DoesNotExist:
            return JsonResponse(
                {"status": "error", "message": "Medicine not found"}, status=404
            )
        except Exception as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=500)


class NoteList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Note
    template_name = "core/note_list.html"
    permission_required = ("core.view_note",)
    filterset_class = filters.NoteFilter


class NoteAdd(CoreAddView):
    model = models.Note
    permission_required = ("core.add_note",)
    form_class = forms.NoteForm
    success_url = reverse_lazy("core:note-list")


class NoteUpdate(CoreUpdateView):
    model = models.Note
    permission_required = ("core.change_note",)
    form_class = forms.NoteForm
    success_url = reverse_lazy("core:note-list")


class NoteDelete(CoreDeleteView):
    model = models.Note
    permission_required = ("core.delete_note",)
    success_url = reverse_lazy("core:note-list")


class PumpingList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Pumping
    template_name = "core/pumping_list.html"
    permission_required = ("core.view_pumping",)
    filterset_class = filters.PumpingFilter


class PumpingAdd(CoreAddView):
    model = models.Pumping
    permission_required = ("core.add_pumping",)
    form_class = forms.PumpingForm
    success_url = reverse_lazy("core:pumping-list")
    success_message = _("%(model)s entry added!")


class PumpingUpdate(CoreUpdateView):
    model = models.Pumping
    permission_required = ("core.change_pumping",)
    form_class = forms.PumpingForm
    success_url = reverse_lazy("core:pumping-list")
    success_message = _("%(model)s entry for %(child)s updated.")


class PumpingDelete(CoreDeleteView):
    model = models.Pumping
    permission_required = ("core.delete_pumping",)
    success_url = reverse_lazy("core:pumping-list")


class SleepList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Sleep
    template_name = "core/sleep_list.html"
    permission_required = ("core.view_sleep",)
    filterset_class = filters.SleepFilter


class SleepAdd(CoreAddView):
    model = models.Sleep
    permission_required = ("core.add_sleep",)
    form_class = forms.SleepForm
    success_url = reverse_lazy("core:sleep-list")


class SleepUpdate(CoreUpdateView):
    model = models.Sleep
    permission_required = ("core.change_sleep",)
    form_class = forms.SleepForm
    success_url = reverse_lazy("core:sleep-list")


class SleepDelete(CoreDeleteView):
    model = models.Sleep
    permission_required = ("core.delete_sleep",)
    success_url = reverse_lazy("core:sleep-list")


class TagAdminList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Tag
    template_name = "core/tag_list.html"
    permission_required = ("core.view_tags",)
    filterset_class = filters.TagFilter

    def get_queryset(self):
        return (
            super()
            .get_queryset()
            .annotate(Count("core_tagged_items"))
            .order_by(Lower("name"))
        )


class TagAdminDetail(PermissionRequiredMixin, DetailView):
    model = models.Tag
    permission_required = ("core.view_tags",)

    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.annotate(
            Count("feeding"),
            Count("diaperchange"),
            Count("pumping"),
            Count("sleep"),
            Count("tummytime"),
            Count("bmi"),
            Count("headcircumference"),
            Count("height"),
            Count("temperature"),
            Count("weight"),
        )
        return qs


class TagAdminAdd(CoreAddView):
    model = models.Tag
    permission_required = ("core.add_tag",)
    form_class = forms.TagAdminForm
    success_url = reverse_lazy("core:tag-list")


class TagAdminUpdate(CoreUpdateView):
    model = models.Tag
    permission_required = ("core.change_tag",)
    form_class = forms.TagAdminForm
    success_url = reverse_lazy("core:tag-list")


class TagAdminDelete(CoreDeleteView):
    model = models.Tag
    permission_required = ("core.delete_tag",)
    success_url = reverse_lazy("core:tag-list")

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.annotate(Count("core_tagged_items"))


class TemperatureList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.Temperature
    template_name = "core/temperature_list.html"
    permission_required = ("core.view_temperature",)
    filterset_class = filters.TemperatureFilter


class TemperatureAdd(CoreAddView):
    model = models.Temperature
    permission_required = ("core.add_temperature",)
    form_class = forms.TemperatureForm
    success_url = reverse_lazy("core:temperature-list")
    success_message = _("%(model)s reading added!")


class TemperatureUpdate(CoreUpdateView):
    model = models.Temperature
    permission_required = ("core.change_temperature",)
    form_class = forms.TemperatureForm
    success_url = reverse_lazy("core:temperature-list")
    success_message = _("%(model)s reading for %(child)s updated.")


class TemperatureDelete(CoreDeleteView):
    model = models.Temperature
    permission_required = ("core.delete_temperature",)
    success_url = reverse_lazy("core:temperature-list")


class Timeline(LoginRequiredMixin, TemplateView):
    template_name = "timeline/timeline.html"

    # Show the overall timeline or a child timeline if one Child instance.
    def get(self, request, *args, **kwargs):
        children = models.Child.objects.count()
        if children == 1:
            return HttpResponseRedirect(
                reverse("core:child", args={models.Child.objects.first().slug})
            )
        return super(Timeline, self).get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(Timeline, self).get_context_data(**kwargs)
        date = self.request.GET.get("date", str(timezone.localdate()))
        _prepare_timeline_context_data(context, date)
        return context


class TimerList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Timer
    template_name = "core/timer_list.html"
    permission_required = ("core.view_timer",)
    filterset_fields = ("user",)


class TimerDetail(PermissionRequiredMixin, DetailView):
    model = models.Timer
    permission_required = ("core.view_timer",)


class TimerAdd(PermissionRequiredMixin, CreateView):
    model = models.Timer
    permission_required = ("core.add_timer",)
    form_class = forms.TimerForm

    def get_form_kwargs(self):
        kwargs = super(TimerAdd, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_success_url(self):
        return reverse("core:timer-detail", kwargs={"pk": self.object.pk})


class TimerUpdate(CoreUpdateView):
    model = models.Timer
    permission_required = ("core.change_timer",)
    form_class = forms.TimerForm
    success_url = reverse_lazy("core:timer-list")

    def get_form_kwargs(self):
        kwargs = super(TimerUpdate, self).get_form_kwargs()
        kwargs.update({"user": self.request.user})
        return kwargs

    def get_success_url(self):
        instance = self.get_object()
        return reverse("core:timer-detail", kwargs={"pk": instance.pk})


class TimerAddQuick(PermissionRequiredMixin, RedirectView):
    http_method_names = ["post"]
    permission_required = ("core.add_timer",)

    def post(self, request, *args, **kwargs):
        instance = models.Timer.objects.create(user=request.user)
        # Find child from child pk in POST
        child_id = request.POST.get("child", False)
        child = models.Child.objects.get(pk=child_id) if child_id else None
        if child:
            instance.child = child
        # Add child relationship if there is only Child instance.
        elif models.Child.count() == 1:
            instance.child = models.Child.objects.first()
        instance.save()
        self.url = request.GET.get(
            "next", reverse("core:timer-detail", args={instance.id})
        )
        return super(TimerAddQuick, self).get(request, *args, **kwargs)


class TimerRestart(PermissionRequiredMixin, RedirectView):
    http_method_names = ["post"]
    permission_required = ("core.change_timer",)

    def post(self, request, *args, **kwargs):
        instance = models.Timer.objects.get(id=kwargs["pk"])
        instance.restart()
        messages.success(request, "{} restarted.".format(instance))
        return super(TimerRestart, self).get(request, *args, **kwargs)

    def get_redirect_url(self, *args, **kwargs):
        return reverse("core:timer-detail", kwargs={"pk": kwargs["pk"]})


class TimerDelete(CoreDeleteView):
    model = models.Timer
    permission_required = ("core.delete_timer",)
    success_url = reverse_lazy("core:timer-list")


class TummyTimeList(
    PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView
):
    model = models.TummyTime
    template_name = "core/tummytime_list.html"
    permission_required = ("core.view_tummytime",)
    filterset_class = filters.TummyTimeFilter


class TummyTimeAdd(CoreAddView):
    model = models.TummyTime
    permission_required = ("core.add_tummytime",)
    form_class = forms.TummyTimeForm
    success_url = reverse_lazy("core:tummytime-list")


class TummyTimeUpdate(CoreUpdateView):
    model = models.TummyTime
    permission_required = ("core.change_tummytime",)
    form_class = forms.TummyTimeForm
    success_url = reverse_lazy("core:tummytime-list")


class TummyTimeDelete(CoreDeleteView):
    model = models.TummyTime
    permission_required = ("core.delete_tummytime",)
    success_url = reverse_lazy("core:tummytime-list")


class WeightList(PermissionRequiredMixin, BabyBuddyPaginatedView, BabyBuddyFilterView):
    model = models.Weight
    template_name = "core/weight_list.html"
    permission_required = ("core.view_weight",)
    filterset_class = filters.WeightFilter


class WeightAdd(CoreAddView):
    model = models.Weight
    permission_required = ("core.add_weight",)
    form_class = forms.WeightForm
    success_url = reverse_lazy("core:weight-list")


class WeightUpdate(CoreUpdateView):
    model = models.Weight
    permission_required = ("core.change_weight",)
    form_class = forms.WeightForm
    success_url = reverse_lazy("core:weight-list")


class WeightDelete(CoreDeleteView):
    model = models.Weight
    permission_required = ("core.delete_weight",)
    success_url = reverse_lazy("core:weight-list")
