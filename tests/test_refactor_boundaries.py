from __future__ import annotations

import unittest
from pathlib import Path

from boundary_checks.refactor_boundaries import (
    evaluate_boundaries,
    format_violations,
    load_boundaries,
)


class RefactorBoundaryTests(unittest.TestCase):
    def test_refactor_boundaries_are_respected(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        config_path = (
            repo_root
            / "tests"
            / "boundary_checks"
            / "refactor_boundaries.json"
        )

        config = load_boundaries(config_path)
        self.assertIn(
            "tests/*.py",
            config.get("include", []),
            msg="Refactor boundaries must include test files in scope.",
        )

        violations = evaluate_boundaries(repo_root, config)

        self.assertEqual(
            violations,
            [],
            msg=format_violations(violations),
        )


if __name__ == "__main__":
    unittest.main()
