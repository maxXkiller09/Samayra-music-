import asyncio
import re

from pyrogram import filters
from pyrogram.enums import ChatMemberStatus, MessageEntityType

from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.misc import SUDOERS

antilink_db = mongodb.antilink
_cache = {}

LINK_RE = re.compile(
    r"(https?://|www\.|t\.me/|telegram\.me/|telegram\.dog/|\b[a-z0-9-]+\.(com|in|net|org|me|io|xyz|co|link|site|live|app|club|top|info)\b)",
    re.I,
)
LINK_ENTITIES = {MessageEntityType.URL, MessageEntityType.TEXT_LINK}


async def _is_admin(chat_id, user_id):
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


async def _enabled(chat_id):
    if chat_id in _cache:
        return _cache[chat_id]
    doc = await antilink_db.find_one({"chat_id": chat_id})
    _cache[chat_id] = bool(doc and doc.get("enabled"))
    return _cache[chat_id]


@app.on_message(filters.command("antilink") & filters.group)
async def antilink_toggle(_, message):
    if not message.from_user or not await _is_admin(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Ye command sirf group admins ke liye hai.")
    if len(message.command) < 2 or message.command[1].lower() not in ("on", "off"):
        state = "ON ✅" if await _enabled(message.chat.id) else "OFF ❌"
        return await message.reply_text(
            f"🔗 Antilink abhi: <b>{state}</b>\n\nUse karo: <code>/antilink on</code> ya <code>/antilink off</code>"
        )
    on = message.command[1].lower() == "on"
    await antilink_db.update_one({"chat_id": message.chat.id}, {"$set": {"enabled": on}}, upsert=True)
    _cache[message.chat.id] = on
    await message.reply_text(
        "✅ Antilink <b>ON</b> ho gaya. Ab admins ke alawa koi link bhejega to delete ho jayega."
        if on
        else "❎ Antilink <b>OFF</b> ho gaya."
    )


def _has_link(message):
    for entities in (message.entities, message.caption_entities):
        if entities and any(e.type in LINK_ENTITIES for e in entities):
            return True
    text = message.text or message.caption or ""
    return bool(LINK_RE.search(text))


async def _delayed_delete(msg, delay=8):
    await asyncio.sleep(delay)
    try:
        await msg.delete()
    except Exception:
        pass


@app.on_message(filters.group & ~filters.service & ~filters.via_bot, group=10)
async def antilink_watcher(_, message):
    if not message.from_user or message.from_user.is_bot:
        return
    if not await _enabled(message.chat.id):
        return
    if not _has_link(message):
        return
    if await _is_admin(message.chat.id, message.from_user.id):
        return
    try:
        await message.delete()
    except Exception:
        return  # delete right nahi hai
    name = message.from_user.first_name or "Dost"
    warn = await message.reply_text(
        f"⚠️ <a href='tg://user?id={message.from_user.id}'>{name}</a>, is group me link bhejna allowed nahi hai."
    )
    asyncio.create_task(_delayed_delete(warn))


__MODULE__ = "Aɴᴛɪʟɪɴᴋ"
__HELP__ = """
**Antilink (link delete):**

• `/antilink on`: Group me links delete hone lagenge (admins chhod ke).
• `/antilink off`: Band karo.
• `/antilink`: Abhi ka status dekho.

Bot ko group me "Delete messages" ka admin right dena zaroori hai.
"""
