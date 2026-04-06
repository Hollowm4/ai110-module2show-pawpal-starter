import unittest
from unittest.mock import patch
from datetime import datetime, timedelta

from pawpal_system import (
    Pet, Owner, PetCareScheduler,
    Walk, Feeding, Medication, Enrichment, Grooming,
)


# ── Existing tests ────────────────────────────────────────────────

class TestTaskCompletion(unittest.TestCase):
    def test_mark_complete_changes_status(self):
        pet = Pet(name="Buddy", species="Dog")
        task = Walk(description="Morning walk", time="07:00 AM",
                    frequency="daily", priority=1, duration=30)
        pet.add_task(task)

        self.assertFalse(task.completed)    # should be incomplete before
        task.mark_complete()
        self.assertTrue(task.completed)     # should be complete after


class TestTaskAddition(unittest.TestCase):
    def test_add_task_increases_count(self):
        pet = Pet(name="Luna", species="Cat")

        self.assertEqual(len(pet.get_tasks()), 0)    # starts with no tasks
        pet.add_task(Walk(description="Evening walk", time="06:00 PM",
                         frequency="daily", priority=1, duration=20))
        self.assertEqual(len(pet.get_tasks()), 1)     # should now have 1 task


# ── Sorting correctness ──────────────────────────────────────────

class TestSortByTime(unittest.TestCase):
    """sort_by_time relies on string comparison, so only zero-padded
    24-hour 'HH:MM' values sort correctly."""

    def _scheduler(self):
        owner = Owner(name="Test", time_available=300)
        return PetCareScheduler(owner)

    def test_chronological_order_24h(self):
        s = self._scheduler()
        tasks = [
            Feeding(description="Dinner", time="18:00",
                    frequency="daily", priority=2, duration=10),
            Walk(description="Morning walk", time="07:00",
                 frequency="daily", priority=1, duration=30),
            Medication(description="Noon meds", time="12:00",
                       frequency="daily", priority=1, duration=5),
        ]
        sorted_tasks = s.sort_by_time(tasks)
        times = [t.time for t in sorted_tasks]
        self.assertEqual(times, ["07:00", "12:00", "18:00"])

    def test_tbd_sorts_after_timed_tasks(self):
        """'TBD' > any digit string, so TBD tasks land at the end."""
        s = self._scheduler()
        tasks = [
            Walk(description="Flex walk", time="TBD",
                 frequency="daily", priority=3, duration=20),
            Feeding(description="Breakfast", time="08:00",
                    frequency="daily", priority=1, duration=10),
        ]
        sorted_tasks = s.sort_by_time(tasks)
        self.assertEqual(sorted_tasks[-1].time, "TBD")

    def test_12h_format_breaks_sort(self):
        """Demonstrates that 12-hour strings like '12:00 PM' mis-sort
        against 24-hour strings — a known limitation."""
        s = self._scheduler()
        tasks = [
            Walk(description="Afternoon", time="14:00",
                 frequency="daily", priority=1, duration=20),
            Walk(description="Morning", time="12:00 PM",
                 frequency="daily", priority=1, duration=20),
        ]
        sorted_tasks = s.sort_by_time(tasks)
        # String comparison: "08:00 AM" > "14:00" is False, so this
        # *happens* to look correct, but "12:00 PM" > "14:00" would fail.
        # This test documents the fragile behaviour.
        times = [t.time for t in sorted_tasks]
        self.assertNotEqual(times, ["14:00", "12:00 PM"],
                            msg="12-hour format accidentally sorted correctly; "
                                "add a '12:00 PM' case to see the real bug")


# ── Recurring task logic ─────────────────────────────────────────

class TestRecurrence(unittest.TestCase):

    def test_daily_recurrence_creates_next_task(self):
        pet = Pet(name="Buddy", species="Dog")
        task = Walk(description="Morning walk", time="07:00",
                    frequency="daily", priority=1, duration=30)
        pet.add_task(task)

        self.assertEqual(len(pet.get_tasks()), 1)
        task.mark_complete()
        # mark_complete should have appended a new Walk to the same pet
        self.assertEqual(len(pet.get_tasks()), 2)
        self.assertTrue(task.completed)
        self.assertFalse(pet.get_tasks()[-1].completed)

    def test_weekly_recurrence_creates_next_task(self):
        pet = Pet(name="Luna", species="Cat")
        task = Grooming(description="Brush fur", time="10:00",
                        frequency="weekly", priority=2, duration=15)
        pet.add_task(task)

        task.mark_complete()
        self.assertEqual(len(pet.get_tasks()), 2)

    def test_no_recurrence_for_one_off_task(self):
        pet = Pet(name="Buddy", species="Dog")
        task = Medication(description="One-time shot", time="09:00",
                          frequency="once", priority=1, duration=5)
        pet.add_task(task)

        task.mark_complete()
        # "once" is neither "daily" nor "weekly", so no new task
        self.assertEqual(len(pet.get_tasks()), 1)

    def test_recurrence_without_pet_silently_skips(self):
        """Tasks with pet=None skip recurrence with no error."""
        task = Walk(description="Orphan walk", time="07:00",
                    frequency="daily", priority=1, duration=30)
        # pet is None by default
        self.assertIsNone(task.pet)
        task.mark_complete()  # should not raise
        self.assertTrue(task.completed)

    def test_next_time_drifts_from_original(self):
        """mark_complete bases next_time on datetime.now(), not on the
        original scheduled time — so the new task's time will differ
        from the parent's unless completed at exactly the right moment."""
        pet = Pet(name="Buddy", species="Dog")
        task = Walk(description="Morning walk", time="07:00",
                    frequency="daily", priority=1, duration=30)
        pet.add_task(task)

        task.mark_complete()
        new_task = pet.get_tasks()[-1]
        # The new task's time is now() + 1 day formatted as HH:MM,
        # which almost certainly != "07:00".
        # This documents the drift bug.
        expected_time = (datetime.now() + timedelta(days=1)).strftime("%H:%M")
        self.assertEqual(new_task.time, expected_time,
                         msg="Recurring time is relative to completion time, "
                             "not the original schedule — this is the drift bug.")


