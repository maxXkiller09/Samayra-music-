import ast
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
PLUGIN_PATH = ROOT / "ShrutiMusic" / "plugins" / "tools" / "setstart.py"
START_PATH = ROOT / "ShrutiMusic" / "plugins" / "bot" / "start.py"
SETTINGS_PATH = ROOT / "ShrutiMusic" / "utils" / "startsettings.py"


def source_function(source, name):
    tree = ast.parse(source)
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == name:
            return ast.get_source_segment(source, node)
    raise AssertionError(f"Missing function: {name}")


class SetStartFeatureRegressionTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plugin = PLUGIN_PATH.read_text(encoding="utf-8")
        cls.start = START_PATH.read_text(encoding="utf-8")
        cls.settings = SETTINGS_PATH.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.plugin)

    def test_feature_modules_have_valid_python_syntax(self):
        ast.parse(self.plugin)
        ast.parse(self.start)
        ast.parse(self.settings)

    def test_owner_checked_for_command_and_every_callback(self):
        command = source_function(self.plugin, "setstart_command")
        callback = source_function(self.plugin, "setstart_callback")
        self.assertIn("_is_owner(message.from_user.id)", command)
        self.assertIn("_is_owner(query.from_user.id)", callback)
        self.assertIn("query.message.chat.id != OWNER_ID", callback)

    def test_stale_callback_tokens_are_rejected(self):
        callback = source_function(self.plugin, "setstart_callback")
        self.assertIn('draft.get("token") != token', callback)
        self.assertIn("_rotate(draft)", callback)

    def test_image_urls_are_restricted_and_bounded(self):
        url_check = source_function(self.plugin, "_safe_public_https")
        downloader = source_function(self.plugin, "_download_image")
        self.assertIn('scheme.lower() != "https"', url_check)
        self.assertIn("address.is_global", url_check)
        self.assertIn("MAX_REDIRECTS", downloader)
        self.assertIn("MAX_IMAGE_BYTES", downloader)
        self.assertIn("allow_redirects=False", downloader)

    def test_telegram_photo_upload_uses_largest_native_file_id(self):
        node = next(
            node for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_largest_photo_file_id"
        )
        namespace = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<largest-photo>", "exec"), namespace)

        class PhotoSize:
            def __init__(self, file_id, width, height, file_size):
                self.file_id = file_id
                self.width = width
                self.height = height
                self.file_size = file_size

        sizes = [
            PhotoSize("small", 90, 90, 1000),
            PhotoSize("medium", 320, 320, 12000),
            PhotoSize("large", 1280, 1280, 90000),
        ]
        self.assertEqual(namespace["_largest_photo_file_id"](sizes), "large")

    def test_photo_upload_does_not_use_url_validation(self):
        collector = source_function(self.plugin, "setstart_collect_input")
        self.assertIn("_largest_photo_file_id(message.photo)", collector)
        self.assertLess(collector.index("if message.photo:"), collector.index("_photo_file_id_from_url(message.text.strip())"))

    def test_preview_and_save_use_draft_photo_file_id(self):
        preview = source_function(self.plugin, "_preview")
        callback = source_function(self.plugin, "setstart_callback")
        self.assertIn("photo=photo", preview)
        self.assertIn('save_start_settings(caption, draft.get("photo"))', callback)
        self.assertIn("Save failed. Previous settings remain active.", callback)
        self.assertIn("await save_start_settings(caption, draft.get(\"photo\"))", callback)

    def test_start_falls_back_when_saved_photo_id_is_unusable(self):
        helper = source_function(self.start, "_reply_welcome_photo")
        self.assertIn("photo=config.START_IMG_URL", helper)
        self.assertIn("saved Yuvika Music welcome image could not be sent", helper)
        self.assertIn("_reply_welcome_photo(", self.start)

    def test_settings_are_persisted_atomically_in_mongodb(self):
        self.assertIn('{"_id": "global"}', self.settings)
        self.assertIn('"$set": {"caption": caption, "photo": photo}', self.settings)
        self.assertIn('delete_one({"_id": "global"})', self.settings)

    def test_start_handlers_read_saved_welcome_settings(self):
        self.assertIn("get_start_settings", self.start)
        self.assertIn("_welcome_payload(message, default_caption)", self.start)
        self.assertIn("_reply_welcome_photo(", self.start)
        self.assertIn("welcome_photo, welcome_caption", self.start)

    def test_help_deep_link_uses_saved_welcome_image(self):
        start_pm = source_function(self.start, "start_pm")
        help_branch = start_pm.split('if name[0:4] == "help":', 1)[1].split('if name[0:3] == "sud":', 1)[0]
        self.assertIn("_welcome_payload(message, help_caption)", help_branch)
        self.assertIn("_reply_welcome_photo(", help_branch)
        self.assertNotIn("photo=config.START_IMG_URL", help_branch)

    def test_caption_length_uses_telegram_utf16_units(self):
        node = next(
            node for node in self.tree.body
            if isinstance(node, ast.FunctionDef) and node.name == "_caption_length"
        )
        namespace = {}
        exec(compile(ast.Module(body=[node], type_ignores=[]), "<caption-length>", "exec"), namespace)
        self.assertEqual(namespace["_caption_length"]("hello"), 5)
        self.assertEqual(namespace["_caption_length"]("🎶"), 2)
        self.assertEqual(namespace["_caption_length"]("a🎶"), 3)


if __name__ == "__main__":
    unittest.main()
