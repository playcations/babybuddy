# -*- coding: utf-8 -*-
import datetime

from django.contrib.auth import get_user_model
from django.core.management import call_command
from django.test import TestCase
from django.utils import timezone

from core import models


class BMITestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.bmi = models.BMI.objects.create(
            child=self.child,
            date=timezone.localdate(),
            bmi=63.2,
        )

    def test_weight_create(self):
        self.assertEqual(self.bmi, models.BMI.objects.first())
        self.assertEqual(str(self.bmi), "BMI")
        self.assertEqual(self.bmi.bmi, 63.2)


class ChildTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)

    def test_child_create(self):
        child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.assertEqual(child, models.Child.objects.get(first_name="First"))
        self.assertEqual(child.slug, "first-last")
        self.assertEqual(str(child), "First Last")
        self.assertEqual(child.name(), "First Last")
        self.assertEqual(child.name(reverse=True), "Last, First")

    def test_child_create_without_last_name(self):
        child = models.Child.objects.create(
            first_name="Nolastname", birth_date=timezone.localdate()
        )
        self.assertEqual(child, models.Child.objects.get(first_name="Nolastname"))
        self.assertEqual(child.slug, "nolastname")
        self.assertEqual(str(child), "Nolastname")
        self.assertEqual(child.name(), "Nolastname")
        self.assertEqual(child.name(reverse=True), "Nolastname")

    def test_child_count(self):
        self.assertEqual(models.Child.count(), 0)
        models.Child.objects.create(
            first_name="First 1", last_name="Last 1", birth_date=timezone.localdate()
        )
        self.assertEqual(models.Child.count(), 1)
        child = models.Child.objects.create(
            first_name="First 2", last_name="Last 2", birth_date=timezone.localdate()
        )
        self.assertEqual(models.Child.count(), 2)
        child.delete()
        self.assertEqual(models.Child.count(), 1)

    def test_child_birth_datetime(self):
        birth_date = timezone.localdate()
        models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=birth_date
        )
        self.assertEqual(models.Child.objects.last().birth_datetime(), birth_date)
        birth_time = datetime.datetime.now().time()
        models.Child.objects.create(
            first_name="Second",
            last_name="Last",
            birth_date=birth_date,
            birth_time=birth_time,
        )
        self.assertEqual(
            models.Child.objects.last().birth_datetime(),
            timezone.make_aware(datetime.datetime.combine(birth_date, birth_time)),
        )


class DiaperChangeTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.change = models.DiaperChange.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            wet=1,
            solid=1,
            color="black",
            amount=1.25,
        )

    def test_diaperchange_create(self):
        self.assertEqual(self.change, models.DiaperChange.objects.first())
        self.assertEqual(str(self.change), "Diaper Change")
        self.assertEqual(self.change.child, self.child)
        self.assertTrue(self.change.wet)
        self.assertTrue(self.change.solid)
        self.assertEqual(self.change.color, "black")
        self.assertEqual(self.change.amount, 1.25)

    def test_diaperchange_attributes(self):
        self.assertListEqual(self.change.attributes(), ["Wet", "Solid", "Black"])


class FeedingTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_feeding_create(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="formula",
            method="bottle",
            amount=2,
        )
        self.assertEqual(feeding, models.Feeding.objects.first())
        self.assertEqual(str(feeding), "Feeding")
        self.assertEqual(feeding.duration, feeding.end - feeding.start)

    def test_method_both_breasts(self):
        feeding = models.Feeding.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
            type="breast milk",
            method="both breasts",
        )
        self.assertEqual(feeding, models.Feeding.objects.first())
        self.assertEqual(str(feeding), "Feeding")
        self.assertEqual(feeding.method, "both breasts")


class HeadCircumferenceTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.hc = models.HeadCircumference.objects.create(
            child=self.child,
            date=timezone.localdate(),
            head_circumference=13.25,
        )

    def test_weight_create(self):
        self.assertEqual(self.hc, models.HeadCircumference.objects.first())
        self.assertEqual(str(self.hc), "Head Circumference")
        self.assertEqual(self.hc.head_circumference, 13.25)


class HeightTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.height = models.Height.objects.create(
            child=self.child,
            date=timezone.localdate(),
            height=34.5,
        )

    def test_weight_create(self):
        self.assertEqual(self.height, models.Height.objects.first())
        self.assertEqual(str(self.height), "Height")
        self.assertEqual(self.height.height, 34.5)


class NoteTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_note_create(self):
        note = models.Note.objects.create(
            child=self.child, note="Note", time=timezone.localtime()
        )
        self.assertEqual(note, models.Note.objects.first())
        self.assertEqual(str(note), "Note")


class PumpingTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        start = timezone.localtime() - timezone.timedelta(days=1)
        end = start + timezone.timedelta(minutes=14)
        self.pumping = models.Pumping.objects.create(
            child=self.child,
            start=start,
            end=end,
            amount=98.6,
        )

    def test_pumping_create(self):
        self.assertEqual(self.pumping, models.Pumping.objects.first())
        self.assertEqual(str(self.pumping), "Pumping")
        self.assertEqual(self.pumping.amount, 98.6)


class SleepTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_sleep_create(self):
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
        )
        self.assertEqual(sleep, models.Sleep.objects.first())
        self.assertEqual(str(sleep), "Sleep")
        self.assertEqual(sleep.duration, sleep.end - sleep.start)

    def test_sleep_nap(self):
        models.Sleep.settings.nap_start_min = datetime.time(0, 0, 0)
        models.Sleep.settings.nap_start_max = datetime.time(23, 59, 59)
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=2)),
        )
        self.assertTrue(sleep.nap)

    def test_sleep_not_nap(self):
        models.Sleep.settings.nap_start_min = datetime.time(0, 0, 0)
        models.Sleep.settings.nap_start_max = datetime.time(0, 0, 0)
        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=8)),
        )
        self.assertFalse(sleep.nap)

        sleep = models.Sleep.objects.create(
            child=self.child,
            start=timezone.now(),
            end=(timezone.now() + timezone.timedelta(hours=8)),
            nap=True,
        )
        self.assertTrue(sleep.nap)


class TagTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_create_tag(self):
        tag1 = models.Tag.objects.create(name="Tag 1")
        self.assertEqual(tag1, models.Tag.objects.first())

        tag2 = models.Tag.objects.create(name="Tag 2")
        self.assertEqual(tag2, models.Tag.objects.filter(name="Tag 2").get())

    def test_tag_complementary_color(self):
        light_tag = models.Tag.objects.create(name="Light Tag", color="#ffffff")
        self.assertEqual(light_tag.complementary_color, models.Tag.DARK_COLOR)

        dark_tag = models.Tag.objects.create(name="Dark Tag", color="#000000")
        self.assertEqual(dark_tag.complementary_color, models.Tag.LIGHT_COLOR)

    def test_model_tagging(self):
        temp = models.Temperature.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            temperature=98.6,
        )
        temp.tags.add("Tag 1")
        self.assertEqual(
            temp.tags.all().get(), models.Tag.objects.filter(name="Tag 1").get()
        )


class TemperatureTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.temp = models.Temperature.objects.create(
            child=self.child,
            time=timezone.localtime() - timezone.timedelta(days=1),
            temperature=98.6,
        )

    def test_temperature_create(self):
        self.assertEqual(self.temp, models.Temperature.objects.first())
        self.assertEqual(str(self.temp), "Temperature")
        self.assertEqual(self.temp.temperature, 98.6)


class TimerTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.user = get_user_model().objects.first()
        self.named = models.Timer.objects.create(
            name="Named", user=self.user, child=child
        )
        self.unnamed = models.Timer.objects.create(user=self.user)

    def test_timer_create(self):
        self.assertEqual(self.named, models.Timer.objects.get(name="Named"))
        self.assertEqual(str(self.named), "Named")
        self.assertEqual(self.unnamed, models.Timer.objects.get(name=None))
        self.assertEqual(str(self.unnamed), "Timer #{}".format(self.unnamed.id))

    def test_timer_title_with_child(self):
        self.assertEqual(self.named.title_with_child, str(self.named))

        models.Child.objects.create(
            first_name="Child", last_name="Two", birth_date=timezone.localdate()
        )
        self.assertEqual(
            self.named.title_with_child,
            "{} ({})".format(str(self.named), str(self.named.child)),
        )

    def test_timer_user_username(self):
        self.assertEqual(self.named.user_username, self.user.get_username())
        self.user.first_name = "User"
        self.user.last_name = "Name"
        self.user.save()
        self.assertEqual(self.named.user_username, self.user.get_full_name())

    def test_timer_restart(self):
        self.named.restart()
        self.assertGreaterEqual(timezone.localtime(), self.named.start)

    def test_timer_duration(self):
        timer = models.Timer.objects.create(user=get_user_model().objects.first())
        timer.start = timezone.localtime() - timezone.timedelta(minutes=30)
        timer.save()
        timer.refresh_from_db()

        self.assertEqual(
            timer.duration().seconds, timezone.timedelta(minutes=30).seconds
        )


class TummyTimeTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )

    def test_tummytime_create(self):
        tummy_time = models.TummyTime.objects.create(
            child=self.child,
            start=timezone.localtime() - timezone.timedelta(minutes=30),
            end=timezone.localtime(),
        )
        self.assertEqual(tummy_time, models.TummyTime.objects.first())
        self.assertEqual(str(tummy_time), "Tummy Time")
        self.assertEqual(tummy_time.duration, tummy_time.end - tummy_time.start)


class WeightTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.weight = models.Weight.objects.create(
            child=self.child,
            date=timezone.localdate(),
            weight=23,
        )

    def test_weight_create(self):
        self.assertEqual(self.weight, models.Weight.objects.first())
        self.assertEqual(str(self.weight), "Weight")
        self.assertEqual(self.weight.weight, 23)


class MedicineTestCase(TestCase):
    def setUp(self):
        call_command("migrate", verbosity=0)
        self.child = models.Child.objects.create(
            first_name="First", last_name="Last", birth_date=timezone.localdate()
        )
        self.medicine = models.Medicine.objects.create(
            child=self.child,
            name="Tylenol",
            dosage=5.0,
            dosage_unit="ml",
            time=timezone.localtime() - timezone.timedelta(hours=1),
            next_dose_interval=timezone.timedelta(hours=4),
        )

    def test_medicine_create(self):
        self.assertEqual(self.medicine, models.Medicine.objects.first())
        self.assertEqual(str(self.medicine), "Medicine")
        self.assertEqual(self.medicine.name, "Tylenol")
        self.assertEqual(self.medicine.dosage, 5.0)
        self.assertEqual(self.medicine.dosage_unit, "ml")

    def test_next_dose_time_calculation(self):
        expected_next_dose = self.medicine.time + self.medicine.next_dose_interval
        self.assertEqual(self.medicine.next_dose_time, expected_next_dose)

    def test_next_dose_ready_property(self):
        # Medicine given 1 hour ago with 4-hour interval should not be ready
        self.assertFalse(self.medicine.next_dose_ready)

        # Medicine given 5 hours ago with 4-hour interval should be ready
        old_medicine = models.Medicine.objects.create(
            child=self.child,
            name="Old Medicine",
            dosage=2.5,
            dosage_unit="mg",
            time=timezone.localtime() - timezone.timedelta(hours=5),
            next_dose_interval=timezone.timedelta(hours=4),
        )
        self.assertTrue(old_medicine.next_dose_ready)

    def test_next_dose_ready_no_interval(self):
        # Medicine with no interval should always be ready
        no_interval_medicine = models.Medicine.objects.create(
            child=self.child,
            name="No Interval Medicine",
            dosage=1.0,
            dosage_unit="tablets",
            time=timezone.localtime(),
        )
        self.assertTrue(no_interval_medicine.next_dose_ready)

    def test_medicine_validation_positive_dosage(self):
        from django.core.exceptions import ValidationError

        medicine = models.Medicine(
            child=self.child,
            name="Test Medicine",
            dosage=-1.0,
            dosage_unit="mg",
            time=timezone.localtime(),
        )
        with self.assertRaises(ValidationError):
            medicine.full_clean()

    def test_medicine_validation_positive_interval(self):
        from django.core.exceptions import ValidationError

        medicine = models.Medicine(
            child=self.child,
            name="Test Medicine",
            dosage=5.0,
            dosage_unit="ml",
            time=timezone.localtime(),
            next_dose_interval=timezone.timedelta(seconds=-1),
        )
        with self.assertRaises(ValidationError):
            medicine.full_clean()

    def test_medicine_save_updates_next_dose_time(self):
        # Test that saving updates next_dose_time when interval changes
        original_next_dose = self.medicine.next_dose_time
        self.medicine.next_dose_interval = timezone.timedelta(hours=6)
        self.medicine.save()

        expected_new_next_dose = self.medicine.time + timezone.timedelta(hours=6)
        self.assertEqual(self.medicine.next_dose_time, expected_new_next_dose)
        self.assertNotEqual(self.medicine.next_dose_time, original_next_dose)

    def test_medicine_save_clears_next_dose_time(self):
        # Test that removing interval clears next_dose_time
        self.assertIsNotNone(self.medicine.next_dose_time)
        self.medicine.next_dose_interval = None
        self.medicine.save()
        self.assertIsNone(self.medicine.next_dose_time)

    def test_medicine_with_tags(self):
        self.medicine.tags.add("fever", "morning")
        self.assertEqual(self.medicine.tags.count(), 2)
        self.assertTrue(self.medicine.tags.filter(name="fever").exists())

    def test_medicine_validation_future_time(self):
        from django.core.exceptions import ValidationError

        future_time = timezone.localtime() + timezone.timedelta(hours=1)
        medicine = models.Medicine(
            child=self.child,
            name="Future Medicine",
            dosage=5.0,
            dosage_unit="ml",
            time=future_time,
        )
        with self.assertRaises(ValidationError):
            medicine.full_clean()

    def test_medicine_validation_tablet_whole_number(self):
        from django.core.exceptions import ValidationError

        # Test that tablet dosage must be whole number
        medicine = models.Medicine(
            child=self.child,
            name="Tablet Medicine",
            dosage=2.5,  # Half tablet should fail
            dosage_unit="tablets",
            time=timezone.localtime(),
        )
        with self.assertRaises(ValidationError):
            medicine.full_clean()

        # Test that whole number tablets work
        medicine.dosage = 2.0
        try:
            medicine.full_clean()
        except ValidationError:
            self.fail("Whole number tablet dosage should be valid")

    def test_medicine_validation_dosage_limits(self):
        from django.core.exceptions import ValidationError

        # Test dosage too high for ml
        medicine = models.Medicine(
            child=self.child,
            name="High Dose Medicine",
            dosage=1000.0,  # 1000ml is too high
            dosage_unit="ml",
            time=timezone.localtime(),
        )
        with self.assertRaises(ValidationError):
            medicine.full_clean()

        # Test dosage too low for mg
        medicine.dosage_unit = "mg"
        medicine.dosage = 0.01  # 0.01mg is too low
        with self.assertRaises(ValidationError):
            medicine.full_clean()

        # Test valid dosage
        medicine.dosage = 100.0  # 100mg is valid
        try:
            medicine.full_clean()
        except ValidationError:
            self.fail("Valid dosage should not raise ValidationError")

    def test_medicine_validation_duplicate_prevention(self):
        from django.core.exceptions import ValidationError

        # Create a duplicate medicine within 5 minutes
        duplicate_time = self.medicine.time + timezone.timedelta(minutes=2)
        duplicate_medicine = models.Medicine(
            child=self.child,
            name="Tylenol",  # Same as existing
            dosage=5.0,  # Same as existing
            dosage_unit="ml",  # Same as existing
            time=duplicate_time,  # Within 5 minutes
        )

        with self.assertRaises(ValidationError):
            duplicate_medicine.full_clean()

        # Test that medicine outside 5-minute window is allowed
        later_time = self.medicine.time + timezone.timedelta(minutes=10)
        later_medicine = models.Medicine(
            child=self.child,
            name="Tylenol",
            dosage=5.0,
            dosage_unit="ml",
            time=later_time,
        )

        try:
            later_medicine.full_clean()
        except ValidationError:
            self.fail("Medicine outside duplicate window should be valid")

        # Test that different medicine name is allowed
        different_medicine = models.Medicine(
            child=self.child,
            name="Advil",  # Different name
            dosage=5.0,
            dosage_unit="ml",
            time=duplicate_time,
        )

        try:
            different_medicine.full_clean()
        except ValidationError:
            self.fail("Different medicine should be valid")

    def test_medicine_validation_case_insensitive_duplicates(self):
        from django.core.exceptions import ValidationError

        # Test case-insensitive duplicate detection
        duplicate_time = self.medicine.time + timezone.timedelta(minutes=2)
        duplicate_medicine = models.Medicine(
            child=self.child,
            name="TYLENOL",  # Different case
            dosage=5.0,
            dosage_unit="ml",
            time=duplicate_time,
        )

        with self.assertRaises(ValidationError):
            duplicate_medicine.full_clean()
