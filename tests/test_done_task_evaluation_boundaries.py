from __future__ import annotations

import unittest
from pathlib import Path

from boundary_checks.done_task_evaluation_boundaries import (
    evaluate_boundaries,
    format_violations,
    load_boundaries,
)


class DoneTaskEvaluationBoundaryTests(unittest.TestCase):
    def test_done_task_evaluation_boundaries_are_respected(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        config_path = (
            repo_root
            / "tests"
            / "boundary_checks"
            / "done_task_evaluation_boundaries.json"
        )

        config = load_boundaries(config_path)
        self.assertIn("docs/workflow/done/T*.md", config.get("include", []))

        violations = evaluate_boundaries(repo_root, config)
        self.assertEqual(violations, [], msg=format_violations(violations))


if __name__ == "__main__":
    unittest.main()
