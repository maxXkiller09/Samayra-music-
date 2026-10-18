import os
import platform
import shutil
import time

import aiohttp
import psutil
from pyrogram import filters

from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS
from ShrutiMusic.utils.database import get_active_chats, get_served_chats, get_served_users


def _fmt_uptime(sec):
    d, rem = divmod(int(sec), 86400)
    h, rem = divmod(rem, 3600)
    m, _ = divmod(rem, 60)
    return f"{d}d {h}h {m}m"


async def _api_status():
    base = (os.getenv("BASE_API_URL") or os.getenv("API_URL") or "").strip().rstrip("/")
    if not base:
        return "❌ Set nahi hai"
    try:
        timeout = aiohttp.ClientTimeout(total=8)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(base) as resp:
                return f"✅ Chal rahi hai (HTTP {resp.status})"
    except Exception as e:
        return f"⚠️ Connect nahi hui ({type(e).__name__})"


@app.on_message(filters.command(["panel", "botstatus"], prefixes=["/", "!", "."]) & SUDOERS)
async def owner_panel(_, message):
    wait = await message.reply_text("⏳ Status nikal raha hoon...")
    proc = psutil.Process()
    chats = len(await get_served_chats())
    users = len(await get_served_users())
    try:
        active = len(await get_active_chats())
    except Exception:
        active = 0
    api = await _api_status()
    ram = psutil.virtual_memory()

    text = (
        "🛠️ <b>Bot Status Panel</b>\n\n"
        f"👥 Groups: <b>{chats}</b>\n"
        f"👤 Users: <b>{users}</b>\n"
        f"🎧 Abhi VC me chal raha: <b>{active}</b>\n\n"
        f"⏱️ Uptime: <b>{_fmt_uptime(time.time() - proc.create_time())}</b>\n"
        f"🧠 Bot RAM: <b>{proc.memory_info().rss / 1024 / 1024:.0f} MB</b> "
        f"(system {ram.percent}% used)\n"
        f"⚙️ CPU: <b>{psutil.cpu_percent(interval=0.5)}%</b>\n\n"
        f"🔌 Downloader API: {api}\n"
        f"🎬 ffmpeg: {'✅' if shutil.which('ffmpeg') else '❌'}  ffprobe: {'✅' if shutil.which('ffprobe') else '❌'}\n"
        f"🤖 Gemini key: {'✅ laga hai' if os.getenv('GEMINI_API_KEY') else '❌ nahi'}\n"
        f"🐍 Python: <b>{platform.python_version()}</b>"
    )
    await wait.edit_text(text)


__MODULE__ = "Pᴀɴᴇʟ"
__HELP__ = """
**Owner Panel (sirf sudoers):**

• `/panel`: Bot ka poora status: groups, users, uptime, RAM, API aur ffmpeg ki sthiti.
"""
