import asyncio
import re

from ShrutiMusic.core.mongo import mongodb

autoplay_db = mongodb.autoplay
AUTOPLAY = {}  # chat_id -> bool (button ke liye sync cache)
_recent = {}  # chat_id -> recently seen source IDs
_recent_identity = {}  # chat_id -> bounded canonical identities
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
    t = re.sub(r"[\(\[\{].*?[\)\]\}]", " ", title or "")
    t = re.sub(r"(?i)\b(official|video|audio|lyrics?|lyrical|full|song|hd|4k|mp3)\b", " ", t)
    return re.sub(r"\s+", " ", t).strip()[:80]


def _tokens(text):
    return set(re.findall(r"[a-z0-9]+", (text or "").lower()))


def _moods(text):
    words = _tokens(text)
    return {mood for mood, hints in _MOOD_WORDS.items() if words & hints}


def _artist_hint(title):
    """Use an explicit 'artist - track' title prefix when available."""
    parts = re.split(r"\s[-–—]\s", _clean_title(title), maxsplit=1)
    return parts[0].strip() if len(parts) == 2 and parts[0].strip() else ""


_VERSION_RE = re.compile(
    r"(?i)\\b(remix|slowed|sped[ -]?up|speed[ -]?up|reverb|live|acoustic|"
    r"instrumental|karaoke|cover|nightcore|8d|visuali[sz]er|extended mix|"
    r"radio edit|club mix|lofi version)\\b"
)
_UPLOAD_NOISE_RE = re.compile(
    r"(?i)\\b(official|video|audio|lyrics?|lyrical|full|hd|4k|mp3|"
    r"visuali[sz]er|topic|uploaded)\\b"
)


def _is_alternate_version(title):
    """Reject uploads explicitly labelled as a remix/alternate recording."""
    return bool(_VERSION_RE.search(title or ""))


def _canonical_identity(title, artist=None):
    """Build a lightweight identity robust to upload labels and title formatting."""
    raw = title or ""
    # Remove only known version/upload labels; preserve meaningful title words.
    raw = _VERSION_RE.sub(" ", raw)
    raw = _UPLOAD_NOISE_RE.sub(" ", raw)
    raw = re.sub(r"[\\[\\]{}()]", " ", raw)
    raw = re.sub(r"[^a-zA-Z0-9\\u0900-\\u097F]+", " ", raw).lower()
    title_tokens = set(re.findall(r"[a-z0-9\\u0900-\\u097f]+", raw))
    if artist:
        artist_raw = _UPLOAD_NOISE_RE.sub(" ", artist or "")
        artist_tokens = set(re.findall(r"[a-z0-9\\u0900-\\u097f]+", artist_raw.lower()))
        # Include an artist signal only when known, but allow artist/title ordering differences.
        if artist_tokens:
            title_tokens |= artist_tokens
    return " ".join(sorted(title_tokens))


def _candidate_artist(candidate):
    channel = candidate.get("channel")
    if isinstance(channel, dict):
        return channel.get("name") or ""
    return str(channel or candidate.get("artist") or "")


def _language_hint(title):
    words = _tokens(title)
    if words & {"punjabi", "bhangra", "gurbani", "sidhu", "diljit", "shubh"}:
        return "Punjabi"
    if words & {"hindi", "bollywood", "arijit", "shreya", "kishore", "lata"}:
        return "Hindi"
    return ""


