import asyncio
import importlib.util
from pathlib import Path
import sys
import time
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

    def test_search_cache_is_bounded_and_expires(self):
        module = self.module
        module._search_cache.clear()
        module._search_cache["old"] = (time.monotonic() - 1, [{"id": "x", "title": "x", "duration": "3:00"}])
        with patch.object(module, "_fetch_search_results", return_value=None):
            # Expired cache entry is discarded before a fresh search is attempted.
            self.assertNotIn("old", module._search_cache)
        module._search_cache.clear()
        module._SEARCH_CACHE_MAX = 2
        try:
            for key in ("a", "b", "c"):
                module._search_cache[key] = (time.monotonic() + 30, [])
                while len(module._search_cache) > module._SEARCH_CACHE_MAX:
                    module._search_cache.popitem(last=False)
            self.assertEqual(list(module._search_cache), ["b", "c"])
        finally:
            module._SEARCH_CACHE_MAX = 64
            module._search_cache.clear()

    def test_recent_history_is_bounded_by_chat_count(self):
        module = self.module
        module._recent.clear()
        module._RECENT_CHAT_MAX = 2
        try:
            module._recent_for(1)
            module._recent_for(2)
            module._recent_for(3)
            self.assertEqual(list(module._recent), [2, 3])
        finally:
            module._RECENT_CHAT_MAX = 256
            module._recent.clear()

    def test_title_cleanup_removes_upload_noise(self):
        self.assertEqual(
            self.module._clean_title("Arijit Singh - Tum Hi Ho (Official Video)"),
            "Arijit Singh - Tum Hi Ho",
        )

    def test_search_query_adds_mood_hint_when_detectable(self):
        query = self.module._search_query("Arijit Singh - Sad Heartbreak Song")
        self.assertIn("similar vibe", query)
        self.assertIn("sad heartbreak songs", query)

    def test_search_query_keeps_neutral_titles_neutral(self):
        query = self.module._search_query("Arijit Singh - Tum Hi Ho")
        self.assertEqual(query, "songs like Arijit Singh - Tum Hi Ho similar vibe")

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
        self.assertLess(self.module._score_candidate(current, unrelated), 1)

    def test_unrelated_neutral_track_does_not_pass_relevance_cutoff(self):
        current = "Arijit Singh - Tum Hi Ho"
        unrelated = {
            "title": "Heavy Metal Workout Mix",
            "duration": "3:35",
        }
        self.assertLess(self.module._score_candidate(current, unrelated), 1)

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

    def test_proactive_autoplay_reschedules_when_sole_track_changes(self):
        old_track = {"title": "Old song"}
        new_track = {"title": "New song"}
        fake_misc = types.ModuleType("ShrutiMusic.misc")
        fake_misc.db = {-1001: [new_track]}
        with patch.dict(sys.modules, {"ShrutiMusic.misc": fake_misc}):
            with patch.dict(self.module.AUTOPLAY, {-1001: True}):
                with patch.object(self.module, "schedule_autoplay_fill") as schedule:
                    self.module._reschedule_if_track_changed(-1001, old_track, None)
        schedule.assert_called_once_with(-1001, new_track)

    def test_proactive_autoplay_does_not_reschedule_same_track(self):
        current_track = {"title": "Same song"}
        fake_misc = types.ModuleType("ShrutiMusic.misc")
        fake_misc.db = {-1002: [current_track]}
        with patch.dict(sys.modules, {"ShrutiMusic.misc": fake_misc}):
            with patch.dict(self.module.AUTOPLAY, {-1002: True}):
                with patch.object(self.module, "schedule_autoplay_fill") as schedule:
                    self.module._reschedule_if_track_changed(-1002, current_track, None)
        schedule.assert_not_called()


class AutoplayDisableTests(unittest.IsolatedAsyncioTestCase):
    async def test_disabling_autoplay_cancels_inflight_search(self):
        if not hasattr(AutoplayMatchingTests, "module"):
            AutoplayMatchingTests.setUpClass()
        module = AutoplayMatchingTests.module

        class FakeAutoplayDB:
            async def update_one(self, *args, **kwargs):
                return None

        module.autoplay_db = FakeAutoplayDB()
        chat_id = -4242
        task = asyncio.create_task(asyncio.sleep(60))
        module._fill_tasks[chat_id] = task
        module.AUTOPLAY[chat_id] = True

        await module.set_autoplay(chat_id, False)
        await asyncio.sleep(0)

        self.assertTrue(task.cancelled())
        self.assertNotIn(chat_id, module._fill_tasks)
        self.assertFalse(module.AUTOPLAY[chat_id])


if __name__ == "__main__":
    unittest.main()
