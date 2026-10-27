import asyncio
import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "platforms" / "Youtube.py"


class FakeContent:
    def __init__(self, chunks):
        self.chunks = chunks

    async def iter_chunked(self, _size):
        for chunk in self.chunks:
            # Yield control just as a network stream does between chunks.
            await asyncio.sleep(0)
            yield chunk


class FakeResponse:
    def __init__(self, chunks, headers=None):
        self.content = FakeContent(chunks)
        self.headers = headers or {}


class AsyncDownloadIOTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "youtube_download_io_under_test", MODULE_PATH
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    async def test_save_stream_writes_complete_file_and_removes_partial_name(self):
        payload = [b"first chunk", b"second chunk", b"third chunk"]
        with tempfile.TemporaryDirectory() as directory:
            destination = str(Path(directory) / "track.mp3")
            response = FakeResponse(payload)

            saved = await self.module._save_stream(
                response, destination, max_bytes=1024
            )

            self.assertTrue(saved)
            self.assertEqual(Path(destination).read_bytes(), b"".join(payload))
            self.assertFalse(Path(destination + ".part").exists())

    async def test_save_stream_rejects_size_over_limit_and_cleans_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = str(Path(directory) / "track.mp3")
            response = FakeResponse([b"1234", b"5678"])

            saved = await self.module._save_stream(
                response, destination, max_bytes=5
            )

            self.assertFalse(saved)
            self.assertFalse(Path(destination).exists())
            self.assertFalse(Path(destination + ".part").exists())


if __name__ == "__main__":
    unittest.main()
