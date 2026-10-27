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
import importlib
from pyrogram import idle
from pyrogram.types import BotCommand
import config
from ShrutiMusic import LOGGER, app, userbot
from ShrutiMusic.core.call import Nand
from ShrutiMusic.misc import sudo
from ShrutiMusic.plugins import ALL_MODULES
from ShrutiMusic.utils.database import get_banned_users, get_gbanned
from ShrutiMusic.utils.stream.diagnostics import (
    start_event_loop_monitor,
    stop_event_loop_monitor,
)
from config import BANNED_USERS

COMMANDS = [
    BotCommand("start", "❖ sᴛᴀʀᴛ ʙᴏᴛ • ᴛᴏ sᴛᴀʀᴛ ᴛʜᴇ ʙᴏᴛ"),
    BotCommand("help", "❖ ʜᴇʟᴘ ᴍᴇɴᴜ • ɢᴇᴛ ᴀʟʟ ᴄᴏᴍᴍᴀɴᴅs ᴀɴᴅ ᴍᴀɴᴀɢᴇᴍᴇɴᴛ"),
    BotCommand("ping", "❖ ᴘɪɴɢ ʙᴏᴛ • ᴄʜᴇᴄᴋ ᴘɪɴɢ ᴀɴᴅ sʏsᴛᴇᴍ sᴛᴀᴛs"),
    BotCommand("play", "❖ ᴘʟᴀʏ ᴀᴜᴅɪᴏ ᴏɴ ᴠᴄ • ᴛᴏ ᴘʟᴀʏ ᴀɴʏ ᴀᴜᴅɪᴏ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
    BotCommand("vplay", "❖ ᴘʟᴀʏ ᴠɪᴅᴇᴏ ᴏɴ ᴠᴄ • ᴛᴏ sᴛʀᴇᴀᴍ ᴀɴʏ ᴠɪᴅᴇᴏ ɪɴ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ"),
    BotCommand("playrtmps", "❖ ᴘʟᴀʏ ʟɪᴠᴇ ᴠɪᴅᴇᴏ • sᴛʀᴇᴀᴍ ʟɪᴠᴇ ᴠɪᴅᴇᴏ ᴄᴏɴᴛᴇɴᴛ"),
    BotCommand("playforce", "❖ ғᴏʀᴄᴇ ᴘʟᴀʏ ᴀᴜᴅɪᴏ • ғᴏʀᴄᴇ ᴘʟᴀʏ ᴀɴʏ ᴀᴜᴅɪᴏ ᴛʀᴀᴄᴋ"),
    BotCommand("vplayforce", "❖ ғᴏʀᴄᴇ ᴘʟᴀʏ ᴠɪᴅᴇᴏ • ғᴏʀᴄᴇ ᴘʟᴀʏ ᴀɴʏ ᴠɪᴅᴇᴏ ᴛʀᴀᴄᴋ"),
    BotCommand("pause", "❖ ᴘᴀᴜsᴇ sᴛʀᴇᴀᴍ • ᴘᴀᴜsᴇ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ"),
    BotCommand("resume", "❖ ʀᴇsᴜᴍᴇ sᴛʀᴇᴀᴍ • ʀᴇsᴜᴍᴇ ᴛʜᴇ ᴘᴀᴜsᴇᴅ sᴛʀᴇᴀᴍ"),
    BotCommand("skip", "❖ sᴋɪᴘ ᴛʀᴀᴄᴋ • sᴋɪᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ ᴛʀᴀᴄᴋ"),
    BotCommand("end", "❖ ᴇɴᴅ sᴛʀᴇᴀᴍ • sᴛᴏᴘ ᴛʜᴇ ᴏɴɢᴏɪɴɢ sᴛʀᴇᴀᴍ"),
    BotCommand("stop", "❖ sᴛᴏᴘ sᴛʀᴇᴀᴍ • sᴛᴏᴘ ᴛʜᴇ ᴄᴜʀʀᴇɴᴛ sᴛʀᴇᴀᴍ"),
    BotCommand("queue", "❖ sʜᴏᴡ ǫᴜᴇᴜᴇ • ᴅɪsᴘʟᴀʏ ᴛʀᴀᴄᴋ ǫᴜᴇᴜᴇ ʟɪsᴛ"),
    BotCommand("auth", "❖ ᴀᴅᴅ ᴀᴜᴛʜ ᴜsᴇʀ • ᴀᴅᴅ ᴜsᴇʀ ᴛᴏ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ʟɪsᴛ"),
    BotCommand("unauth", "❖ ʀᴇᴍᴏᴠᴇ ᴀᴜᴛʜ • ʀᴇᴍᴏᴠᴇ ᴜsᴇʀ ғʀᴏᴍ ᴀᴜᴛʜ ʟɪsᴛ"),
    BotCommand("authusers", "❖ ᴀᴜᴛʜ ʟɪsᴛ • sʜᴏᴡ ᴀʟʟ ᴀᴜᴛʜᴏʀɪᴢᴇᴅ ᴜsᴇʀs"),
    BotCommand("cplay", "❖ ᴄʜᴀɴɴᴇʟ ᴀᴜᴅɪᴏ • ᴘʟᴀʏ ᴀᴜᴅɪᴏ ɪɴ ᴄʜᴀɴɴᴇʟ"),
    BotCommand("cvplay", "❖ ᴄʜᴀɴɴᴇʟ ᴠɪᴅᴇᴏ • ᴘʟᴀʏ ᴠɪᴅᴇᴏ ɪɴ ᴄʜᴀɴɴᴇʟ"),
    BotCommand("cplayforce", "❖ ᴄʜᴀɴɴᴇʟ ғᴏʀᴄᴇ ᴀᴜᴅɪᴏ • ғᴏʀᴄᴇ ᴘʟᴀʏ ɪɴ ᴄʜᴀɴɴᴇʟ"),
    BotCommand("cvplayforce", "❖ ᴄʜᴀɴɴᴇʟ ғᴏʀᴄᴇ ᴠɪᴅᴇᴏ • ғᴏʀᴄᴇ ᴠɪᴅᴇᴏ ɪɴ ᴄʜᴀɴɴᴇʟ"),
    BotCommand("channelplay", "❖ ᴄᴏɴɴᴇᴄᴛ ᴄʜᴀɴɴᴇʟ • ʟɪɴᴋ ɢʀᴏᴜᴘ ᴛᴏ ᴄʜᴀɴɴᴇʟ"),
    BotCommand("loop", "❖ ʟᴏᴏᴘ ᴍᴏᴅᴇ • ᴇɴᴀʙʟᴇ ᴏʀ ᴅɪsᴀʙʟᴇ ʟᴏᴏᴘ"),
    BotCommand("stats", "❖ ʙᴏᴛ sᴛᴀᴛs • sʜᴏᴡ ʙᴏᴛ sᴛᴀᴛɪsᴛɪᴄs"),
    BotCommand("shuffle", "❖ sʜᴜғғʟᴇ ǫᴜᴇᴜᴇ • ʀᴀɴᴅᴏᴍɪᴢᴇ ᴛʀᴀᴄᴋ ᴏʀᴅᴇʀ"),
    BotCommand("seek", "❖ sᴇᴇᴋ ғᴏʀᴡᴀʀᴅ • sᴋɪᴘ ᴛᴏ sᴘᴇᴄɪғɪᴄ ᴛɪᴍᴇ"),
    BotCommand("seekback", "❖ sᴇᴇᴋ ʙᴀᴄᴋᴡᴀʀᴅ • ɢᴏ ʙᴀᴄᴋ ᴛᴏ ᴘʀᴇᴠɪᴏᴜs ᴛɪᴍᴇ"),
    BotCommand("song", "❖ ᴅᴏᴡɴʟᴏᴀᴅ sᴏɴɢ • ɢᴇᴛ ᴍᴘ3 ᴏʀ ᴍᴘ4 ғɪʟᴇ"),
    BotCommand("speed", "❖ ᴀᴅᴊᴜsᴛ sᴘᴇᴇᴅ • ᴄʜᴀɴɢᴇ ᴘʟᴀʏʙᴀᴄᴋ sᴘᴇᴇᴅ ɪɴ ɢʀᴏᴜᴘ"),
    BotCommand("cspeed", "❖ ᴄʜᴀɴɴᴇʟ sᴘᴇᴇᴅ • ᴀᴅᴊᴜsᴛ sᴘᴇᴇᴅ ɪɴ ᴄʜᴀɴɴᴇʟ"),
    BotCommand("tagall", "❖ ᴛᴀɢ ᴀʟʟ • ᴍᴇɴᴛɪᴏɴ ᴇᴠᴇʀʏᴏɴᴇ ɪɴ ɢʀᴏᴜᴘ"),
]

async def setup_bot_commands():
    try:
        await app.set_bot_commands(COMMANDS)
        LOGGER("YuvikaMusic").info("Yuvika Music bot commands set successfully!")
        
    except Exception as e:
        LOGGER("YuvikaMusic").error(f"Failed to set Yuvika Music bot commands: {str(e)}")

async def init():
    if (
        not config.STRING1
        and not config.STRING2
        and not config.STRING3
        and not config.STRING4
        and not config.STRING5
    ):
        LOGGER(__name__).error("Assistant client variables not defined, exiting...")
        exit()

    await sudo()

    try:
        users = await get_gbanned()
        for user_id in users:
            BANNED_USERS.add(user_id)
        users = await get_banned_users()
        for user_id in users:
            BANNED_USERS.add(user_id)
    except:
        pass

    await app.start()
    
    await setup_bot_commands()

    for all_module in ALL_MODULES:
        importlib.import_module("ShrutiMusic.plugins" + all_module)

    LOGGER("YuvikaMusic.plugins").info("Successfully imported Yuvika Music modules.")

    await userbot.start()
    await Nand.start()

    await Nand.decorators()

    LOGGER("ShrutiMusic").info(
        "Yuvika Music started successfully."
    )

    start_event_loop_monitor()
    await idle()
    await stop_event_loop_monitor()

    await app.stop()
    await userbot.stop()
    LOGGER("YuvikaMusic").info("Stopping Yuvika Music bot...")

if __name__ == "__main__":
    asyncio.get_event_loop().run_until_complete(init())


# ©️ Copyright Reserved - @NoxxOP  Nand Yaduwanshi

# ===========================================
# ©️ 2025 Nand Yaduwanshi (aka @NoxxOP)
# 🔗 GitHub : https://github.com/NoxxOP/ShrutiMusic
# 📢 Telegram Channel : https://t.me/ShrutiBots
# ===========================================


# ❤️ Love From ShrutiBots
