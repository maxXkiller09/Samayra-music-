import asyncio
import importlib.util
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "platforms" / "Youtube.py"
SPEC = importlib.util.spec_from_file_location("youtube_download_lock_under_test", MODULE_PATH)
YOUTUBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(YOUTUBE)


class ConcurrentDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_same_track_downloads_are_serialized(self):
        active = 0
        maximum_active = 0
        original = YOUTUBE._api_download_unlocked

        async def fake_download(*args, **kwargs):
            nonlocal active, maximum_active
            active += 1
            maximum_active = max(maximum_active, active)
            await asyncio.sleep(0.02)
            active -= 1
            return "downloads/dQw4w9WgXcQ.mp3"

        YOUTUBE._api_download_unlocked = fake_download
        try:
            results = await asyncio.gather(
                YOUTUBE._api_download(
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio", "mp3", 10
                ),
                YOUTUBE._api_download(
                    "https://www.youtube.com/watch?v=dQw4w9WgXcQ", "audio", "mp3", 10
                ),
            )
        finally:
            YOUTUBE._api_download_unlocked = original

        self.assertEqual(results, [
            "downloads/dQw4w9WgXcQ.mp3",
            "downloads/dQw4w9WgXcQ.mp3",
        ])
        self.assertEqual(maximum_active, 1)

    async def test_invalid_id_does_not_start_download(self):
        async def unexpected_download(*args, **kwargs):
            self.fail("invalid IDs must not start a download")

        original = YOUTUBE._api_download_unlocked
        YOUTUBE._api_download_unlocked = unexpected_download
        try:
            result = await YOUTUBE._api_download("not-a-video-url", "audio", "mp3", 10)
        finally:
            YOUTUBE._api_download_unlocked = original
        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