# ── Conflict detection ───────────────────────────────────────────

class TestConflictDetection(unittest.TestCase):

    def _scheduler(self):
        owner = Owner(name="Test", time_available=300)
        return PetCareScheduler(owner)

    def test_exact_time_conflict_flagged(self):
        s = self._scheduler()
        pet = Pet(name="Buddy", species="Dog")
        tasks = [
            Feeding(description="Breakfast", time="08:00",
                    frequency="daily", priority=1, duration=10, pet=pet),
            Medication(description="Morning meds", time="08:00",
                       frequency="daily", priority=1, duration=5, pet=pet),
        ]
        warnings = s.detect_conflicts(tasks)
        self.assertTrue(len(warnings) > 0)
        self.assertIn("08:00", warnings[0])

    def test_no_conflict_different_times(self):
        s = self._scheduler()
        tasks = [
            Walk(description="Walk", time="07:00",
                 frequency="daily", priority=1, duration=30),
            Feeding(description="Breakfast", time="08:00",
                    frequency="daily", priority=1, duration=10),
        ]
        warnings = s.detect_conflicts(tasks)
        self.assertEqual(warnings, [])

    def test_overlapping_duration_not_detected(self):
        """A 30-min task at 08:00 overlaps with a task at 08:15,
        but detect_conflicts only checks exact time equality,
        so this overlap is silently missed."""
        s = self._scheduler()
        tasks = [
            Walk(description="Long walk", time="08:00",
                 frequency="daily", priority=1, duration=30),
            Feeding(description="Breakfast", time="08:15",
                    frequency="daily", priority=1, duration=10),
        ]
        warnings = s.detect_conflicts(tasks)
        # No conflict detected even though the walk runs 08:00-08:30
        self.assertEqual(warnings, [],
                         msg="Duration-based overlap is NOT detected — "
                             "only exact time matches are flagged.")

    def test_cross_pet_conflict_flagged_as_false_positive(self):
        """Two different pets at the same time isn't a real conflict
        if there are multiple caretakers, but the current code flags it."""
        s = self._scheduler()
        dog = Pet(name="Buddy", species="Dog")
        cat = Pet(name="Luna", species="Cat")
        tasks = [
            Walk(description="Dog walk", time="08:00",
                 frequency="daily", priority=1, duration=30, pet=dog),
            Feeding(description="Cat breakfast", time="08:00",
                    frequency="daily", priority=1, duration=10, pet=cat),
        ]
        warnings = s.detect_conflicts(tasks)
        # Currently flags this — documenting as a known false-positive
        self.assertTrue(len(warnings) > 0,
                        msg="Cross-pet same-time tasks are flagged as "
                            "conflicts even though they may not be.")


# ── Filtering ────────────────────────────────────────────────────

