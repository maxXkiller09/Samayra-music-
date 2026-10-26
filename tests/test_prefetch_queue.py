import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "stream" / "queue_files.py"


spec = importlib.util.spec_from_file_location("queue_files_prefetch_test", MODULE_PATH)
queue_files = importlib.util.module_from_spec(spec)
spec.loader.exec_module(queue_files)


class PrefetchQueueReplacementTests(unittest.TestCase):
    def test_prefetched_file_replaces_only_the_same_live_queue_item(self):
        item = {"file": "vid_abc", "vidid": "abc"}
        queue = [{"file": "current.mp3"}, item]
        tracked = ["current.mp3", "vid_abc"]

        changed = queue_files.replace_tracked_queue_item(
            queue, tracked, item, "vid_abc", "/cache/abc.mp3"
        )

        self.assertTrue(changed)
        self.assertEqual(item["file"], "/cache/abc.mp3")
        self.assertEqual(tracked, ["current.mp3", "/cache/abc.mp3"])

    def test_removed_queue_item_is_not_resurrected_by_late_prefetch(self):
        item = {"file": "vid_abc", "vidid": "abc"}
        queue = [{"file": "current.mp3"}]
        tracked = ["current.mp3", "vid_abc"]

        changed = queue_files.replace_tracked_queue_item(
            queue, tracked, item, "vid_abc", "/cache/abc.mp3"
        )

        self.assertFalse(changed)
        self.assertEqual(item["file"], "vid_abc")
        self.assertEqual(tracked, ["current.mp3", "vid_abc"])

    def test_stale_placeholder_does_not_replace_item_after_skip(self):
        item = {"file": "vid_new", "vidid": "new"}
        queue = [item]
        tracked = ["vid_new"]

        changed = queue_files.replace_tracked_queue_item(
            queue, tracked, item, "vid_old", "/cache/old.mp3"
        )

        self.assertFalse(changed)
        self.assertEqual(item["file"], "vid_new")
        self.assertEqual(tracked, ["vid_new"])


if __name__ == "__main__":
    unittest.main()
