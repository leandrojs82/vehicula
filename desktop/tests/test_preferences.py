import json
import tempfile
import unittest
from pathlib import Path

from toolbar.preferences import load_preferences, save_preferences


class PreferencesTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.path = Path(temp.name) / "settings.json"

    def test_missing_and_corrupt_files_recover_defaults(self):
        self.assertEqual(load_preferences(self.path)["theme"], "system")
        self.path.write_text("{broken", encoding="utf-8")
        self.assertEqual(load_preferences(self.path)["favorites"], [])

    def test_persists_only_valid_preferences(self):
        save_preferences(self.path, {"theme": "light", "favorites": ["sqlait", "invalid", "sqlait"],
                                     "on_top": True, "rows": ["private data"], "x": 122, "y": 43})
        saved = load_preferences(self.path)
        self.assertEqual(saved["theme"], "light")
        self.assertEqual(saved["favorites"], ["sqlait"])
        self.assertTrue(saved["on_top"])
        self.assertEqual((saved["x"], saved["y"]), (122, 43))
        self.assertNotIn("rows", json.loads(self.path.read_text(encoding="utf-8")))
        self.assertEqual(list(self.path.parent.iterdir()), [self.path])

    def test_bad_types_do_not_enable_settings(self):
        save_preferences(self.path, {"theme": "bad", "favorites": "sqlait", "on_top": "false",
                                     "x": True, "y": "9", "expanded_width": -1})
        saved = load_preferences(self.path)
        self.assertEqual(saved["theme"], "system")
        self.assertEqual(saved["favorites"], [])
        self.assertFalse(saved["on_top"])
        self.assertIsNone(saved["x"])
        self.assertEqual(saved["expanded_width"], 1120)


if __name__ == "__main__":
    unittest.main()
