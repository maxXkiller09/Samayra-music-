import asyncio
import re

from ShrutiMusic.core.mongo import mongodb

autoplay_db = mongodb.autoplay
AUTOPLAY = {}  # chat_id -> bool (button ke liye sync cache)
_recent = {}  # chat_id -> pichle vidid (repeat se bachne ke liye)
_loaded = False
_fill_tasks = {}  # chat_id -> active recommendation search task

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
    if not value:
        # Stop wasting search/download-related work once autoplay is disabled.
        # Remove the slot first so a quick re-enable can schedule a fresh task.
        task = _fill_tasks.pop(chat_id, None)
        if task and not task.done():
            task.cancel()
    try:
        await autoplay_db.update_one(
            {"chat_id": chat_id}, {"$set": {"enabled": value}}, upsert=True
        )
    except Exception as e:
        print(f"[autoplay] save error: {e}")
    if value:
        try:
            from ShrutiMusic.misc import db

            queue = db.get(chat_id) or []
            if len(queue) == 1:
                schedule_autoplay_fill(chat_id, queue[0])
        except Exception as e:
            print(f"[autoplay] prefill schedule error: {type(e).__name__}: {e}")


def _clean_title(title):
    # Normalize upload labels and common alternate versions so autoplay does
    # not mistake a slowed/reverb/cover upload of the same song for a new track.
    t = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", title or "")
    t = re.sub(
        r"(?i)\b(official|video|audio|lyrics?|lyrical|full|song|hd|4k|mp3|"
        r"slowed|reverb|remix|remaster(?:ed)?|cover|karaoke|instrumental|"
        r"lofi|lo-fi|sped[ -]?up|nightcore|unplugged|reprise|version|status|"
        r"bass boosted|extended|loop)\b",
        " ",
        t,
    )
    return re.sub(r"\s+", " ", t).strip()[:80]


def _track_core(title, split_artist=True):
    """Prefer the track portion of 'artist - track' titles when both titles use it."""
    cleaned = _clean_title(title).lower()
    parts = re.split(r"\s[-–—]\s", cleaned, maxsplit=1) if split_artist else []
    track = parts[1] if len(parts) == 2 and parts[1].strip() else cleaned
    return _tokens(track)


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _moods(text):
    words = _tokens(text)
    return {mood for mood, hints in _MOOD_WORDS.items() if words & hints}


def _artist_hint(title):
    """Use an explicit 'artist - track' title prefix when available."""
    parts = re.split(r"\s[-–—]\s", _clean_title(title), maxsplit=1)
    return parts[0].strip() if len(parts) == 2 and parts[0].strip() else ""


def _search_query(current_title):
    """Add a small mood hint when the current title clearly signals a vibe."""
    mood_terms = {
        "sad": "sad heartbreak songs",
        "romantic": "romantic love songs",
        "party": "party dance songs",
        "devotional": "devotional songs",
        "lofi": "lofi chill songs",
        "rap": "rap hip hop songs",
    }
    moods = _moods(current_title)
    hint = next((mood_terms[mood] for mood in mood_terms if mood in moods), "")
    query = f"songs like {_clean_title(current_title)} similar vibe"
    return f"{query} {hint}".strip()


def _score_candidate(current_title, candidate):
    """Rank results by mood/artist/word overlap and penalize near-duplicates."""
    title = candidate.get("title") or ""
    current = _clean_title(current_title).lower()
    candidate_clean = _clean_title(title).lower()
    if not candidate_clean or candidate_clean == current:
        return -100

    current_words = _tokens(current)
    candidate_words = _tokens(candidate_clean)
    # Reject alternate uploads of the same underlying track, even when titles
    # add labels such as "slowed", "Brahmastra", or "female version".
    has_artist_prefix = bool(re.search(r"\s[-–—]\s", current))
    current_core = _track_core(current_title, split_artist=has_artist_prefix)
    candidate_core = _track_core(title, split_artist=has_artist_prefix)
    core_overlap = current_core & candidate_core
    if current_core and (
        current_core <= candidate_core
        or len(core_overlap) / max(1, len(current_core)) >= 0.8
    ):
        return -100

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


