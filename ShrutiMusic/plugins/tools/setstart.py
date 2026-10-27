"""Owner-only, MongoDB-backed /setstart welcome editor."""
import asyncio
import html
import ipaddress
import io
import logging
import socket
import uuid

from PIL import Image, UnidentifiedImageError
from urllib.parse import urljoin, urlparse

import aiohttp
from pyrogram import enums, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ShrutiMusic import app
from ShrutiMusic.core.mongo import mongodb
from ShrutiMusic.utils.startsettings import get_start_settings, reset_start_settings, save_start_settings

OWNER_ID = getattr(config, "OWNER_ID", 0)
MAX_CAPTION = 1024
MAX_IMAGE_BYTES = 5 * 1024 * 1024
MAX_IMAGE_DIMENSION = 10_000
MAX_IMAGE_PIXELS = 40_000_000
MAX_REDIRECTS = 3
LOGGER = logging.getLogger(__name__)
_drafts = {}
_locks = {}
_IMAGE_FORMATS = {"JPEG", "PNG", "GIF", "WEBP"}


def _validate_image_bytes(data):
    """Validate downloaded bytes using Pillow, not filenames or HTTP headers."""
    if not isinstance(data, (bytes, bytearray)) or not data:
        raise ValueError("The image download was empty.")
    if len(data) > MAX_IMAGE_BYTES:
        raise ValueError("Image is too large (maximum 5 MB).")
    try:
        with Image.open(io.BytesIO(data)) as image:
            image_format = (image.format or "").upper()
            width, height = image.size
            if image_format not in _IMAGE_FORMATS:
                raise ValueError("Supported formats are JPEG, PNG, GIF and WebP.")
            if width < 1 or height < 1 or width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
                raise ValueError("Image dimensions are invalid or too large.")
            if width * height > MAX_IMAGE_PIXELS:
                raise ValueError("Image resolution is too large.")
            image.verify()
        return image_format
    except ValueError:
        raise
    except (UnidentifiedImageError, OSError, SyntaxError) as exc:
        raise ValueError("The file is not a valid, complete image.") from exc


def _downloaded_bytes(downloaded):
    if downloaded is None:
        raise RuntimeError("Telegram returned no downloaded file.")
    if isinstance(downloaded, (bytes, bytearray)):
        return bytes(downloaded)
    if hasattr(downloaded, "getvalue"):
        return downloaded.getvalue()
    if hasattr(downloaded, "read"):
        downloaded.seek(0)
        return downloaded.read(MAX_IMAGE_BYTES + 1)
    raise RuntimeError("Telegram returned an unsupported download object.")


def _is_owner(user_id):
    return isinstance(OWNER_ID, int) and OWNER_ID > 0 and user_id == OWNER_ID


def _new_token():
    return uuid.uuid4().hex[:10]


def _caption_length(text):
    # Telegram entity offsets/limits use UTF-16 code units, including emoji.
    return len(text.encode("utf-16-le")) // 2


def _rotate(draft):
    draft["token"] = _new_token()


def _menu(draft, note=None):
    prefix = f"ss:{draft['token']}:"
    rows = [
        [InlineKeyboardButton("✏️ Set Welcome Text", callback_data=prefix + "text"),
         InlineKeyboardButton("🖼 Set Welcome Image", callback_data=prefix + "image")],
        [InlineKeyboardButton("👀 Preview Welcome Message", callback_data=prefix + "preview")],
        [InlineKeyboardButton("💾 Save Changes", callback_data=prefix + "save"),
         InlineKeyboardButton("✖️ Cancel Changes", callback_data=prefix + "cancel")],
        [InlineKeyboardButton("♻️ Reset to Default", callback_data=prefix + "reset")],
    ]
    status = (f"\n\nDraft: text {'custom' if draft.get('caption') else 'default'}, "
              f"image {'custom' if draft.get('photo') else 'default'}.")
    if draft.get("mode") == "text":
        status += "\nSend the new caption as a message. HTML formatting is supported."
    elif draft.get("mode") == "image":
        status += "\nSend a Telegram photo or a direct HTTPS image URL."
    if note:
        status += "\n\n" + note
    return "⚙️ <b>Yuvika Music — Start Welcome Settings</b>" + status, InlineKeyboardMarkup(rows)


