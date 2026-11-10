import subprocess
import sys
import unittest
from pathlib import Path

from toolbar.launcher import tool_command


class DispatchTest(unittest.TestCase):
    def test_unknown_identifier_is_rejected(self):
        with self.assertRaises(ValueError):
            tool_command("other.exe")
        result = subprocess.run([sys.executable, "main.py", "--tool", "invalid"],
                                cwd=Path(__file__).resolve().parents[1], capture_output=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn(b"desconhecida", result.stderr)

    def test_commands_use_interpreter_and_fixed_entry(self):
        command = tool_command("preparafrota")
        self.assertEqual(Path(command[0]).resolve(), Path(sys.executable).resolve())
        self.assertEqual(Path(command[1]).name, "main.py")
        self.assertEqual(command[2:], ["--tool", "preparafrota"])


if __name__ == "__main__":
    unittest.main()
