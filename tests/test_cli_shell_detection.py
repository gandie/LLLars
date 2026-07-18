from __future__ import annotations

import unittest
from unittest.mock import patch

from lllars_core.shell import detect_shell


class CliShellDetectionTests(unittest.TestCase):
    def test_shell_auto_detection_prefers_powershell_when_pwsh_missing(
        self,
    ) -> None:
        which_table = {
            "pwsh": None,
            "powershell": (
                "C:/Windows/System32/WindowsPowerShell/v1.0/" "powershell.exe"
            ),
            "cmd": "C:/Windows/System32/cmd.exe",
        }
        with (
            patch("lllars_core.shell.platform.system", return_value="Windows"),
            patch(
                "lllars_core.shell.shutil.which",
                side_effect=lambda name: which_table.get(name),
            ),
        ):
            selection = detect_shell(shell_mode="auto", shell_override=None)
        self.assertIsNotNone(selection)
        self.assertEqual(selection.name, "powershell")

    def test_shell_override_is_honored_when_available(self) -> None:
        with (
            patch("lllars_core.shell.platform.system", return_value="Windows"),
            patch(
                "lllars_core.shell.shutil.which",
                side_effect=lambda name: (
                    "C:/Windows/System32/cmd.exe" if name == "cmd" else None
                ),
            ),
        ):
            selection = detect_shell(
                shell_mode="override", shell_override="cmd"
            )
        self.assertIsNotNone(selection)
        self.assertEqual(selection.name, "cmd")

    def test_shell_override_is_used_when_mode_is_auto(self) -> None:
        table = {
            "pwsh": "C:/Program Files/PowerShell/7/pwsh.exe",
            "powershell": (
                "C:/Windows/System32/WindowsPowerShell/v1.0/" "powershell.exe"
            ),
            "cmd": "C:/Windows/System32/cmd.exe",
        }
        with (
            patch("lllars_core.shell.platform.system", return_value="Windows"),
            patch(
                "lllars_core.shell.shutil.which",
                side_effect=lambda name: table.get(name),
            ),
        ):
            selection = detect_shell(shell_mode="auto", shell_override="cmd")
        self.assertIsNotNone(selection)
        self.assertEqual(selection.name, "cmd")


if __name__ == "__main__":
    unittest.main()
