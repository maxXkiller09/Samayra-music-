import importlib.util
from pathlib import Path
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "platforms" / "Youtube.py"
SPEC = importlib.util.spec_from_file_location("youtube_atomic_download_under_test", MODULE_PATH)
YOUTUBE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(YOUTUBE)


class FakeContent:
    def __init__(self, chunks):
        self.chunks = chunks

    async def iter_chunked(self, _size):
        for chunk in self.chunks:
            yield chunk


class FakeResponse:
    def __init__(self, chunks, content_length=None):
        self.headers = {}
        if content_length is not None:
            self.headers["Content-Length"] = str(content_length)
        self.content = FakeContent(chunks)


class AtomicDownloadTests(unittest.IsolatedAsyncioTestCase):
    async def test_complete_download_is_published_atomically(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "track.mp3")
            with open(path, "wb") as handle:
                handle.write(b"old-cache")
            response = FakeResponse([b"new-", b"audio"], content_length=9)

            result = await YOUTUBE._save_stream(response, path, 20)

            self.assertTrue(result)
            self.assertEqual(Path(path).read_bytes(), b"new-audio")
            self.assertFalse(Path(path + ".part").exists())

    async def test_oversized_content_length_preserves_existing_cache(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "track.mp3")
            Path(path).write_bytes(b"valid-cache")
            Path(path + ".part").write_bytes(b"stale-partial")

            result = await YOUTUBE._save_stream(
                FakeResponse([], content_length=100), path, 10
            )

            self.assertFalse(result)
            self.assertEqual(Path(path).read_bytes(), b"valid-cache")
            self.assertFalse(Path(path + ".part").exists())

    async def test_stream_over_limit_removes_partial_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "track.mp3")

            result = await YOUTUBE._save_stream(
                FakeResponse([b"123456", b"789012"]), path, 10
            )

            self.assertFalse(result)
            self.assertFalse(Path(path).exists())
            self.assertFalse(Path(path + ".part").exists())

    async def test_empty_download_leaves_no_file(self):
        with tempfile.TemporaryDirectory() as directory:
            path = str(Path(directory) / "track.mp3")

            result = await YOUTUBE._save_stream(FakeResponse([]), path, 10)

            self.assertFalse(result)
            self.assertFalse(Path(path).exists())
            self.assertFalse(Path(path + ".part").exists())


if __name__ == "__main__":
    unittest.main()
