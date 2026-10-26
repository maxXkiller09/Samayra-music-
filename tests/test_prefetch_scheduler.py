import asyncio
import importlib.util
from pathlib import Path
import sys
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "stream" / "prefetch.py"


class PrefetchSchedulerTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.db_data = {}
        fake_config = types.ModuleType("config")
        fake_config.autoclean = []
        fake_misc = types.ModuleType("ShrutiMusic.misc")
        fake_misc.db = self.db_data
        fake_queue_files = types.ModuleType("ShrutiMusic.utils.stream.queue_files")
        fake_queue_files.replace_tracked_queue_item = lambda *args: True
        modules = {
            "config": fake_config,
            "ShrutiMusic.misc": fake_misc,
            "ShrutiMusic.utils.stream.queue_files": fake_queue_files,
        }
        self.module_patch = patch.dict(sys.modules, modules)
        self.module_patch.start()
        spec = importlib.util.spec_from_file_location(
            "prefetch_scheduler_under_test", MODULE_PATH
        )
        self.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.module)

    async def asyncTearDown(self):
        for task in self.module._TASKS.values():
            task.cancel()
        await asyncio.gather(*self.module._TASKS.values(), return_exceptions=True)
        self.module_patch.stop()

    async def test_only_one_prefetch_task_runs_per_chat(self):
        chat_id = -100123
        current = {"file": "/cache/current.mp3"}
        next_item = {"file": "vid_abcdefghijk", "vidid": "abcdefghijk"}
        self.db_data[chat_id] = [current, next_item]
        gate = asyncio.Event()

        async def pending_task():
            await gate.wait()

        active = asyncio.create_task(pending_task())
        self.module._TASKS[(chat_id, id({"file": "old"}))] = active
        scheduled = self.module.schedule_next_prefetch(chat_id)

        self.assertIs(scheduled, active)
        self.assertEqual(len(self.module._TASKS), 1)
        gate.set()
        await active

    async def test_reschedules_when_next_item_changes_while_prefetch_is_busy(self):
        chat_id = -100456
        attempted = {"file": "vid_old", "vidid": "old"}
        replacement = {"file": "vid_new", "vidid": "new"}
        self.db_data[chat_id] = [{"file": "/cache/current.mp3"}, replacement]

        with patch.object(self.module, "schedule_next_prefetch") as schedule:
            self.module._reschedule_if_next_changed(chat_id, attempted, None)

        schedule.assert_called_once_with(chat_id)

    async def test_does_not_reschedule_when_same_next_item_remains(self):
        chat_id = -100789
        attempted = {"file": "vid_same", "vidid": "same"}
        self.db_data[chat_id] = [{"file": "/cache/current.mp3"}, attempted]

        with patch.object(self.module, "schedule_next_prefetch") as schedule:
            self.module._reschedule_if_next_changed(chat_id, attempted, None)

        schedule.assert_not_called()


if __name__ == "__main__":
    unittest.main()
