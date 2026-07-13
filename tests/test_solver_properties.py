import random
import unittest
from datetime import date, timedelta

from zmlc import Route, Router, Task


class SolverPropertyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router()

    def test_generated_arithmetic_pairs(self) -> None:
        randomizer = random.Random(20260713)
        for index in range(200):
            left = randomizer.randint(-10_000, 10_000)
            right = randomizer.randint(-10_000, 10_000)
            with self.subTest(index=index, left=left, right=right):
                result = self.router.solve(
                    Task(prompt=f"Calculate {left} + {right}.", task_type="math")
                )
                self.assertEqual(result.route, Route.DETERMINISTIC)
                self.assertEqual(result.answer, str(left + right))

    def test_generated_unit_conversions(self) -> None:
        for value in range(1, 101):
            with self.subTest(value=value):
                result = self.router.solve(
                    Task(prompt=f"Convert {value} km to m.", task_type="math")
                )
                self.assertEqual(result.route, Route.DETERMINISTIC)
                self.assertEqual(result.answer, str(value * 1000))

    def test_generated_date_differences(self) -> None:
        start = date(2025, 1, 1)
        for days in range(1, 121):
            end = start + timedelta(days=days)
            with self.subTest(days=days):
                result = self.router.solve(
                    Task(
                        prompt=f"How many days between {start} and {end}?",
                        task_type="math",
                    )
                )
                self.assertEqual(result.route, Route.DETERMINISTIC)
                self.assertEqual(result.answer, str(days))

    def test_ambiguous_or_unsafe_inputs_abstain(self) -> None:
        prompts = (
            "Calculate the best architecture for this company.",
            "Convert 10 kg to meters.",
            "What is 10 / 0?",
            "What is the percentage change from 0 to 100?",
            "Return the union concept in philosophy.",
            "How many days between sometime next week and Friday?",
        )
        for prompt in prompts:
            with self.subTest(prompt=prompt):
                result = self.router.solve(Task(prompt=prompt))
                self.assertNotEqual(result.route, Route.DETERMINISTIC)


if __name__ == "__main__":
    unittest.main()
