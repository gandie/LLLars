from __future__ import annotations

import unittest
from pathlib import Path

from lllars_core.markdown_boundaries import (
    evaluate_boundaries,
    format_violations,
    load_boundaries,
)


class MarkdownBoundaryTests(unittest.TestCase):
    def test_markdown_boundaries_are_respected(self) -> None:
        repo_root = Path(__file__).resolve().parent.parent
        config_path = repo_root / "docs" / "markdown_boundaries.json"

        config = load_boundaries(config_path)
        violations = evaluate_boundaries(repo_root, config)

        self.assertEqual(
            violations,
            [],
            msg=format_violations(violations),
        )


if __name__ == "__main__":
    unittest.main()
