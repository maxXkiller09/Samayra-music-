"""Low-overhead asyncio event-loop lag diagnostics for voice-chat stability."""

import asyncio
import logging

_LOGGER = logging.getLogger("YuvikaMusic.diagnostics")
_last_lag_ms = 0.0
_monitor_task = None


async def _monitor_loop(interval=1.0, report_interval=60.0):
    global _last_lag_ms
    loop = asyncio.get_running_loop()
    expected = loop.time() + interval
    next_report = loop.time() + report_interval
    max_lag_ms = 0.0

    while True:
        await asyncio.sleep(max(0.0, expected - loop.time()))
        now = loop.time()
        _last_lag_ms = max(0.0, (now - expected) * 1000.0)
        max_lag_ms = max(max_lag_ms, _last_lag_ms)

        if _last_lag_ms >= 250.0:
            _LOGGER.warning("event_loop_lag_ms=%.1f", _last_lag_ms)

        if now >= next_report:
            _LOGGER.info(
                "event_loop_lag_ms=%.1f max_event_loop_lag_60s_ms=%.1f",
                _last_lag_ms,
                max_lag_ms,
            )
            max_lag_ms = 0.0
            next_report = now + report_interval

        expected = now + interval


def start_event_loop_monitor(interval=1.0, report_interval=60.0):
    """Start one lightweight lag monitor; safe to call more than once."""
    global _monitor_task
    if _monitor_task is None or _monitor_task.done():
        _monitor_task = asyncio.create_task(
            _monitor_loop(interval=interval, report_interval=report_interval)
        )
    return _monitor_task


def get_event_loop_lag_ms():
    """Return the most recently sampled event-loop lag in milliseconds."""
    return _last_lag_ms


async def stop_event_loop_monitor():
    """Cancel and await the monitor during a clean shutdown."""
    global _monitor_task
    task = _monitor_task
    _monitor_task = None
    if task is None:
        return
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        pass
