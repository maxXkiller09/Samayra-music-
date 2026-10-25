"""Minimal HTTP health endpoint for Render Web Services.

This endpoint confirms the container's HTTP listener is alive; it does not
claim that Telegram, MongoDB, or voice-chat playback are healthy.
"""
import asyncio
import os

from aiohttp import web


async def health(_request):
    return web.json_response({"status": "ok", "service": "samayra-music"})


async def main():
    app = web.Application()
    app.router.add_get("/", health)
    app.router.add_get("/health", health)
    runner = web.AppRunner(app, access_log=None)
    await runner.setup()
    port = int(os.environ.get("PORT", "10000"))
    site = web.TCPSite(runner, "0.0.0.0", port)
    await site.start()
    print(f"[health] HTTP listener ready on 0.0.0.0:{port}", flush=True)
    try:
        await asyncio.Event().wait()
    finally:
        await runner.cleanup()


if __name__ == "__main__":
    asyncio.run(main())
