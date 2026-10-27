import asyncio
import importlib.util
from pathlib import Path
import time
import unittest


ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = ROOT / "ShrutiMusic" / "utils" / "stream" / "diagnostics.py"


class EventLoopDiagnosticsTests(unittest.IsolatedAsyncioTestCase):
    @classmethod
    def setUpClass(cls):
        spec = importlib.util.spec_from_file_location(
            "event_loop_diagnostics_under_test", MODULE_PATH
        )
        cls.module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.module)

    async def test_monitor_records_a_deliberate_event_loop_stall(self):
        self.module.start_event_loop_monitor(interval=0.05, report_interval=60)
        try:
            await asyncio.sleep(0.01)
            time.sleep(0.08)
            for _ in range(10):
                await asyncio.sleep(0)
                if self.module.get_event_loop_lag_ms() > 10.0:
                    break
            self.assertGreater(self.module.get_event_loop_lag_ms(), 10.0)
        finally:
            await self.module.stop_event_loop_monitor()

    async def test_monitor_start_is_idempotent(self):
        first = self.module.start_event_loop_monitor(interval=0.02)
        second = self.module.start_event_loop_monitor(interval=0.02)
        self.assertIs(first, second)
        await self.module.stop_event_loop_monitor()


if __name__ == "__main__":
    unittest.main()
