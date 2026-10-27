import unittest

from session_validation import duplicate_session_slots


class DuplicateAssistantSessionTests(unittest.TestCase):
    def test_detects_duplicate_session_without_returning_secret(self):
        secret = "private-session-value"
        duplicates = duplicate_session_slots([
            ("STRING_SESSION", secret),
            ("STRING_SESSION2", f" {secret} "),
        ])
        self.assertEqual(duplicates, [("STRING_SESSION", "STRING_SESSION2")])
        self.assertNotIn(secret, repr(duplicates))

    def test_ignores_empty_slots_and_allows_distinct_sessions(self):
        self.assertEqual(duplicate_session_slots([
            ("STRING_SESSION", ""),
            ("STRING_SESSION2", None),
            ("STRING_SESSION3", "session-three"),
            ("STRING_SESSION4", "session-four"),
        ]), [])

    def test_ignores_whitespace_only_values(self):
        self.assertEqual(duplicate_session_slots([
            ("STRING_SESSION", "   "),
            ("STRING_SESSION2", ""),
        ]), [])


if __name__ == "__main__":
    unittest.main()
