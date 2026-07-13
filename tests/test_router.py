import json
import asyncio
import unittest

from zmlc import Route, Router, RoutingPolicy, Task


class RouterTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router()

    def test_arithmetic_is_deterministic(self) -> None:
        result = self.router.solve(Task(prompt="Calculate 17 + 25", task_type="math"))
        self.assertEqual(result.answer, "42")
        self.assertEqual(result.route, Route.DETERMINISTIC)

    def test_percent_is_deterministic(self) -> None:
        self.assertEqual(self.router.solve("What is 25% of 80?").answer, "20")

    def test_exact_json_preserves_literal(self) -> None:
        answer = self.router.solve(Task(prompt='Return JSON only: {"x": 1}', task_type="format_strict")).answer
        self.assertEqual(json.loads(answer), {"x": 1})

    def test_format_strict_string_transform_is_not_forced_to_json(self) -> None:
        result = self.router.solve(
            Task(prompt='Return uppercase for "Token Route".', task_type="format_strict")
        )
        self.assertEqual(result.answer, "TOKEN ROUTE")
        self.assertEqual(result.route, Route.DETERMINISTIC)

    def test_unknown_task_fails_without_provider(self) -> None:
        result = self.router.solve("Write an essay about routing")
        self.assertEqual(result.route, Route.FAILED)

    def test_plugin_policy_delegates_unknown_task_to_host(self) -> None:
        router = Router(policy=RoutingPolicy(delegate_to_host=True))
        result = router.solve("Write an essay about routing")
        self.assertEqual(result.route, Route.HOST_MODEL)
        self.assertEqual(result.trace[-1].status, "delegate")

    def test_batch_preserves_input_order(self) -> None:
        results = self.router.solve_batch(["Calculate 2+2", "Calculate 3+4"], max_workers=2)
        self.assertEqual([result.answer for result in results], ["4", "7"])

    def test_async_route(self) -> None:
        result = asyncio.run(self.router.solve_async("Calculate 5+6"))
        self.assertEqual(result.answer, "11")

    def test_minimum_savings_policy_can_bypass_middleware(self) -> None:
        router = Router(
            policy=RoutingPolicy(minimum_estimated_savings=10, delegate_to_host=True)
        )
        result = router.solve(
            Task(prompt="Calculate 2+2", metadata={"baseline_tokens": 3})
        )
        self.assertEqual(result.route, Route.HOST_MODEL)


if __name__ == "__main__":
    unittest.main()
