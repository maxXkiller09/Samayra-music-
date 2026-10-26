import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "stream" / "queue_files.py"
SPEC = importlib.util.spec_from_file_location("queue_files_under_test", MODULE_PATH)
QUEUE_FILES = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(QUEUE_FILES)


class QueueFileReplacementTests(unittest.TestCase):
    def test_replaces_placeholder_and_cleanup_reference(self):
        queue = [{"file": "vid_dQw4w9WgXcQ", "title": "Track"}]
        tracked = ["vid_dQw4w9WgXcQ", "vid_dQw4w9WgXcQ"]

        result = QUEUE_FILES.replace_tracked_file(
            queue, tracked, "vid_dQw4w9WgXcQ", "downloads/dQw4w9WgXcQ.mp3"
        )

        self.assertTrue(result)
        self.assertEqual(queue[0]["file"], "downloads/dQw4w9WgXcQ.mp3")
        self.assertEqual(
            tracked,
            ["vid_dQw4w9WgXcQ", "downloads/dQw4w9WgXcQ.mp3"],
        )

    def test_does_not_change_a_different_queue_head(self):
        queue = [{"file": "downloads/current.mp3"}]
        tracked = ["vid_expected"]

        result = QUEUE_FILES.replace_tracked_file(
            queue, tracked, "vid_expected", "downloads/new.mp3"
        )

        self.assertFalse(result)
        self.assertEqual(queue[0]["file"], "downloads/current.mp3")
        self.assertEqual(tracked, ["vid_expected"])

    def test_rejects_empty_download_path(self):
        queue = [{"file": "vid_expected"}]
        tracked = ["vid_expected"]

        result = QUEUE_FILES.replace_tracked_file(
            queue, tracked, "vid_expected", None
        )

        self.assertFalse(result)
        self.assertEqual(queue[0]["file"], "vid_expected")
        self.assertEqual(tracked, ["vid_expected"])


if __name__ == "__main__":
    unittest.main()
