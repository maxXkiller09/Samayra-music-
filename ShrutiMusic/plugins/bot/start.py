import time

from pyrogram import filters
from pyrogram.enums import ChatType
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from py_yt import VideosSearch
import config
from ShrutiMusic import app
from ShrutiMusic.misc import _boot_
from ShrutiMusic.plugins.sudo.sudoers import sudoers_list
from ShrutiMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from ShrutiMusic.utils import bot_sys_stats
from ShrutiMusic.utils.decorators.language import LanguageStart
from ShrutiMusic.utils.formatters import get_readable_time
from ShrutiMusic.utils.inline import help_pannel_page1, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string


async def _reply_welcome_photo(message, photo, caption, reply_markup):
    """Send the selected welcome image, falling back safely if a stored file_id expires."""
    kwargs = {"caption": caption, "reply_markup": reply_markup}
    try:
        return await message.reply_photo(
            photo=photo, message_effect_id=5159385139981059251, **kwargs
        )
    except Exception:
        try:
            return await message.reply_photo(photo=photo, **kwargs)
        except Exception:
            if not photo or photo == config.START_IMG_URL:
                raise
            try:
                result = await message.reply_photo(
                    photo=config.START_IMG_URL,
                    message_effect_id=5159385139981059251,
                    **kwargs,
                )
            except Exception:
                result = await message.reply_photo(photo=config.START_IMG_URL, **kwargs)
            owner_id = getattr(config, "OWNER_ID", 0)
            if isinstance(owner_id, int) and owner_id > 0:
                try:
                    await app.send_message(
                        owner_id,
                        "⚠️ The saved Yuvika Music welcome image could not be sent. "
                        "Use /setstart → Set Welcome Image, upload a replacement, "
                        "then Preview and Save Changes.",
                    )
                except Exception:
                    pass
            return result


async def _welcome_payload(message, default_caption):
    """Resolve custom global welcome settings, falling back to the existing caption."""
    import html
    from ShrutiMusic.utils.startsettings import get_start_settings
    try:
        settings = await get_start_settings()
    except Exception:
        settings = {"caption": None, "photo": None}
    photo = settings.get("photo") or config.START_IMG_URL
    caption = settings.get("caption")
    if caption:
        first_name = message.from_user.first_name if message.from_user else "there"
        caption = (caption.replace("{first_name}", html.escape(first_name or "there"))
                   .replace("{bot_name}", html.escape("Yuvika Music"))
                   .replace("{username}", html.escape("Yuvikamusic_bot")))
    else:
        caption = default_caption
    return photo, caption


