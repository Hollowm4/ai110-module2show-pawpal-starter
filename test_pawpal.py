import unittest
from pawpal_system import Pet, Walk


class TestTaskCompletion(unittest.TestCase):
    def test_mark_complete_changes_status(self):
        pet = Pet(name="Buddy", species="Dog")
        task = Walk(description="Morning walk", time="07:00 AM",
                    frequency="daily", priority=1, duration=30)
        pet.add_task(task)

        self.assertFalse(task.completed)   # should be incomplete before
        task.mark_complete()
        self.assertTrue(task.completed)    # should be complete after


class TestTaskAddition(unittest.TestCase):
    def test_add_task_increases_count(self):
        pet = Pet(name="Luna", species="Cat")

        self.assertEqual(len(pet.get_tasks()), 0)   # starts with no tasks
        pet.add_task(Walk(description="Evening walk", time="06:00 PM",
                          frequency="daily", priority=1, duration=20))
        self.assertEqual(len(pet.get_tasks()), 1)   # should now have 1 task


if __name__ == "__main__":
    unittest.result = unittest.TextTestRunner(verbosity=2).run(
        unittest.TestLoader().loadTestsFromModule(__import__("__main__"))
    )