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


import os

from config import autoclean


def release_file(path):
    """Release one queued reference and delete the file when no item uses it."""
    if not path:
        return

    try:
        autoclean.remove(path)
    except ValueError:
        pass

    if autoclean.count(path) == 0:
        if os.path.basename(str(path)).startswith(("vid_", "live_", "index_")):
            return
        try:
            os.remove(path)
        except OSError:
            pass


async def auto_clean(popped):
    if not popped:
        return

    rem = popped.get("file")
    speed_path = popped.get("speed_path")
    release_file(rem)
    if speed_path and speed_path != rem:
        release_file(speed_path)


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
