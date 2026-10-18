import html
import time

from pyrogram import filters

from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb

history_db = mongodb.play_history
PLAY_COMMANDS = [
    "play", "vplay", "cplay", "cvplay",
    "playforce", "vplayforce", "cplayforce", "cvplayforce",
]
KEEP = 50


@app.on_message(filters.command(PLAY_COMMANDS, prefixes=["/", "!", "."]) & filters.group, group=7)
async def log_play(_, message):
    try:
        if not message.from_user:
            return
        query = None
        if len(message.command) > 1:
            query = message.text.split(None, 1)[1].strip()
        elif message.reply_to_message:
            r = message.reply_to_message
            media = r.audio or r.video
            if media:
                query = (getattr(media, "title", None) or getattr(media, "file_name", None) or "Telegram file")
        if not query:
            return
        await history_db.insert_one(
            {
                "chat_id": message.chat.id,
                "user_id": message.from_user.id,
                "name": message.from_user.first_name or "User",
                "query": query[:150],
                "ts": int(time.time()),
            }
        )
        count = await history_db.count_documents({"chat_id": message.chat.id})
        if count > KEEP:
            old = history_db.find({"chat_id": message.chat.id}).sort("ts", 1).limit(count - KEEP)
            ids = [d["_id"] async for d in old]
            if ids:
                await history_db.delete_many({"_id": {"$in": ids}})
    except Exception as e:
        print(f"[history] {type(e).__name__}: {e}")


@app.on_message(filters.command(["history", "recent"], prefixes=["/", "!", "."]) & filters.group)
async def show_history(_, message):
    docs = [d async for d in history_db.find({"chat_id": message.chat.id}).sort("ts", -1).limit(10)]
    if not docs:
        return await message.reply_text("📭 Is group me abhi koi play history nahi hai.")
    lines = []
    for i, d in enumerate(docs, 1):
        lines.append(f"{i}. <b>{html.escape(d['query'])}</b>  —  <i>{html.escape(d['name'])}</i>")
    await message.reply_text("🕘 <b>Is group ke last 10 gaane:</b>\n\n" + "\n".join(lines))


__MODULE__ = "Hɪsᴛᴏʀʏ"
__HELP__ = """
**Play history:**

• `/history`: Is group me last 10 baar kaun sa gaana play kiya gaya, aur kisne.
"""
