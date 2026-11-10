import subprocess
import sys
import unittest
from unittest.mock import patch

from toolbar.launcher import ToolLauncher


class LauncherTest(unittest.TestCase):
    def test_repeated_click_reuses_owned_process_and_exit_allows_retry(self):
        children = []

        launcher = ToolLauncher()
        try:
            original = subprocess.Popen
            def real_child(_command, **_kwargs):
                process = original([sys.executable, "-c", "import time; time.sleep(20)"])
                children.append(process)
                return process
            with patch("toolbar.launcher.subprocess.Popen", side_effect=real_child), \
                    patch("toolbar.launcher.focus_process", return_value=False):
                self.assertEqual(launcher.open("pbix")["status"], "opening")
                self.assertEqual(launcher.open("pbix")["status"], "opening")
                self.assertEqual(len(children), 1)
                children[0].terminate()
                children[0].wait(timeout=5)
                self.assertEqual(launcher.open("pbix")["status"], "opening")
                self.assertEqual(len(children), 2)
        finally:
            for process in children:
                if process.poll() is None:
                    process.terminate()
                    process.wait(timeout=5)

    def test_invalid_tool_returns_actionable_error(self):
        result = ToolLauncher().open("unknown")
        self.assertEqual(result["status"], "error")
        self.assertIn("desconhecida", result["message"])


if __name__ == "__main__":
    unittest.main()
