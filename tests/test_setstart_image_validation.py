"""Regression tests for /setstart welcome-image validation and Telegram media handling."""
import ast
import asyncio
import io
import unittest
from types import SimpleNamespace
from urllib.parse import urljoin
from unittest.mock import AsyncMock
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock

from PIL import Image, UnidentifiedImageError


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "ShrutiMusic" / "plugins" / "tools" / "setstart.py"


def _function_node(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            node.decorator_list = []
            return node
    raise AssertionError(f"Missing function: {name}")


def _validator():
    source = PLUGIN_PATH.read_text(encoding="utf-8")
    node = _function_node(source, "_validate_image_bytes")
    namespace = {
        "io": io,
        "Image": Image,
        "UnidentifiedImageError": UnidentifiedImageError,
        "MAX_IMAGE_BYTES": 5 * 1024 * 1024,
        "MAX_IMAGE_DIMENSION": 10_000,
        "MAX_IMAGE_PIXELS": 40_000_000,
        "_IMAGE_FORMATS": {"JPEG", "PNG", "GIF", "WEBP"},
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(PLUGIN_PATH), "exec"), namespace)
    return namespace["_validate_image_bytes"]


def _image_bytes(fmt="JPEG", size=(32, 24)):
    output = io.BytesIO()
    Image.new("RGB", size, "navy").save(output, format=fmt)
    return output.getvalue()


class _FakeContent:
    def __init__(self, data):
        self.data = data

    async def iter_chunked(self, chunk_size):
        for offset in range(0, len(self.data), chunk_size):
            yield self.data[offset:offset + chunk_size]


class _FakeResponse:
    def __init__(self, data, content_type="application/octet-stream", status=200, timeout=False):
        self.data = data
        self.status = status
        self.headers = {"Content-Type": content_type, "Content-Length": str(len(data))}
        self.content = _FakeContent(data)
        self.timeout = timeout

    async def __aenter__(self):
        if self.timeout:
            raise asyncio.TimeoutError()
        return self

    async def __aexit__(self, *args):
        return False


class _FakeSession:
    def __init__(self, response):
        self.response = response

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return False

    def get(self, url, allow_redirects=False):
        return self.response


def _image_downloader(response, validate):
    source = PLUGIN_PATH.read_text(encoding="utf-8")
    node = _function_node(source, "_download_image")
    namespace = {
        "aiohttp": SimpleNamespace(
            ClientTimeout=lambda **kwargs: None,
            ClientSession=lambda **kwargs: _FakeSession(response),
        ),
        "asyncio": asyncio,
        "urljoin": urljoin,
        "_safe_public_https": AsyncMock(),
        "_validate_image_bytes": validate,
        "MAX_REDIRECTS": 3,
        "MAX_IMAGE_BYTES": 5 * 1024 * 1024,
        "_IMAGE_FORMATS": {"JPEG", "PNG", "GIF", "WEBP"},
    }
    exec(compile(ast.Module(body=[node], type_ignores=[]), str(PLUGIN_PATH), "exec"), namespace)
    return namespace["_download_image"]


class SetStartImageValidationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = PLUGIN_PATH.read_text(encoding="utf-8")
        cls.validate = staticmethod(_validator())

    def test_valid_telegram_jpeg_is_accepted(self):
        self.assertEqual(self.validate(_image_bytes("JPEG")), "JPEG")

    def test_valid_png_and_webp_are_accepted(self):
        self.assertEqual(self.validate(_image_bytes("PNG")), "PNG")
        self.assertEqual(self.validate(_image_bytes("WEBP")), "WEBP")

    def test_corrupt_or_html_content_is_rejected(self):
        for payload in (b"not an image", b"<html><body>not an image</body></html>", b"\xff\xd8\xfftruncated"):
            with self.subTest(payload=payload[:12]):
                with self.assertRaises(ValueError):
                    self.validate(payload)

    def test_empty_and_oversized_downloads_are_rejected(self):
        with self.assertRaisesRegex(ValueError, "empty"):
            self.validate(b"")
        with self.assertRaisesRegex(ValueError, "5 MB"):
            self.validate(b"x" * (5 * 1024 * 1024 + 1))

    def test_oversized_dimensions_are_rejected(self):
        with self.assertRaises(ValueError):
            self.validate(_image_bytes("PNG", (10_001, 1)))

    def test_telegram_photo_and_document_use_framework_download(self):
        self.assertIn("filters.photo | filters.document", self.source)
        self.assertIn("await app.download_media(message, in_memory=True)", self.source)
        self.assertIn("media = message.photo[-1]", self.source)
        self.assertIn('stage = "download_telegram_photo"', self.source)
        self.assertIn('stage = "download_telegram_document"', self.source)

    def test_invalid_image_does_not_update_draft_before_validation(self):
        handler = ast.get_source_segment(
            self.source, _function_node(self.source, "setstart_collect_input")
        )
        self.assertLess(handler.index("_validate_image_bytes(data)"), handler.index('draft["photo"] = photo_id'))
        self.assertIn("_drafts.get(OWNER_ID) is not draft", handler)

    def test_failure_logging_is_safe_and_stage_specific(self):
        self.assertIn("stage=%s exception_type=%s", self.source)
        self.assertIn("setstart image input failed", self.source)
        self.assertNotIn("LOGGER.error(\"setstart image input failed; stage=%s exception=%s", self.source)

    def test_url_content_is_validated_by_image_parser_not_header_only(self):
        downloader = ast.get_source_segment(self.source, _function_node(self.source, "_download_image"))
        self.assertIn("_validate_image_bytes(image)", downloader)
        self.assertIn("allow_redirects=False", downloader)
        self.assertIn("MAX_REDIRECTS", downloader)
        self.assertIn("MAX_IMAGE_BYTES", downloader)
        self.assertNotIn('raise ValueError("That URL is not serving an image.")', downloader)

    def test_owner_guard_and_save_only_on_confirmation_remain(self):
        command = ast.get_source_segment(self.source, _function_node(self.source, "setstart_command"))
        callback = ast.get_source_segment(self.source, _function_node(self.source, "setstart_callback"))
        self.assertIn("_is_owner(message.from_user.id)", command)
        self.assertIn("_is_owner(query.from_user.id)", callback)
        self.assertIn('if action == "save":', callback)
        self.assertIn("await save_start_settings(caption, draft.get(\"photo\"))", callback)

    def test_https_url_download_accepts_image_even_with_mismatched_content_type(self):
        response = _FakeResponse(_image_bytes("JPEG"), content_type="application/octet-stream")
        downloader = _image_downloader(response, self.validate)
        self.assertEqual(asyncio.run(downloader("https://images.example/welcome")), _image_bytes("JPEG"))

    def test_https_url_download_rejects_html_body(self):
        response = _FakeResponse(b"<html>not an image</html>", content_type="image/jpeg")
        downloader = _image_downloader(response, self.validate)
        with self.assertRaises(ValueError):
            asyncio.run(downloader("https://images.example/not-an-image"))

    def test_https_url_timeout_is_not_silently_swallowed(self):
        response = _FakeResponse(b"", timeout=True)
        downloader = _image_downloader(response, self.validate)
        with self.assertRaises(asyncio.TimeoutError):
            asyncio.run(downloader("https://images.example/slow"))


if __name__ == "__main__":
    unittest.main()
