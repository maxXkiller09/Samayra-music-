import asyncio
import random
import re

from ShrutiMusic.core.mongo import mongodb

autoplay_db = mongodb.autoplay
AUTOPLAY = {}  # chat_id -> bool (button ke liye sync cache)
_recent = {}  # chat_id -> pichle vidid (repeat se bachne ke liye)
_loaded = False


def autoplay_label(chat_id):
    return "ᴀᴜᴛᴏᴘʟᴀʏ: ʏᴇs" if AUTOPLAY.get(chat_id) else "ᴀᴜᴛᴏᴘʟᴀʏ: ɴᴏ"


async def load_autoplay():
    global _loaded
    try:
        async for doc in autoplay_db.find({"enabled": True}):
            AUTOPLAY[doc["chat_id"]] = True
        _loaded = True
    except Exception as e:
        print(f"[autoplay] load error: {e}")


async def set_autoplay(chat_id, value: bool):
    AUTOPLAY[chat_id] = value
    try:
        await autoplay_db.update_one(
            {"chat_id": chat_id}, {"$set": {"enabled": value}}, upsert=True
        )
    except Exception as e:
        print(f"[autoplay] save error: {e}")


def _clean_title(title):
    t = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", title or "")
    t = re.sub(r"(?i)\b(official|video|audio|lyrics?|lyrical|full|song|hd|4k|remix|mp3)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:60]


def _is_short(duration):
    """3 ghante se chhota aur 10 minute se kam wala hi chuno (mix/podcast skip)."""
    if not duration:
        return False
    parts = str(duration).split(":")
    if len(parts) != 2:
        return False
    try:
        return int(parts[0]) < 10
    except ValueError:
        return False


async def autoplay_fill(chat_id, popped):
    """Queue khatam hone par agar autoplay ON hai to milta-julta gaana queue me daal do."""
    try:
        if not popped or not AUTOPLAY.get(chat_id):
            return False
        from py_yt import VideosSearch

        from ShrutiMusic import app
        from ShrutiMusic.misc import db
        from ShrutiMusic.utils.stream.queue import put_queue

        seen = _recent.setdefault(chat_id, [])
        if popped.get("vidid"):
            seen.append(popped["vidid"])
        del seen[:-15]

        query = f"{_clean_title(popped.get('title'))} songs"
        results = (await VideosSearch(query, limit=12).next()).get("result", [])
        pool = [
            r for r in results
            if r.get("id") not in seen and _is_short(r.get("duration"))
        ]
        if not pool:
            return False
        pick = random.choice(pool[:6])

        vidid = pick["id"]
        title = pick["title"]
        duration = pick["duration"]
        seen.append(vidid)
        if chat_id not in db:
            db[chat_id] = []
        await put_queue(
            chat_id,
            popped.get("chat_id") or chat_id,
            f"vid_{vidid}",
            title,
            duration,
            f"🔁 {app.mention} (ᴀᴜᴛᴏᴘʟᴀʏ)",
            vidid,
            getattr(app, "id", 0),
            popped.get("streamtype") if popped.get("streamtype") in ("audio", "video") else "audio",
        )
        return True
    except Exception as e:
        print(f"[autoplay] fill error: {type(e).__name__}: {e}")
        return False


try:
    asyncio.get_running_loop().create_task(load_autoplay())
except RuntimeError:
    pass
