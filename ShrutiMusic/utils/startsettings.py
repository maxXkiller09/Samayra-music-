"""MongoDB persistence and small cache for the global /start welcome."""
import asyncio

from ShrutiMusic.core.mongo import mongodb

_collection = mongodb.start_settings
_cache = None
_lock = asyncio.Lock()


async def get_start_settings():
    global _cache
    if _cache is not None:
        return dict(_cache)
    async with _lock:
        if _cache is None:
            try:
                document = await _collection.find_one({"_id": "global"})
                _cache = {
                    "caption": document.get("caption") if document else None,
                    "photo": document.get("photo") if document else None,
                }
            except Exception:
                _cache = {"caption": None, "photo": None}
        return dict(_cache)


async def save_start_settings(caption, photo):
    global _cache
    async with _lock:
        await _collection.update_one(
            {"_id": "global"},
            {"$set": {"caption": caption, "photo": photo}},
            upsert=True,
        )
        _cache = {"caption": caption, "photo": photo}


async def reset_start_settings():
    global _cache
    async with _lock:
        await _collection.delete_one({"_id": "global"})
        _cache = {"caption": None, "photo": None}
