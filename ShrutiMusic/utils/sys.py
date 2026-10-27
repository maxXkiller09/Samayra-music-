# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com


import asyncio
import time

import psutil

from ShrutiMusic.misc import _boot_
from ShrutiMusic.utils.formatters import get_readable_time


def _read_system_metrics():
    """Collect blocking psutil metrics outside the asyncio event loop."""
    return (
        psutil.cpu_percent(interval=0.5),
        psutil.virtual_memory().percent,
        psutil.disk_usage("/").percent,
    )


async def bot_sys_stats():
    bot_uptime = int(time.time() - _boot_)
    up = get_readable_time(bot_uptime)
    cpu, ram, disk = await asyncio.to_thread(_read_system_metrics)
    return up, f"{cpu}%", f"{ram}%", f"{disk}%"


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
