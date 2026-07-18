from __future__ import annotations

import sys
import unittest
from unittest.mock import patch

from runtime_api_smoke_test import main


class RuntimeApiSmokeCliRegressionTests(unittest.TestCase):
    def test_main_normalizes_expected_shells(self) -> None:
        with (
            patch.object(
                sys,
                "argv",
                [
                    "runtime_api_smoke_test.py",
                    "--expected-shells",
                    " bash, SH , pwsh ",
                ],
            ),
            patch(
                "runtime_api_smoke_test.run_smoke_test",
                return_value=0,
            ) as run_smoke,
        ):
            with self.assertRaises(SystemExit) as exit_ctx:
                main()

        self.assertEqual(exit_ctx.exception.code, 0)
        self.assertEqual(
            run_smoke.call_args.kwargs["expected_shells"],
            ("bash", "sh", "pwsh"),
        )

    def test_main_rejects_empty_expected_shells(self) -> None:
        with patch.object(
            sys,
            "argv",
            [
                "runtime_api_smoke_test.py",
                "--expected-shells",
                " , , ",
            ],
        ):
            with self.assertRaisesRegex(
                SystemExit,
                "--expected-shells must include at least one shell",
            ):
                main()


if __name__ == "__main__":
    unittest.main()