async def _show_menu(chat_id, draft, note=None, message=None):
    text, markup = _menu(draft, note)
    if message:
        try:
            await message.edit_text(text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)
            return
        except Exception:
            pass
    await app.send_message(chat_id, text, reply_markup=markup, parse_mode=enums.ParseMode.HTML)


async def _safe_public_https(url):
    parsed = urlparse(url)
    if parsed.scheme.lower() != "https" or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError("Please send a direct HTTPS image URL.")
    if parsed.port not in (None, 443):
        raise ValueError("Only standard HTTPS image URLs are allowed.")
    host = parsed.hostname.rstrip(".")
    if not host or host.lower() in {"localhost", "localhost.localdomain"}:
        raise ValueError("That image host is not allowed.")
    try:
        addresses = [ipaddress.ip_address(host)]
    except ValueError:
        try:
            records = await asyncio.get_running_loop().getaddrinfo(host, 443, type=socket.SOCK_STREAM)
            addresses = [ipaddress.ip_address(record[4][0]) for record in records]
        except Exception as exc:
            raise ValueError("Could not resolve that image host.") from exc
    if not addresses or any(not address.is_global for address in addresses):
        raise ValueError("Private or non-public image hosts are not allowed.")


async def _download_image(url):
    timeout = aiohttp.ClientTimeout(total=12, connect=4, sock_read=5)
    current = url
    async with aiohttp.ClientSession(timeout=timeout, trust_env=False) as session:
        for redirect in range(MAX_REDIRECTS + 1):
            await _safe_public_https(current)
            async with session.get(current, allow_redirects=False) as response:
                if response.status in (301, 302, 303, 307, 308):
                    location = response.headers.get("Location")
                    if not location or redirect >= MAX_REDIRECTS:
                        raise ValueError("Image URL has too many redirects or an invalid redirect.")
                    current = urljoin(current, location)
                    continue
                if response.status != 200:
                    raise ValueError(f"Image server returned HTTP {response.status}.")
                # Content-Type is advisory: validate the bytes below so valid images
                # served as application/octet-stream work, while HTML is still rejected.
                length = response.headers.get("Content-Length")
                if length:
                    try:
                        if int(length) > MAX_IMAGE_BYTES:
                            raise ValueError("Image is too large (maximum 5 MB).")
                    except ValueError as exc:
                        if "too large" in str(exc):
                            raise
                        raise ValueError("Image server returned an invalid content length.") from exc
                data = bytearray()
                async for chunk in response.content.iter_chunked(65536):
                    data.extend(chunk)
                    if len(data) > MAX_IMAGE_BYTES:
                        raise ValueError("Image is too large (maximum 5 MB).")
                image = bytes(data)
                _validate_image_bytes(image)
                return image
    raise ValueError("Could not retrieve that image.")


async def _photo_file_id_from_bytes(data, image_format):
    _validate_image_bytes(data)
    suffix = {"JPEG": ".jpg", "PNG": ".png", "GIF": ".gif", "WEBP": ".webp"}[image_format]
    stream = io.BytesIO(data)
    stream.name = "welcome-image" + suffix
    uploaded = await app.send_photo(OWNER_ID, photo=stream)
    try:
        if not uploaded.photo:
            raise RuntimeError("Telegram did not return a photo after upload.")
        return uploaded.photo[-1].file_id
    finally:
        try:
            await uploaded.delete()
        except Exception as exc:
            LOGGER.warning("setstart temporary image cleanup failed; exception_type=%s", type(exc).__name__)


async def _photo_file_id_from_url(url):
    data = await _download_image(url)
    image_format = _validate_image_bytes(data)
    return await _photo_file_id_from_bytes(data, image_format)


def _render_caption(template, first_name="there"):
    if not template:
        return None
    return (template.replace("{first_name}", html.escape(first_name or "there"))
            .replace("{bot_name}", html.escape("Yuvika Music"))
            .replace("{username}", html.escape("Yuvikamusic_bot")))


async def _preview(draft):
    photo = draft.get("photo") or config.START_IMG_URL
    caption = _render_caption(draft.get("caption"))
    if not caption:
        try:
            from ShrutiMusic.utils import bot_sys_stats
            from ShrutiMusic.utils.database import get_lang
            from strings import get_string

            owner = await app.get_users(OWNER_ID)
            up, cpu, ram, disk = await bot_sys_stats()
            strings = get_string(await get_lang(OWNER_ID))
            caption = strings["start_2"].format(owner.mention, app.mention, up, disk, cpu, ram)
        except Exception:
            caption = "🎶 <b>Yuvika Music</b>\\n\\nThis is the default welcome preview."
    await app.send_photo(OWNER_ID, photo=photo, caption=caption, parse_mode=enums.ParseMode.HTML)

