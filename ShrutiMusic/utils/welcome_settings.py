"""Persistent owner-configurable /start image with a safe default fallback."""

from ShrutiMusic.utils.database import db


async def get_start_image(default):
    try:
        settings = await db.welcome.find_one({"_id": "start_image"})
        if settings and settings.get("photo"):
            return settings["photo"]
    except Exception:
        # A database hiccup should not prevent the /start command from working.
        pass
    return default
