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


# --- ffmpeg PATH me daalo (pip package imageio-ffmpeg se, internet download ki zaroorat nahi) ---
import os as _os
import shutil as _shutil

try:
    _bin_dir = _os.path.join(_os.getcwd(), "bin")
    if _os.path.isdir(_bin_dir):
        _os.environ["PATH"] = _bin_dir + _os.pathsep + _os.environ.get("PATH", "")
    if not _shutil.which("ffmpeg"):
        import imageio_ffmpeg as _iio

        _os.makedirs(_bin_dir, exist_ok=True)
        _link = _os.path.join(_bin_dir, "ffmpeg")
        if not _os.path.exists(_link):
            _os.symlink(_iio.get_ffmpeg_exe(), _link)
        _os.environ["PATH"] = _bin_dir + _os.pathsep + _os.environ.get("PATH", "")
except Exception as _e:
    print(f"[ffmpeg setup] {type(_e).__name__}: {_e}")
# ------------------------------------------------------------------------------------------

from ShrutiMusic.core.bot import Nand
from ShrutiMusic.core.dir import dirr
from ShrutiMusic.core.git import git
from ShrutiMusic.core.userbot import Userbot
from ShrutiMusic.misc import dbb, heroku

from .logging import LOGGER

dirr()
git()
dbb()
heroku()

app = Nand()
userbot = Userbot()


from .platforms import *

Apple = AppleAPI()
Carbon = CarbonAPI()
SoundCloud = SoundAPI()
Spotify = SpotifyAPI()
Resso = RessoAPI()
Telegram = TeleAPI()
YouTube = YouTubeAPI()


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots 