async def _load_draft():
    active = await get_start_settings()
    draft = {"token": _new_token(), "caption": active.get("caption"),
             "photo": active.get("photo"), "mode": None, "initialized": True}
    _drafts[OWNER_ID] = draft
    return draft


@app.on_message(filters.command("setstart"))
async def setstart_command(_, message: Message):
    if not isinstance(OWNER_ID, int) or OWNER_ID <= 0:
        return await message.reply_text("⚠️ Configure a valid positive OWNER_ID in Render environment variables, then restart the service.")
    if not message.from_user or not _is_owner(message.from_user.id):
        return await message.reply_text("⛔ This command is available to the configured bot owner only.")
    try:
        draft = _drafts.get(OWNER_ID)
        if draft is None:
            draft = await _load_draft()
        if message.chat.id != OWNER_ID:
            await message.reply_text("📩 Welcome editor sent to your private chat. Open the bot and press Start if needed.")
            return await _show_menu(OWNER_ID, draft)
        await _show_menu(OWNER_ID, draft)
    except Exception:
        await message.reply_text("⚠️ Open @Yuvikamusic_bot in private and press Start, then retry /setstart.")


@app.on_callback_query(filters.regex(r"^ss:"))
async def setstart_callback(_, query):
    if not query.from_user or not _is_owner(query.from_user.id):
        return await query.answer("⛔ Owner only.", show_alert=True)
    if not query.message or query.message.chat.id != OWNER_ID:
        return await query.answer("⛔ Use the private owner menu.", show_alert=True)
    parts = (query.data or "").split(":")
    if len(parts) != 3:
        return await query.answer("Invalid button. Open /setstart again.", show_alert=True)
    _, token, action = parts
    draft = _drafts.get(OWNER_ID)
    if not draft or draft.get("token") != token:
        return await query.answer("This menu is old. Open /setstart again.", show_alert=True)
    await query.answer()
    lock = _locks.setdefault(OWNER_ID, asyncio.Lock())
    async with lock:
        # Re-check after acquiring the lock so two simultaneous callbacks cannot reuse a stale draft.
        if _drafts.get(OWNER_ID) is not draft or draft.get("token") != token:
            return
        if action in {"text", "image"}:
            draft["mode"] = action
            _rotate(draft)
            return await _show_menu(OWNER_ID, draft, message=query.message)
        if action == "preview":
            try:
                await _preview(draft)
                note = "Preview sent above; live welcome is unchanged."
            except Exception:
                note = "Preview failed. Check the caption formatting or image and try again."
            _rotate(draft)
            return await _show_menu(OWNER_ID, draft, note, query.message)
        if action == "cancel":
            fresh = await _load_draft()
            return await _show_menu(OWNER_ID, fresh, "Draft discarded. Live settings were not changed.", query.message)
        if action == "save":
            try:
                caption = draft.get("caption")
                if caption and _caption_length(caption) > MAX_CAPTION:
                    raise ValueError("Welcome caption exceeds Telegram's 1024-character photo caption limit.")
                if caption:
                    await app.parser.parse(caption, enums.ParseMode.HTML)
                await save_start_settings(caption, draft.get("photo"))
                fresh = await _load_draft()
                return await _show_menu(OWNER_ID, fresh, "✅ Changes saved. Future /start messages will use this welcome.", query.message)
            except ValueError as exc:
                _rotate(draft)
                return await _show_menu(OWNER_ID, draft, "❌ " + html.escape(str(exc)), query.message)
            except Exception:
                _rotate(draft)
                return await _show_menu(OWNER_ID, draft, "❌ Save failed. Previous settings remain active.", query.message)
        if action == "reset":
            _rotate(draft)
            prefix = f"ss:{draft['token']}:"
            keyboard = InlineKeyboardMarkup([
                [InlineKeyboardButton("✅ Confirm Reset", callback_data=prefix + "confirmreset"),
                 InlineKeyboardButton("↩️ Keep Current", callback_data=prefix + "keepreset")]
            ])
            return await query.message.edit_text(
                "⚠️ <b>Reset welcome to the original default text and image?</b>\nThis affects future /start responses only.",
                reply_markup=keyboard, parse_mode=enums.ParseMode.HTML)
        if action == "confirmreset":
            await reset_start_settings()
            fresh = {"token": _new_token(), "caption": None, "photo": None, "mode": None, "initialized": True}
            _drafts[OWNER_ID] = fresh
            return await _show_menu(OWNER_ID, fresh, "✅ Reset complete. Original default welcome is active.", query.message)
        if action == "keepreset":
            _rotate(draft)
            return await _show_menu(OWNER_ID, draft, "Reset cancelled; no settings changed.", query.message)


