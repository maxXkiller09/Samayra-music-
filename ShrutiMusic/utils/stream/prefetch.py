"""Background prefetch for the next queued YouTube track.

Only the immediate next track is prepared, keeping memory and disk use modest
for small hosts such as Render Free Web Service.
"""

import asyncio

from config import autoclean
from ShrutiMusic.misc import db
from ShrutiMusic.utils.stream.queue_files import replace_tracked_queue_item

_TASKS = {}


async def _prefetch_item(chat_id, item):
    key = (chat_id, id(item))
    old_file = item.get("file")
    message = None
    try:
        if not isinstance(old_file, str) or not old_file.startswith("vid_"):
            return
        videoid = item.get("vidid")
        if not videoid:
            return

        from ShrutiMusic import YouTube, app

        message = await app.send_message(
            item.get("chat_id") or chat_id,
            "⚡ Preparing the next track…",
        )
        file_path, _direct = await YouTube.download(
            videoid,
            message,
            videoid=True,
            video=str(item.get("streamtype")) == "video",
        )
        if not file_path:
            return

        current_queue = db.get(chat_id) or []
        replace_tracked_queue_item(
            current_queue, autoclean, item, old_file, file_path
        )
    except asyncio.CancelledError:
        raise
    except Exception as exc:
        print(f"[prefetch] chat={chat_id} failed: {type(exc).__name__}: {exc}")
    finally:
        if message is not None:
            try:
                await message.delete()
            except Exception:
                pass
        if _TASKS.get(key) is asyncio.current_task():
            _TASKS.pop(key, None)


def schedule_next_prefetch(chat_id):
    """Start preparing queue[1] if it is a deferred YouTube item."""
    queue = db.get(chat_id) or []
    if len(queue) < 2:
        return None
    item = queue[1]
    file_path = item.get("file")
    if not isinstance(file_path, str) or not file_path.startswith("vid_"):
        return None

    key = (chat_id, id(item))
    task = _TASKS.get(key)
    if task and not task.done():
        return task
    task = asyncio.create_task(_prefetch_item(chat_id, item))
    _TASKS[key] = task
    return task


async def wait_for_prefetch(chat_id, item):
    """Wait only when this exact queue item already has a prefetch in progress."""
    task = _TASKS.get((chat_id, id(item)))
    if task and task is not asyncio.current_task():
        try:
            await asyncio.shield(task)
        except asyncio.CancelledError:
            raise
        except Exception:
            pass
