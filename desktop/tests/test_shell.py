import unittest
from unittest.mock import patch

from toolbar.shell import run


class ShellTest(unittest.TestCase):
    def test_missing_runtime_explains_preparation_and_exits(self):
        with patch('toolbar.shell.runtime_available', return_value=False), \
                patch('toolbar.shell.show_error') as show:
            self.assertEqual(run(),1)
        self.assertIn('WebView2 Runtime',show.call_args.args[1])


if __name__ == '__main__':
    unittest.main()