@app.on_message(filters.private & filters.user(OWNER_ID) & (filters.text | filters.photo | filters.document), group=10)
async def setstart_collect_input(_, message: Message):
    if not message.from_user or not _is_owner(message.from_user.id):
        return
    draft = _drafts.get(OWNER_ID)
    if not draft or not draft.get("mode"):
        return
    lock = _locks.setdefault(OWNER_ID, asyncio.Lock())
    async with lock:
        if draft["mode"] == "text":
            if not message.text or message.text.startswith("/"):
                return await message.reply_text("Send the welcome caption as text/HTML, not as a command.")
            if _caption_length(message.text) > MAX_CAPTION:
                return await message.reply_text("❌ Caption too long. Telegram photo captions allow up to 1024 characters.")
            try:
                await app.parser.parse(message.text, enums.ParseMode.HTML)
            except Exception:
                return await message.reply_text("❌ Invalid HTML. Close every tag and try again.")
            draft["caption"] = message.text
            draft["mode"] = None
            _rotate(draft)
            return await _show_menu(OWNER_ID, draft, "✅ Draft text updated. Preview it before saving.")
        if draft["mode"] == "image":
            stage = "detect_input"
            try:
                if message.photo:
                    media = message.photo[-1]  # Pyrogram lists photo sizes smallest to largest.
                    if media.file_size and media.file_size > MAX_IMAGE_BYTES:
                        raise ValueError("Image is too large (maximum 5 MB).")
                    stage = "download_telegram_photo"
                    downloaded = await app.download_media(message, in_memory=True)
                    data = _downloaded_bytes(downloaded)
                    stage = "validate_telegram_photo"
                    _validate_image_bytes(data)
                    photo_id = media.file_id
                elif message.document:
                    media = message.document
                    if media.file_size and media.file_size > MAX_IMAGE_BYTES:
                        raise ValueError("Image is too large (maximum 5 MB).")
                    stage = "download_telegram_document"
                    downloaded = await app.download_media(message, in_memory=True)
                    data = _downloaded_bytes(downloaded)
                    stage = "validate_telegram_document"
                    image_format = _validate_image_bytes(data)
                    stage = "upload_document_as_photo"
                    photo_id = await _photo_file_id_from_bytes(data, image_format)
                elif message.text and not message.text.startswith("/"):
                    stage = "download_https_url"
                    photo_id = await _photo_file_id_from_url(message.text.strip())
                else:
                    return await message.reply_text("Send a Telegram photo, an image document, or a direct HTTPS image URL.")
            except ValueError as exc:
                LOGGER.warning("setstart image rejected; stage=%s exception_type=%s", stage, type(exc).__name__)
                return await message.reply_text("❌ " + str(exc))
            except Exception as exc:
                LOGGER.error("setstart image input failed; stage=%s exception_type=%s", stage, type(exc).__name__)
                return await message.reply_text("❌ Image processing failed at the %s stage (%s). The previous draft image is unchanged." % (stage, type(exc).__name__))

            # Commit only after the input has been downloaded and validated. The active
            # welcome remains unchanged until Save Changes is pressed.
            if _drafts.get(OWNER_ID) is not draft or not _is_owner(message.from_user.id):
                return await message.reply_text("⚠️ This editor session is no longer active. Reopen /setstart.")
            draft["photo"] = photo_id
            draft["mode"] = None
            _rotate(draft)
            try:
                return await _show_menu(OWNER_ID, draft, "✅ Draft image updated. Preview it before saving.")
            except Exception as exc:
                LOGGER.error("setstart image confirmation failed; stage=render_confirmation exception_type=%s", type(exc).__name__)
                return await message.reply_text("✅ Image validated and added to the draft. Reopen /setstart to continue; live welcome is unchanged.")