async def _autoplay_fill_impl(chat_id, popped, proactive=False):
    """Find and queue a relevant track, optionally while the current track plays."""
    try:
        if not popped or not AUTOPLAY.get(chat_id):
            return False
        from py_yt import VideosSearch

        from ShrutiMusic import app
        from ShrutiMusic.misc import db
        from ShrutiMusic.utils.stream.queue import put_queue

        current_queue = db.get(chat_id) or []
        if proactive:
            if len(current_queue) != 1 or current_queue[0] is not popped:
                return False
        elif current_queue:
            return False

        seen = _recent.setdefault(chat_id, [])
        if popped.get("vidid"):
            seen.append(popped["vidid"])
        del seen[:-20]

        current_title = _clean_title(popped.get("title"))
        if not current_title:
            return False
        # One focused query keeps end-of-track lookup lightweight. Rank the
        # returned pool locally instead of choosing an arbitrary first result.
        query = _search_query(current_title)
        # Never let a slow search hold the voice chat at the end of the queue.
        # If YouTube search stalls, autoplay safely gives up and playback can end.
        results = (
            await asyncio.wait_for(VideosSearch(query, limit=15).next(), timeout=12)
        ).get("result", [])
        # If the current song ended while search was running, allow the result
        # only while the voice chat is still active and no manual track replaced it.
        current_queue = db.get(chat_id) or []
        if proactive:
            if current_queue and not (
                len(current_queue) == 1 and current_queue[0] is popped
            ):
                return False
            if not current_queue:
                from ShrutiMusic.utils.database import is_active_chat

                if not await is_active_chat(chat_id):
                    return False
        elif current_queue:
            return False
        if not AUTOPLAY.get(chat_id):
            return False
        pool = [
            item for item in results
            if item.get("id")
            and item.get("id") not in seen
            and _is_short(item.get("duration"))
        ]
        if not pool:
            return False
        ranked = sorted(
            pool, key=lambda item: _score_candidate(current_title, item), reverse=True
        )
        # A score below 1 means there is no meaningful mood, artist, or title
        # overlap. The previous -5 cutoff admitted almost every valid-duration
        # result, including unrelated tracks returned by broad YouTube searches.
        pick = ranked[0]
        if _score_candidate(current_title, pick) < 1:
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


def _clear_fill_task(chat_id, task):
    if _fill_tasks.get(chat_id) is task:
        _fill_tasks.pop(chat_id, None)


def _reschedule_if_track_changed(chat_id, attempted_track, _task):
    """Restart proactive search if a different sole queue item replaced this track."""
    if not AUTOPLAY.get(chat_id):
        return
    try:
        from ShrutiMusic.misc import db

        queue = db.get(chat_id) or []
        if len(queue) == 1 and queue[0] is not attempted_track:
            schedule_autoplay_fill(chat_id, queue[0])
    except Exception as exc:
        print(f"[autoplay] reschedule error: {type(exc).__name__}: {exc}")


def schedule_autoplay_fill(chat_id, current_track):
    """Start finding one similar song early, while the current track is playing."""
    if not current_track or not AUTOPLAY.get(chat_id):
        return None
    existing = _fill_tasks.get(chat_id)
    if existing and not existing.done():
        return existing
    task = asyncio.create_task(
        _autoplay_fill_impl(chat_id, current_track, proactive=True)
    )
    _fill_tasks[chat_id] = task
    task.add_done_callback(lambda done: _clear_fill_task(chat_id, done))
    task.add_done_callback(
        lambda done: _reschedule_if_track_changed(chat_id, current_track, done)
    )
    return task


async def autoplay_fill(chat_id, popped):
    """At queue end, wait for an early recommendation or perform a fallback search."""
    existing = _fill_tasks.get(chat_id)
    if existing and existing is not asyncio.current_task():
        try:
            # The proactive search should normally finish while the current
            # track is playing. At queue end, wait briefly only; never make
            # the voice chat sit silent for the full search timeout.
            if await asyncio.wait_for(asyncio.shield(existing), timeout=2):
                return True
        except asyncio.TimeoutError:
            try:
                from ShrutiMusic.misc import db

                if not db.get(chat_id):
                    return False
            except Exception:
                return False
        except Exception:
            pass
        try:
            from ShrutiMusic.misc import db

            if db.get(chat_id):
                return False
        except Exception:
            return False

    task = asyncio.create_task(_autoplay_fill_impl(chat_id, popped))
    _fill_tasks[chat_id] = task
    try:
        return await task
    finally:
        _clear_fill_task(chat_id, task)


try:
    asyncio.get_running_loop().create_task(load_autoplay())
except RuntimeError:
    pass
