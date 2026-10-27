import asyncio
import importlib.util
from pathlib import Path
import sys
import time
import types
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "sys.py"


class SystemStatsAsyncTests(unittest.IsolatedAsyncioTestCase):
    async def test_slow_metrics_do_not_block_event_loop(self):
        fake_root = types.ModuleType("ShrutiMusic")
        fake_root.__path__ = [str(ROOT / "ShrutiMusic")]
        fake_misc = types.ModuleType("ShrutiMusic.misc")
        fake_misc._boot_ = time.time() - 60
        fake_utils = types.ModuleType("ShrutiMusic.utils")
        fake_utils.__path__ = [str(ROOT / "ShrutiMusic" / "utils")]
        fake_formatters = types.ModuleType("ShrutiMusic.utils.formatters")
        fake_formatters.get_readable_time = lambda seconds: f"{seconds}s"

        modules = {
            "ShrutiMusic": fake_root,
            "ShrutiMusic.misc": fake_misc,
            "ShrutiMusic.utils": fake_utils,
            "ShrutiMusic.utils.formatters": fake_formatters,
        }
        with patch.dict(sys.modules, modules):
            spec = importlib.util.spec_from_file_location(
                "system_stats_under_test", MODULE_PATH
            )
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)

        def slow_metrics():
            time.sleep(0.15)
            return 10.0, 20.0, 30.0

        ticks = 0

        async def heartbeat():
            nonlocal ticks
            deadline = asyncio.get_running_loop().time() + 0.12
            while asyncio.get_running_loop().time() < deadline:
                ticks += 1
                await asyncio.sleep(0.005)

        with patch.object(module, "_read_system_metrics", slow_metrics):
            result, _ = await asyncio.gather(module.bot_sys_stats(), heartbeat())

        self.assertGreater(ticks, 5)
        self.assertEqual(result, ("60s", "10.0%", "20.0%", "30.0%"))


if __name__ == "__main__":
    unittest.main()
