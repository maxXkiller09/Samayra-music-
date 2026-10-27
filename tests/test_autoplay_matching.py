import asyncio
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

    def test_search_query_adds_mood_hint_when_detectable(self):
        query = self.module._search_query("Arijit Singh - Sad Heartbreak Song")
        self.assertIn("similar vibe", query)
        self.assertIn("sad heartbreak songs", query)

    def test_search_query_keeps_neutral_titles_neutral(self):
        query = self.module._search_query("Arijit Singh - Tum Hi Ho")
        self.assertEqual(query, "songs like Arijit Singh - Tum Hi Ho similar vibe")

    def test_search_queries_use_multiple_discovery_strategies(self):
        queries = self.module._search_queries("Arijit Singh - Romantic Hindi Song")
        self.assertGreaterEqual(len(queries), 2)
        self.assertTrue(any("romantic" in query.lower() for query in queries))
        self.assertTrue(any("artists similar to" in query.lower() for query in queries))

    def test_canonical_identity_ignores_upload_labels_and_punctuation(self):
        current = "Arijit Singh - Tum Hi Ho"
        alternate_upload = "Tum Hi Ho (Official Video) - Arijit Singh"
        self.assertEqual(
            self.module._canonical_identity(current, self.module._artist_hint(current)),
            self.module._canonical_identity(alternate_upload, self.module._artist_hint(alternate_upload)),
        )

    def test_alternate_versions_are_rejected(self):
        for title in (
            "Tum Hi Ho Remix",
            "Tum Hi Ho (Slowed + Reverb)",
            "Tum Hi Ho Sped Up",
            "Tum Hi Ho Live",
        ):
            self.assertTrue(self.module._is_alternate_version(title), title)

    def test_duplicate_filter_rejects_current_track_and_versions(self):
        current = "Arijit Singh - Tum Hi Ho"
        self.assertTrue(
            self.module._candidate_is_duplicate(
                current,
                {"title": "Tum Hi Ho (Official Audio) - Arijit Singh"},
                set(),
                set(),
            )
        )
        self.assertTrue(
            self.module._candidate_is_duplicate(
                current, {"title": "Tum Hi Ho Remix"}, set(), set()
            )
        )

    def test_duplicate_filter_respects_queue_and_recent_history(self):
        current = "Arijit Singh - Tum Hi Ho"
        queued = self.module._canonical_identity("Kesariya - Arijit Singh")
        recent = self.module._canonical_identity("Channa Mereya - Arijit Singh")
        self.assertTrue(
            self.module._candidate_is_duplicate(
                current, {"title": "Kesariya - Arijit Singh"}, {queued}, set()
            )
        )
        self.assertTrue(
            self.module._candidate_is_duplicate(
                current, {"title": "Channa Mereya - Arijit Singh"}, set(), {recent}
            )
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
