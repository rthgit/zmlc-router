import json
import unittest

from zmlc import Route, Router, RoutingPolicy, Task
from zmlc.models import SolverResult
from zmlc.verifiers import verify_solver_result


class AdvancedSolverTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router(
            policy=RoutingPolicy(
                delegate_to_host=True,
                allow_local_model=False,
                allow_remote_model=False,
            )
        )

    def test_unit_conversion(self) -> None:
        result = self.router.solve("Convert 2.5 km to m")
        self.assertEqual(result.answer, "2500")
        self.assertEqual(result.solver, "unit_conversion")

    def test_incompatible_units_abstain(self) -> None:
        result = self.router.solve("Convert 2 kg to m")
        self.assertEqual(result.route, Route.HOST_MODEL)

    def test_simple_interest(self) -> None:
        result = self.router.solve("Calculate simple interest on principal 1000 at 5% for 3 years")
        self.assertEqual(result.answer, "150")

    def test_percentage_change(self) -> None:
        result = self.router.solve("Calculate the percentage change from 80 to 100")
        self.assertEqual(result.answer, "25")

    def test_set_intersection(self) -> None:
        result = self.router.solve("Return the intersection of [1,2,3] and [2,3,4] as JSON")
        self.assertEqual(json.loads(result.answer), [2, 3])

    def test_iso_date_difference_beats_arithmetic(self) -> None:
        result = self.router.solve("How many days between 2026-01-01 and 2026-01-11?")
        self.assertEqual(result.answer, "10")
        self.assertEqual(result.solver, "date_difference")

    def test_subjective_question_delegates(self) -> None:
        result = self.router.solve("What is the best programming language?")
        self.assertEqual(result.route, Route.HOST_MODEL)

    def test_forged_evidence_is_rejected(self) -> None:
        forged = SolverResult(
            answer="43",
            solver="arithmetic",
            confidence=1.0,
            evidence={"operation": "expression", "expression": "17+25"},
        )
        self.assertFalse(verify_solver_result(Task(prompt="Calculate 17+25"), forged))


if __name__ == "__main__":
    unittest.main()
