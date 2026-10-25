# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Keep the upstream attribution and license notices when modifying this file.

import ipaddress
import os
import re
import tempfile
from urllib.parse import urlparse

import aiohttp
from pyrogram import filters
from pyrogram.types import Message

from ShrutiMusic import app

API_ENDPOINT = "https://allvideodownloader.cc/wp-json/aio-dl/video-data/"
MAX_VIDEO_BYTES = int(os.environ.get("VIDEO_DOWNLOADER_MAX_BYTES", str(500 * 1024 * 1024)))


def _is_public_http_url(value: str) -> bool:
    try:
        parsed = urlparse(value)
        if parsed.scheme not in {"https", "http"} or not parsed.hostname:
            return False
        host = parsed.hostname.lower().rstrip(".")
        if host in {"localhost", "localhost.localdomain"} or host.endswith(".local"):
            return False
        try:
            return ipaddress.ip_address(host).is_global
        except ValueError:
            return True
    except (TypeError, ValueError):
        return False


def _quality_score(item: dict) -> int:
    quality = str(item.get("quality", ""))
    match = re.search(r"(\d{3,4})", quality)
    return int(match.group(1)) if match else 0


async def _download_video(url: str, token: str, file_path: str) -> str:
    api_timeout = aiohttp.ClientTimeout(total=25)
    async with aiohttp.ClientSession(timeout=api_timeout) as session:
        async with session.post(
            API_ENDPOINT,
            data={"url": url, "token": token},
            headers={"User-Agent": "SamayraMusicBot/1.0"},
            allow_redirects=False,
        ) as response:
            if response.status != 200:
                raise RuntimeError("Video provider returned an error.")
            data = await response.json(content_type=None)

        medias = data.get("medias") if isinstance(data, dict) else None
        if not isinstance(medias, list) or not medias:
            raise RuntimeError("No downloadable video was found.")

        candidates = [
            item for item in medias
            if isinstance(item, dict) and _is_public_http_url(str(item.get("url", "")))
        ]
        if not candidates:
            raise RuntimeError("Provider returned no safe video link.")

        video_url = max(candidates, key=_quality_score)["url"]
        file_timeout = aiohttp.ClientTimeout(total=120, connect=20)
        async with session.get(
            video_url,
            timeout=file_timeout,
            allow_redirects=False,
        ) as response:
            if response.status != 200:
                raise RuntimeError("Video file could not be fetched.")
            length = response.headers.get("Content-Length")
            if length and int(length) > MAX_VIDEO_BYTES:
                raise RuntimeError("Video is too large for this bot.")
            written = 0
            with open(file_path, "wb") as output:
                async for chunk in response.content.iter_chunked(128 * 1024):
                    written += len(chunk)
                    if written > MAX_VIDEO_BYTES:
                        raise RuntimeError("Video is too large for this bot.")
                    output.write(chunk)
            if written == 0:
                raise RuntimeError("The provider returned an empty file.")

        return str(data.get("title") or "Video")


@app.on_message(filters.command(["vid"]))
async def video_downloader(_, message: Message):
    if len(message.command) < 2:
        return await message.reply_text(
            "❌ Please provide a video URL.\n\nExample: /vid https://example.com/video"
        )

    video_url = message.text.split(None, 1)[1].strip()
    if not _is_public_http_url(video_url):
        return await message.reply_text("❌ Please provide a valid public HTTP(S) video URL.")

    token = os.environ.get("VIDEO_DOWNLOADER_TOKEN", "").strip()
    if not token:
        return await message.reply_text(
            "⚙️ Video downloader is not configured yet. Music playback is unaffected."
        )

    status = await message.reply_text("🔍 Fetching video...")
    temp_path = None
    try:
        with tempfile.NamedTemporaryFile(prefix="samayra-video-", suffix=".mp4", delete=False) as temp:
            temp_path = temp.name

        await status.edit_text("⬇️ Downloading video...")
        title = await _download_video(video_url, token, temp_path)
        await app.send_video(
            chat_id=message.chat.id,
            video=temp_path,
            caption=f"🎬 {title[:900]}",
            supports_streaming=True,
            reply_to_message_id=message.id,
        )
        await status.delete()
    except Exception as exc:
        # Keep provider URLs, tokens, and internal exception details out of chat.
        error = str(exc)
        if error in {
            "Video provider returned an error.",
            "No downloadable video was found.",
            "Provider returned no safe video link.",
            "Video file could not be fetched.",
            "Video is too large for this bot.",
            "The provider returned an empty file.",
        }:
            message_text = f"❌ {error}"
        else:
            message_text = "❌ Download failed. Please try another public video URL later."
        try:
            await status.edit_text(message_text)
        except Exception:
            pass
    finally:
        if temp_path and os.path.exists(temp_path):
            try:
                os.remove(temp_path)
            except OSError:
                pass


# ©️ Copyright Reserved - @NoxxOP Nand Yaduwanshi
# Original project: https://github.com/NoxxOP/ShrutiMusic