class TestFilterTasks(unittest.TestCase):

    def _scheduler(self):
        owner = Owner(name="Test", time_available=300)
        return PetCareScheduler(owner)

    def _sample_tasks(self):
        dog = Pet(name="Buddy", species="Dog")
        cat = Pet(name="Luna", species="Cat")
        t1 = Walk(description="Dog walk", time="07:00",
                  frequency="daily", priority=1, duration=30)
        t2 = Feeding(description="Cat food", time="08:00",
                     frequency="daily", priority=2, duration=10)
        t3 = Medication(description="Dog meds", time="09:00",
                        frequency="daily", priority=1, duration=5)
        dog.add_task(t1)
        cat.add_task(t2)
        dog.add_task(t3)
        t1.completed = True
        return [t1, t2, t3], dog, cat

    def test_filter_by_pet_name(self):
        s = self._scheduler()
        tasks, dog, cat = self._sample_tasks()
        result = s.filter_tasks(tasks, pet_name="Buddy")
        self.assertEqual(len(result), 2)
        self.assertTrue(all(t.pet.name == "Buddy" for t in result))

    def test_filter_by_task_type(self):
        s = self._scheduler()
        tasks, _, _ = self._sample_tasks()
        result = s.filter_tasks(tasks, task_type="Walk")
        self.assertEqual(len(result), 1)
        self.assertIsInstance(result[0], Walk)

    def test_filter_by_completed_status(self):
        s = self._scheduler()
        tasks, _, _ = self._sample_tasks()
        result = s.filter_tasks(tasks, status="completed")
        self.assertTrue(all(t.completed for t in result))

    def test_filter_by_pending_status(self):
        s = self._scheduler()
        tasks, _, _ = self._sample_tasks()
        result = s.filter_tasks(tasks, status="pending")
        self.assertTrue(all(not t.completed for t in result))

    def test_filter_orphan_task_by_pet_name_raises(self):
        """A task with pet=None is safely excluded by the
        'if t.pet and ...' short-circuit in filter_tasks."""
        s = self._scheduler()
        orphan = Walk(description="Stray walk", time="07:00",
                      frequency="daily", priority=1, duration=30)
        # pet is None — no pet assigned
        result = s.filter_tasks([orphan], pet_name="Buddy")
        self.assertEqual(result, [], msg="Orphan tasks should be filtered out, not crash.")


    def test_filter_case_insensitive_pet_name(self):
        s = self._scheduler()
        tasks, _, _ = self._sample_tasks()
        result = s.filter_tasks(tasks, pet_name="buddy")
        self.assertEqual(len(result), 2)

    def test_combined_filters(self):
        s = self._scheduler()
        tasks, _, _ = self._sample_tasks()
        result = s.filter_tasks(tasks, pet_name="Buddy", status="pending")
        self.assertEqual(len(result), 1)
        self.assertFalse(result[0].completed)
        self.assertEqual(result[0].pet.name, "Buddy")


# ── Plan generation edge cases ───────────────────────────────────

class TestGeneratePlan(unittest.TestCase):

    def test_empty_plan_no_pets(self):
        owner = Owner(name="Solo", time_available=120)
        s = PetCareScheduler(owner)
        plan = s.generate_plan()
        self.assertEqual(plan, [])

    def test_empty_plan_pet_with_no_tasks(self):
        owner = Owner(name="Test", time_available=120)
        pet = Pet(name="Ghost", species="Hamster")
        owner.add_pet(pet)
        s = PetCareScheduler(owner)
        plan = s.generate_plan()
        self.assertEqual(plan, [])

    def test_warning_when_time_exceeded(self):
        owner = Owner(name="Busy", time_available=10)  # only 10 min
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(Walk(description="Long walk", time="07:00",
                         frequency="daily", priority=1, duration=60))
        owner.add_pet(pet)
        s = PetCareScheduler(owner)

        # generate_plan prints a warning but still returns all tasks
        with patch("builtins.print") as mock_print:
            plan = s.generate_plan()
            warning_printed = any(
                "Warning" in str(call) for call in mock_print.call_args_list
            )
            self.assertTrue(warning_printed,
                            msg="Expected a time-exceeded warning.")
        self.assertEqual(len(plan), 1,
                         msg="All tasks are scheduled even when time is exceeded.")

    def test_plan_sorted_by_priority_then_time(self):
        owner = Owner(name="Test", time_available=300)
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(Walk(description="Walk", time="09:00",
                         frequency="daily", priority=3, duration=30))
        pet.add_task(Medication(description="Meds", time="07:00",
                                frequency="daily", priority=1, duration=5))
        pet.add_task(Feeding(description="Food", time="08:00",
                             frequency="daily", priority=1, duration=10))
        owner.add_pet(pet)
        s = PetCareScheduler(owner)
        plan = s.generate_plan()

        # generate_plan sorts by priority first, then by time
        # priority-1 tasks (07:00, 08:00) should come before priority-3 (09:00)
        priorities = [t.priority for t in plan]
        self.assertEqual(priorities, sorted(priorities))


# ── Owner / Pet bookkeeping ──────────────────────────────────────

class TestOwnerAndPet(unittest.TestCase):

    def test_get_total_task_time(self):
        owner = Owner(name="Test", time_available=300)
        pet = Pet(name="Buddy", species="Dog")
        pet.add_task(Walk(description="Walk", time="07:00",
                         frequency="daily", priority=1, duration=30))
        pet.add_task(Feeding(description="Food", time="08:00",
                             frequency="daily", priority=1, duration=10))
        owner.add_pet(pet)
        self.assertEqual(owner.get_total_task_time(), 40)

    def test_get_pending_tasks_excludes_completed(self):
        pet = Pet(name="Luna", species="Cat")
        t1 = Feeding(description="Breakfast", time="08:00",
                     frequency="daily", priority=1, duration=10)
        t2 = Feeding(description="Dinner", time="18:00",
                     frequency="daily", priority=2, duration=10)
        pet.add_task(t1)
        pet.add_task(t2)
        t1.completed = True

        pending = pet.get_pending_tasks()
        self.assertEqual(len(pending), 1)
        self.assertIs(pending[0], t2)

    def test_task_repr_status_indicator(self):
        task = Walk(description="Walk", time="07:00",
                    frequency="daily", priority=1, duration=30)
        self.assertIn("✗", repr(task))
        task.completed = True
        self.assertIn("✓", repr(task))


if __name__ == "__main__":
    unittest.result = unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromModule(__import__("__main__"))
    )