@app.on_message(filters.command(["start"]) & filters.private & ~BANNED_USERS)
@LanguageStart
async def start_pm(client, message: Message, _):
    await add_served_user(message.from_user.id)
    if len(message.text.split()) > 1:
        name = message.text.split(None, 1)[1]
        if name[0:4] == "help":
            keyboard = help_pannel_page1(_)
            try:
                return await message.reply_photo(
                    photo=config.START_IMG_URL,
                    caption=_["help_1"].format(config.SUPPORT_GROUP),
                    reply_markup=keyboard,
                    message_effect_id=5159385139981059251,
                )
            except:
                return await message.reply_photo(
                    photo=config.START_IMG_URL,
                    caption=_["help_1"].format(config.SUPPORT_GROUP),
                    reply_markup=keyboard,
                )
        if name[0:3] == "sud":
            await sudoers_list(client=client, message=message, _=_)
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>sᴜᴅᴏʟɪsᴛ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
            return
        if name[0:3] == "inf":
            m = await message.reply_text("🔎")
            query = (str(name)).replace("info_", "", 1)
            query = f"https://www.youtube.com/watch?v={query}"
            results = VideosSearch(query, limit=1)
            for result in (await results.next())["result"]:
                title = result["title"]
                duration = result["duration"]
                views = result["viewCount"]["short"]
                thumbnail = result["thumbnails"][0]["url"].split("?")[0]
                channellink = result["channel"]["link"]
                channel = result["channel"]["name"]
                link = result["link"]
                published = result["publishedTime"]
            searched_text = _["start_6"].format(
                title, duration, views, published, channellink, channel, app.mention
            )
            key = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text=_["S_B_8"], url=link),
                        InlineKeyboardButton(text=_["S_B_9"], url=config.SUPPORT_GROUP),
                    ],
                ]
            )
            await m.delete()
            try:
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=searched_text,
                    reply_markup=key,
                    message_effect_id=5159385139981059251,
                )
            except:
                await app.send_photo(
                    chat_id=message.chat.id,
                    photo=thumbnail,
                    caption=searched_text,
                    reply_markup=key,
                )
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ ᴛᴏ ᴄʜᴇᴄᴋ <b>ᴛʀᴀᴄᴋ ɪɴғᴏʀᴍᴀᴛɪᴏɴ</b>.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
        if name == "start":
            out = private_panel(_)
            UP, CPU, RAM, DISK = await bot_sys_stats()
            default_caption = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM)
            welcome_photo, welcome_caption = await _welcome_payload(message, default_caption)
            await _reply_welcome_photo(
                message, welcome_photo, welcome_caption, InlineKeyboardMarkup(out)
            )
            if await is_on_off(2):
                return await app.send_message(
                    chat_id=config.LOG_GROUP_ID,
                    text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
                )
    else:
        out = private_panel(_)
        UP, CPU, RAM, DISK = await bot_sys_stats()
        default_caption = _["start_2"].format(message.from_user.mention, app.mention, UP, DISK, CPU, RAM)
        welcome_photo, welcome_caption = await _welcome_payload(message, default_caption)
        await _reply_welcome_photo(
            message, welcome_photo, welcome_caption, InlineKeyboardMarkup(out)
        )
        if await is_on_off(2):
            return await app.send_message(
                chat_id=config.LOG_GROUP_ID,
                text=f"{message.from_user.mention} ᴊᴜsᴛ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ʙᴏᴛ.\n\n<b>ᴜsᴇʀ ɪᴅ :</b> <code>{message.from_user.id}</code>\n<b>ᴜsᴇʀɴᴀᴍᴇ :</b> @{message.from_user.username}",
            )


@app.on_message(filters.command(["start"]) & filters.group & ~BANNED_USERS)
@LanguageStart
async def start_gp(client, message: Message, _):
    out = start_panel(_)
    uptime = int(time.time() - _boot_)
    default_caption = _["start_1"].format(app.mention, get_readable_time(uptime))
    welcome_photo, welcome_caption = await _welcome_payload(message, default_caption)
    try:
        await message.reply_photo(
            photo=welcome_photo,
            caption=welcome_caption,
            reply_markup=InlineKeyboardMarkup(out),
            message_effect_id=5159385139981059251,
        )
    except:
        await message.reply_photo(
            photo=welcome_photo,
            caption=welcome_caption,
            reply_markup=InlineKeyboardMarkup(out),
        )
    return await add_served_chat(message.chat.id)


@app.on_message(filters.new_chat_members, group=-1)
async def welcome(client, message: Message):
    for member in message.new_chat_members:
        try:
            language = await get_lang(message.chat.id)
            _ = get_string(language)
            if await is_banned_user(member.id):
                try:
                    await message.chat.ban_member(member.id)
                except:
                    pass
            if member.id == app.id:
                if message.chat.type != ChatType.SUPERGROUP:
                    await message.reply_text(_["start_4"])
                    return await app.leave_chat(message.chat.id)
                if message.chat.id in await blacklisted_chats():
                    await message.reply_text(
                        _["start_5"].format(
                            app.mention,
                            f"https://t.me/{app.username}?start=sudolist",
                            config.SUPPORT_GROUP,
                        ),
                        disable_web_page_preview=True,
                    )
                    return await app.leave_chat(message.chat.id)

                out = start_panel(_)
                default_caption = _["start_3"].format(
                    message.from_user.first_name, app.mention, message.chat.title, app.mention
                )
                welcome_photo, welcome_caption = await _welcome_payload(message, default_caption)
                await _reply_welcome_photo(
                    message, welcome_photo, welcome_caption, InlineKeyboardMarkup(out)
                )
                await add_served_chat(message.chat.id)
                await message.stop_propagation()
        except Exception as ex:
            print(ex)
