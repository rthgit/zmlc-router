import json
import unittest

from zmlc.mcp_server import _call_tool
from zmlc.policy import RoutingPolicy
from zmlc.router import Router
from zmlc.telemetry import MemoryTelemetry


class McpContractTests(unittest.TestCase):
    def setUp(self) -> None:
        self.router = Router(
            policy=RoutingPolicy(
                delegate_to_host=True,
                allow_local_model=False,
                allow_remote_model=False,
            ),
            telemetry=MemoryTelemetry(),
        )

    def test_default_route_payload_is_compact(self) -> None:
        payload = json.loads(
            _call_tool(self.router, "route_task", {"prompt": "Write an essay"})
        )
        self.assertEqual(payload["action"], "delegate_to_codex")
        self.assertNotIn("trace", payload)
        self.assertNotIn("codex_prompt", payload)

    def test_audit_payload_contains_trace(self) -> None:
        payload = json.loads(
            _call_tool(self.router, "audit_task", {"prompt": "Calculate 2+2"})
        )
        self.assertEqual(payload["answer"], "4")
        self.assertTrue(payload["trace"])

    def test_session_metrics_do_not_contain_prompts(self) -> None:
        _call_tool(self.router, "route_task", {"prompt": "Calculate 2+2"})
        payload = json.loads(_call_tool(self.router, "session_metrics", {}))
        self.assertEqual(payload["task_count"], 1)
        self.assertGreater(payload["estimated_tokens_saved"], 0)
        self.assertNotIn("prompt", json.dumps(payload).lower())


if __name__ == "__main__":
    unittest.main()
