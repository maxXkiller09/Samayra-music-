import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "autoplay.py"


class AutoplayMatchingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        fake_mongo = types.ModuleType("ShrutiMusic.core.mongo")
        fake_mongo.mongodb = types.SimpleNamespace(autoplay=object())
        with patch.dict(sys.modules, {"ShrutiMusic.core.mongo": fake_mongo}):
            spec = importlib.util.spec_from_file_location(
                "autoplay_matching_under_test", MODULE_PATH
            )
            cls.module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(cls.module)

    def test_title_cleanup_removes_upload_noise(self):
        self.assertEqual(
            self.module._clean_title("Arijit Singh - Tum Hi Ho (Official Video)"),
            "Arijit Singh - Tum Hi Ho",
        )

    def test_mood_and_artist_match_ranks_above_unrelated_track(self):
        current = "Arijit Singh - Sad Heartbreak Song"
        similar = {
            "title": "Arijit Singh Bewafa Dard",
            "duration": "4:12",
        }
        unrelated = {
            "title": "DJ Party Dance Club",
            "duration": "3:35",
        }
        self.assertGreater(
            self.module._score_candidate(current, similar),
            self.module._score_candidate(current, unrelated),
        )

    def test_exact_same_title_is_rejected(self):
        title = "Arijit Singh - Tum Hi Ho"
        self.assertEqual(
            self.module._score_candidate(
                title, {"title": title, "duration": "4:12"}
            ),
            -100,
        )

    def test_duration_filter_rejects_mixes_and_invalid_values(self):
        self.assertTrue(self.module._is_short("4:32"))
        self.assertFalse(self.module._is_short("1:20:00"))
        self.assertFalse(self.module._is_short("10:01"))
        self.assertFalse(self.module._is_short("4:99"))
        self.assertFalse(self.module._is_short(None))


if __name__ == "__main__":
    unittest.main()