def _search_queries(current_title):
    """Use a few bounded, distinct searches rather than one title-only query."""
    moods = _moods(current_title)
    language = _language_hint(current_title)
    mood_phrases = {
        "sad": "sad heartbreak emotional songs",
        "romantic": "romantic love songs",
        "party": "energetic party dance songs",
        "devotional": "devotional bhajan songs",
        "lofi": "chill lofi mellow songs",
        "rap": "rap hip hop songs",
    }
    mood_phrase = next((mood_phrases[m] for m in ("romantic", "party", "sad", "devotional", "lofi", "rap") if m in moods), "")
    base = f"songs like {_clean_title(current_title)} similar vibe"
    if mood_phrase:
        base = f"{base} {mood_phrase}"
    queries = [base]
    if mood_phrase:
        queries.append(" ".join(part for part in (mood_phrase, language, "songs similar vibe") if part))
    artist = _artist_hint(current_title)
    if artist:
        queries.append(" ".join(part for part in ("songs by artists similar to", artist, language, mood_phrase) if part))
    else:
        queries.append(" ".join(part for part in ("different songs with a similar vibe", language, mood_phrase) if part))
    # Stable de-duplication and hard cap keep external load predictable.
    return list(dict.fromkeys(q.strip() for q in queries if q.strip()))[:3]


def _candidate_is_duplicate(current_title, candidate, queued_identities, recent_identities):
    title = candidate.get("title") or ""
    if not title or _is_alternate_version(title):
        return True
    identity = _canonical_identity(title, _artist_hint(title))
    current_identity = _canonical_identity(current_title, _artist_hint(current_title))
    if identity and identity == current_identity:
        return True
    if identity and (identity in queued_identities or identity in recent_identities):
        return True
    return False


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
    """Rank different tracks by vibe cues; never reward same-artist repetition."""
    title = candidate.get("title") or ""
    current_identity = _canonical_identity(current_title, _artist_hint(current_title))
    candidate_identity = _canonical_identity(title, _candidate_artist(candidate))
    if not candidate_identity or candidate_identity == current_identity or _is_alternate_version(title):
        return -100

    current_words = _tokens(_clean_title(current_title))
    candidate_words = _tokens(_clean_title(title))
    shared = current_words & candidate_words
    generic = {"the", "and", "song", "songs", "official", "video", "audio", "lyrics"}
    score = min(len(shared - generic), 2)
    current_moods = _moods(current_title)
    candidate_moods = _moods(title)
    if current_moods and candidate_moods:
        score += 5 if current_moods & candidate_moods else -3
    language = _language_hint(current_title)
    if language and language.lower() in title.lower():
        score += 2
    artist = _artist_hint(current_title)
    candidate_artist = _artist_hint(title)
    if artist and candidate_artist and artist.casefold() == candidate_artist.casefold():
        score -= 2
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
        recent_identities = _recent_identity.setdefault(chat_id, [])
        if popped.get("vidid"):
            seen.append(popped["vidid"])
        current_title = _clean_title(popped.get("title"))
        current_identity = _canonical_identity(current_title, _artist_hint(current_title))
        if current_identity:
            recent_identities.append(current_identity)
        del seen[:-30]
        del recent_identities[:-30]

        if not current_title:
            return False

        # Exclude anything already queued, including same-song uploads with a
        # different YouTube ID. Manual requests remain untouched; this applies
        # only to autoplay recommendations.
        current_queue = db.get(chat_id) or []
        queued_ids = {str(item.get("vidid")) for item in current_queue if item.get("vidid")}
        queued_identities = {
            _canonical_identity(item.get("title", ""), _artist_hint(item.get("title", "")))
            for item in current_queue
            if item.get("title")
        }
        queries = _search_queries(current_title)

        async def _fetch(query):
            try:
                response = await asyncio.wait_for(VideosSearch(query, limit=10).next(), timeout=9)
                return response.get("result", [])
            except Exception as exc:
                print(f"[autoplay] search failed: {type(exc).__name__}")
                return []

        # Three bounded strategies run concurrently; no AI/API/model is needed.
        batches = await asyncio.gather(*(_fetch(query) for query in queries))
        results = []
        ids = set()
        for batch in batches:
            for item in batch:
                vidid = str(item.get("id") or "")
                if vidid and vidid not in ids:
                    ids.add(vidid)
                    results.append(item)
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
            and str(item.get("id")) not in seen
            and str(item.get("id")) not in queued_ids
            and _is_short(item.get("duration"))
            and not _candidate_is_duplicate(
                current_title, item, queued_identities, set(recent_identities)
            )
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
