import unittest

from ShrutiMusic.utils.autoplay_commands import parse_autoplay_action


class AutoplayCommandParsingTests(unittest.TestCase):
    def test_no_argument_preserves_legacy_toggle(self):
        self.assertEqual(parse_autoplay_action([]), "toggle")

    def test_supported_actions_are_case_insensitive(self):
        for action in ("on", "off", "status", "next"):
            with self.subTest(action=action):
                self.assertEqual(parse_autoplay_action([action.upper()]), action)

    def test_unknown_action_is_rejected(self):
        self.assertEqual(parse_autoplay_action(["maybe"]), "invalid")


if __name__ == "__main__":
    unittest.main()
