import importlib.util
from pathlib import Path
import sys
import tempfile
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "stream" / "autoclear.py"


class PlaybackFileCleanupTests(unittest.TestCase):
    def load_cleanup_module(self, tracked_files):
        fake_config = types.ModuleType("config")
        fake_config.autoclean = tracked_files
        spec = importlib.util.spec_from_file_location(
            "autoclear_under_test", MODULE_PATH
        )
        module = importlib.util.module_from_spec(spec)
        with patch.dict(sys.modules, {"config": fake_config}):
            spec.loader.exec_module(module)
        return module

    def test_shared_speed_file_is_removed_only_after_last_reference(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "speed.mp3")
            Path(path).write_bytes(b"audio")
            tracked = [path, path]
            cleanup = self.load_cleanup_module(tracked)

            cleanup.release_file(path)
            self.assertTrue(Path(path).exists())
            self.assertEqual(tracked, [path])

            cleanup.release_file(path)
            self.assertFalse(Path(path).exists())
            self.assertEqual(tracked, [])

    def test_placeholder_names_are_never_removed_as_files(self):
        tracked = ["vid_example"]
        cleanup = self.load_cleanup_module(tracked)

        cleanup.release_file("vid_example")

        self.assertEqual(tracked, [])
        self.assertFalse(Path("vid_example").exists())

    def test_auto_clean_releases_original_and_speed_path(self):
        with tempfile.TemporaryDirectory() as directory:
            original = str(Path(directory) / "original.mp3")
            speed = str(Path(directory) / "speed.mp3")
            Path(original).write_bytes(b"original")
            Path(speed).write_bytes(b"speed")
            tracked = [original, speed]
            cleanup = self.load_cleanup_module(tracked)

            import asyncio
            asyncio.run(cleanup.auto_clean({"file": original, "speed_path": speed}))

            self.assertFalse(Path(original).exists())
            self.assertFalse(Path(speed).exists())
            self.assertEqual(tracked, [])


if __name__ == "__main__":
    unittest.main()
