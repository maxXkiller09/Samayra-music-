import os
from pathlib import Path
import subprocess
import sys
import unittest


ROOT = Path(__file__).resolve().parents[1]
REQUIRED_VALUES = {
    "API_ID": "12345",
    "API_HASH": "test-api-hash",
    "BOT_TOKEN": "12345:test-token",
    "OWNER_ID": "123456789",
    "LOG_GROUP_ID": "-1001234567890",
    "MONGO_DB_URI": "mongodb://127.0.0.1:27017/test",
}


class RequiredStartupConfigTests(unittest.TestCase):
    def test_duplicate_assistant_sessions_fail_without_echoing_secrets(self):
        env = os.environ.copy()
        env.update(REQUIRED_VALUES)
        env["STRING_SESSION"] = "private-session-test-value"
        env["STRING_SESSION2"] = "private-session-test-value"
        result = subprocess.run(
            [sys.executable, "-c", "import config"],
            cwd=ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=15,
        )
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("Duplicate assistant session configured", result.stderr)
        self.assertNotIn("private-session-test-value", result.stderr)

    def test_each_required_setting_fails_fast_when_missing(self):
        for missing in REQUIRED_VALUES:
            with self.subTest(missing=missing):
                env = os.environ.copy()
                env.update(REQUIRED_VALUES)
                env.pop(missing, None)
                result = subprocess.run(
                    [sys.executable, "-c", "import config"],
                    cwd=ROOT,
                    env=env,
                    capture_output=True,
                    text=True,
                    timeout=15,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertIn(
                    f"Missing required environment variable: {missing}",
                    result.stderr,
                )


if __name__ == "__main__":
    unittest.main()
