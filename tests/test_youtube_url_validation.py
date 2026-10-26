"""Regression tests for YouTube input and downloader URL validation.

Load the module by file path to avoid importing the bot's side-effectful package
initializer (which starts configuring clients and databases).
"""
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "platforms" / "Youtube.py"
SPEC = importlib.util.spec_from_file_location("youtube_validation_under_test", MODULE_PATH)
YOUTUBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(YOUTUBE)


class YouTubeIdValidationTests(unittest.TestCase):
    def test_accepts_plain_video_id(self):
        self.assertEqual(YOUTUBE._extract_video_id("dQw4w9WgXcQ"), "dQw4w9WgXcQ")

    def test_accepts_watch_url(self):
        self.assertEqual(
            YOUTUBE._extract_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_accepts_short_url(self):
        self.assertEqual(
            YOUTUBE._extract_video_id("https://youtu.be/dQw4w9WgXcQ"),
            "dQw4w9WgXcQ",
        )

    def test_accepts_shorts_url_with_query(self):
        self.assertEqual(
            YOUTUBE._extract_video_id("https://youtube.com/shorts/dQw4w9WgXcQ?feature=share"),
            "dQw4w9WgXcQ",
        )

    def test_rejects_arbitrary_host(self):
        self.assertEqual(
            YOUTUBE._extract_video_id("https://example.com/watch?v=dQw4w9WgXcQ"),
            "",
        )

    def test_rejects_malformed_video_id(self):
        self.assertEqual(
            YOUTUBE._extract_video_id("https://youtu.be/not-a-valid-id"),
            "",
        )

    def test_rejects_empty_input(self):
        self.assertEqual(YOUTUBE._extract_video_id(""), "")


class DownloadUrlSafetyTests(unittest.TestCase):
    def test_accepts_public_https_url(self):
        self.assertTrue(YOUTUBE._safe_public_download_url("https://example.com/file.mp3"))

    def test_rejects_non_http_scheme(self):
        self.assertFalse(YOUTUBE._safe_public_download_url("file:///etc/passwd"))

    def test_rejects_urls_with_embedded_credentials(self):
        self.assertFalse(
            YOUTUBE._safe_public_download_url("https://user:secret@example.com/file.mp3")
        )

    def test_rejects_localhost(self):
        self.assertFalse(YOUTUBE._safe_public_download_url("http://localhost/file"))

    def test_rejects_loopback_ip(self):
        self.assertFalse(YOUTUBE._safe_public_download_url("http://127.0.0.1/file"))

    def test_rejects_private_ipv6(self):
        self.assertFalse(YOUTUBE._safe_public_download_url("http://[::1]/file"))


class RepositoryImportSafetyTests(unittest.TestCase):
    def test_standard_queue_module_is_not_shadowed(self):
        import queue

        self.assertTrue(hasattr(queue, "SimpleQueue"))
        self.assertFalse((ROOT / "queue.py").exists())


if __name__ == "__main__":
    unittest.main()
