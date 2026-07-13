import unittest

from zmlc.prompting import (
    PromptSpec,
    compact_host_prompt,
    compact_request,
    compile_prompt,
    estimate_tokens,
)


class PromptingTests(unittest.TestCase):
    def test_compiler_deduplicates_constraints(self) -> None:
        result = compile_prompt(
            PromptSpec(
                objective="Fix the parser.",
                constraints=("Keep API stable.", "Keep API stable."),
                verification=("Run parser tests.",),
            )
        )
        self.assertEqual(result.text.count("Keep API stable."), 1)
        self.assertIn("DONE WHEN", result.text)

    def test_compactor_preserves_code_fence(self) -> None:
        source = "Task\n\n```python\nx  =  1\n```"
        self.assertIn("x  =  1", compact_request(source))

    def test_estimate_is_stable(self) -> None:
        self.assertEqual(estimate_tokens(""), 0)
        self.assertGreater(estimate_tokens("one two three"), 0)

    def test_host_compactor_keeps_short_prompt(self) -> None:
        source = "Fix the parser."
        self.assertEqual(compact_host_prompt(source).text, source)

    def test_host_compactor_removes_material_transport_noise(self) -> None:
        source = ("Fix parser.    \n\n" * 20).strip()
        result = compact_host_prompt(source, minimum_savings=1)
        self.assertLess(result.estimated_tokens, result.source_tokens)


if __name__ == "__main__":
    unittest.main()
