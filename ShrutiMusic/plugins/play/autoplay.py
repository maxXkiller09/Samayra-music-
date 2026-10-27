from pyrogram import filters
from pyrogram.enums import ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from ShrutiMusic import app
from ShrutiMusic.misc import SUDOERS
import asyncio

from ShrutiMusic.utils.autoplay import (
    AUTOPLAY,
    autoplay_label,
    load_autoplay,
    schedule_autoplay_fill,
    set_autoplay,
)
from ShrutiMusic.utils.autoplay_commands import parse_autoplay_action


try:
    asyncio.get_running_loop().create_task(load_autoplay())
except RuntimeError:
    pass


async def _can_toggle(chat_id, user_id):
    if user_id in SUDOERS:
        return True
    try:
        member = await app.get_chat_member(chat_id, user_id)
        return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)
    except Exception:
        return False


@app.on_callback_query(filters.regex(r"^AUTOPLAY "))
async def autoplay_callback(_, query):
    try:
        chat_id = int(query.data.split(None, 1)[1])
    except Exception:
        return await query.answer()

    if not await _can_toggle(chat_id, query.from_user.id):
        return await query.answer("Sirf admins autoplay badal sakte hain.", show_alert=True)

    new_value = not AUTOPLAY.get(chat_id, False)
    await set_autoplay(chat_id, new_value)
    await query.answer("Autoplay ON ✅ — queue khatam hone par milta-julta gaana bajega." if new_value else "Autoplay OFF.", show_alert=False)

    # isi message ke button ko update karo
    try:
        rows = []
        for row in query.message.reply_markup.inline_keyboard:
            new_row = []
            for b in row:
                if b.callback_data and b.callback_data.startswith("AUTOPLAY "):
                    new_row.append(InlineKeyboardButton(text=autoplay_label(chat_id), callback_data=b.callback_data))
                else:
                    new_row.append(b)
            rows.append(new_row)
        await query.message.edit_reply_markup(InlineKeyboardMarkup(rows))
    except Exception:
        pass


@app.on_message(filters.command("autoplay") & filters.group)
async def autoplay_command(_, message):
    if not message.from_user or not await _can_toggle(message.chat.id, message.from_user.id):
        return await message.reply_text("❌ Ye command sirf group admins ke liye hai.")
    chat_id = message.chat.id
    action = parse_autoplay_action(message.command[1:])
    if action == "invalid":
        return await message.reply_text(
            "Use: /autoplay on, /autoplay off, /autoplay status, or /autoplay next."
        )

    if action == "status":
        value = bool(AUTOPLAY.get(chat_id, False))
        return await message.reply_text(
            "🔁 Autoplay <b>ON</b> ✅" if value else "🔁 Autoplay <b>OFF</b>."
        )

    if action == "next":
        if not AUTOPLAY.get(chat_id, False):
            return await message.reply_text("Autoplay OFF hai. Pehle /autoplay on karo.")
        from ShrutiMusic.misc import db

        queue = db.get(chat_id) or []
        if not queue:
            return await message.reply_text("Pehle /play se ek track start karo.")
        if len(queue) > 1:
            return await message.reply_text(
                "Queue mein next track pehle se hai; autoplay usse replace nahi karega."
            )
        task = schedule_autoplay_fill(chat_id, queue[0])
        if task is None:
            return await message.reply_text("Similar track search abhi start nahi ho saki.")
        return await message.reply_text(
            "🔎 Similar-vibe track background mein search ho raha hai. Milne par queue mein add hoga."
        )

    if action in ("on", "off"):
        value = action == "on"
    else:
        value = not AUTOPLAY.get(chat_id, False)
    await set_autoplay(chat_id, value)
    await message.reply_text(
        "🔁 Autoplay <b>ON</b> ✅\nQueue khatam hone par milta-julta gaana apne aap bajega."
        if value
        else "🔁 Autoplay <b>OFF</b>."
    )


__MODULE__ = "Aᴜᴛᴏᴘʟᴀʏ"
__HELP__ = """
**Autoplay:**

• Gaane ke message me **AUTOPLAY** button dabao, ya `/autoplay on` / `/autoplay off` likho.
• ON hone par queue khatam hote hi milta-julta gaana apne aap bajta rehta hai.
• Sirf group admins badal sakte hain.
"""
