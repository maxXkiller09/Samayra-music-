import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "stream" / "speed_filters.py"
SPEC = importlib.util.spec_from_file_location("speed_filters_under_test", MODULE_PATH)
SPEED_FILTERS = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SPEED_FILTERS)
build_ffmpeg_speed_args = SPEED_FILTERS.build_ffmpeg_speed_args


class PlaybackSpeedFilterTests(unittest.TestCase):
    def test_audio_conversion_does_not_apply_video_filter(self):
        args = build_ffmpeg_speed_args("song.mp3", "song-fast.mp3", "1.5", False)
        self.assertIn("-filter:a", args)
        self.assertIn("atempo=1.5", args)
        self.assertNotIn("-filter:v", args)
        self.assertEqual(args[-1], "song-fast.mp3")

    def test_video_conversion_applies_video_and_audio_filters(self):
        args = build_ffmpeg_speed_args("clip.mp4", "clip-fast.mp4", "2.0", True)
        self.assertIn("-filter:v", args)
        self.assertIn("setpts=0.5*PTS", args)
        self.assertIn("-filter:a", args)
        self.assertIn("atempo=2.0", args)

    def test_shell_metacharacters_remain_plain_arguments(self):
        path = "downloads/track;touch-not-run.mp3"
        args = build_ffmpeg_speed_args(path, "out.mp3", "0.5", False)
        self.assertEqual(args[args.index("-i") + 1], path)
        self.assertNotIsInstance(args, str)

    def test_rejects_unsupported_speed(self):
        with self.assertRaises(ValueError):
            build_ffmpeg_speed_args("song.mp3", "out.mp3", "8.0", False)


if __name__ == "__main__":
    unittest.main()
