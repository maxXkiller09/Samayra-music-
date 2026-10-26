import asyncio
import re

from ShrutiMusic.core.mongo import mongodb

autoplay_db = mongodb.autoplay
AUTOPLAY = {}  # chat_id -> bool (button ke liye sync cache)
_recent = {}  # chat_id -> pichle vidid (repeat se bachne ke liye)
_loaded = False

# Lightweight mood hints from titles; no extra API or model call required.
_MOOD_WORDS = {
    "sad": {"sad", "heartbreak", "broken", "bewafa", "dard", "rona", "alone", "cry"},
    "romantic": {"love", "romantic", "romance", "ishq", "pyaar", "mohabbat", "jaan"},
    "party": {"party", "dance", "club", "dj", "dance", "nach", "bhangra"},
    "devotional": {"bhajan", "bhakti", "devotional", "aarti", "mantra", "shiv", "krishna"},
    "lofi": {"lofi", "slowed", "reverb", "chill", "relax", "lo-fi"},
    "rap": {"rap", "rapper", "hiphop", "hip-hop", "drill", "diss"},
}


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
    t = re.sub(r"[\\(\\[\\{].*?[\\)\\]\\}]", " ", title or "")
    t = re.sub(r"(?i)\\b(official|video|audio|lyrics?|lyrical|full|song|hd|4k|mp3)\\b", " ", t)
    return re.sub(r"\\s+", " ", t).strip()[:80]


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _moods(text):
    words = _tokens(text)
    return {mood for mood, hints in _MOOD_WORDS.items() if words & hints}


def _artist_hint(title):
    """Use an explicit 'artist - track' title prefix when available."""
    parts = re.split(r"\\s[-–—]\\s", _clean_title(title), maxsplit=1)
    return parts[0].strip() if len(parts) == 2 and parts[0].strip() else ""


def _score_candidate(current_title, candidate):
    """Rank results by mood/artist/word overlap and penalize near-duplicates."""
    title = candidate.get("title") or ""
    current = _clean_title(current_title).lower()
    candidate_clean = _clean_title(title).lower()
    if not candidate_clean or candidate_clean == current:
        return -100

    current_words = _tokens(current)
    candidate_words = _tokens(candidate_clean)
    shared = current_words & candidate_words
    # Generic words are weak evidence; mood and artist hints matter more.
    generic = {"the", "and", "song", "songs", "official", "video", "audio", "lyrics"}
    score = min(len(shared - generic), 4)
    current_moods = _moods(current_title)
    candidate_moods = _moods(title)
    if current_moods and candidate_moods:
        score += 5 if current_moods & candidate_moods else -3
    artist = _artist_hint(current_title)
    if artist and artist.lower() in title.lower():
        score += 3
    duration = str(candidate.get("duration") or "")
    if not duration or len(duration.split(":")) != 2:
        score -= 8
    return score


def _is_short(duration):
    """Keep normal tracks under 10 minutes; skip mixes and podcasts."""
    if not duration:
        return False
    parts = str(duration).split(":")
    if len(parts) != 2:
        return False
    try:
        minutes, seconds = (int(part) for part in parts)
        return 0 <= minutes < 10 and 0 <= seconds < 60
    except ValueError:
        return False


async def autoplay_fill(chat_id, popped):
    """Queue a relevant next track when the queue ends and autoplay is enabled."""
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
        del seen[:-20]

        current_title = _clean_title(popped.get("title"))
        if not current_title:
            return False
        # One focused query keeps end-of-track lookup lightweight. Rank the
        # returned pool locally instead of choosing an arbitrary first result.
        query = f"songs like {current_title} similar vibe"
        results = (await VideosSearch(query, limit=15).next()).get("result", [])
        pool = [
            item for item in results
            if item.get("id")
            and item.get("id") not in seen
            and _is_short(item.get("duration"))
        ]
        if not pool:
            return False
        pick = max(pool, key=lambda item: _score_candidate(current_title, item))
        if _score_candidate(current_title, pick) < -5:
            return False

        vidid = pick["id"]
        title = pick["title"]
        duration = pick["duration"]
        seen.append(vidid)
        del seen[:-20]
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
