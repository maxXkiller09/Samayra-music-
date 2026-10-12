import asyncio
import os
import re
from typing import Union
import yt_dlp
from pyrogram.enums import MessageEntityType
from pyrogram.types import Message
from py_yt import VideosSearch, Playlist
import aiohttp

# ---------------------------------------------------------------------------
# Generic downloader API (koi bhi API chalegi, sirf .env / Render env me set karo)
#
#   BASE_API_URL   -> API ka base url, e.g. https://api.example.com (API_URL naam bhi chalega)
#   BASE_API_KEY   -> API key (API_KEY naam bhi chalega; key na lage to khali chhod do)
#
# Optional (sirf tab badlo jab tumhari API ka format alag ho):
#   API_ENDPOINT    -> default "/download"
#   API_URL_PARAM   -> video id/link ka param name, default "url"
#   API_TYPE_PARAM  -> audio/video ka param name, default "type" (khali = mat bhejo)
#   API_KEY_PARAM   -> key ka param name, default "api_key" (khali = query me mat bhejo)
#   API_KEY_HEADER  -> agar key header me jaati hai, e.g. "x-api-key" ya "Authorization"
#   API_KEY_PREFIX  -> header value ke aage prefix, e.g. "Bearer "
#   API_SEND_FULL_URL -> "true" to video id ki jagah full youtube link bhejo
#   API_AUDIO_VALUE / API_VIDEO_VALUE -> type param ki values, default "audio" / "video"
#   API_EXTRA_PARAMS  -> extra query params, e.g. "quality=128&format=mp3"
#
# Purane naam (SHRUTI_API_URL / SHRUTI_API_KEY) bhi abhi kaam karenge.
# ---------------------------------------------------------------------------
def _env(name, default=""):
    value = os.environ.get(name)
    return value.strip() if value and value.strip() else default


API_URL = (_env("BASE_API_URL") or _env("API_URL") or _env("SHRUTI_API_URL")).rstrip("/")
API_KEY = _env("BASE_API_KEY") or _env("API_KEY") or _env("SHRUTI_API_KEY")
API_ENDPOINT = _env("API_ENDPOINT", "/download")
API_URL_PARAM = _env("API_URL_PARAM", "url")
API_TYPE_PARAM = os.environ.get("API_TYPE_PARAM", "type").strip()
API_KEY_PARAM = os.environ.get("API_KEY_PARAM", "api_key").strip()
API_KEY_HEADER = _env("API_KEY_HEADER")
API_KEY_PREFIX = os.environ.get("API_KEY_PREFIX", "")
API_SEND_FULL_URL = _env("API_SEND_FULL_URL", "false").lower() in ("1", "true", "yes")
API_AUDIO_VALUE = _env("API_AUDIO_VALUE", "audio")
API_VIDEO_VALUE = _env("API_VIDEO_VALUE", "video")
API_EXTRA_PARAMS = _env("API_EXTRA_PARAMS")

DOWNLOAD_DIR = "downloads"

_LINK_KEYS = (
    "download_url", "downloadUrl", "download_link", "downloadLink", "download",
    "url", "link", "audio_url", "video_url", "audio", "video", "file", "stream_url",
)


def time_to_seconds(time):
    stringt = str(time)
    return sum(int(x) * 60 ** i for i, x in enumerate(reversed(stringt.split(":"))))


def _extract_video_id(link: str) -> str:
    if "v=" in link:
        return link.split("v=")[-1].split("&")[0]
    if "youtu.be/" in link:
        return link.split("youtu.be/")[-1].split("?")[0].split("&")[0]
    return link


def _find_link(data):
    """JSON response ke andar se download link dhundta hai (nested bhi)."""
    if isinstance(data, str):
        return data if data.startswith("http") else None
    if isinstance(data, dict):
        for key in _LINK_KEYS:
            if key in data:
                found = _find_link(data[key])
                if found:
                    return found
        for value in data.values():
            if isinstance(value, (dict, list)):
                found = _find_link(value)
                if found:
                    return found
    if isinstance(data, list):
        for item in data:
            found = _find_link(item)
            if found:
                return found
    return None


async def _save_stream(resp, file_path: str) -> bool:
    with open(file_path, "wb") as f:
        async for chunk in resp.content.iter_chunked(131072):
            f.write(chunk)
    return os.path.exists(file_path) and os.path.getsize(file_path) > 0


async def _api_download(link: str, media: str, ext: str, timeout: int):
    video_id = _extract_video_id(link)
    if not video_id or len(video_id) < 3:
        return None

    os.makedirs(DOWNLOAD_DIR, exist_ok=True)
    file_path = os.path.join(DOWNLOAD_DIR, f"{video_id}.{ext}")
    if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
        return file_path

    if not API_URL:
        print("[API] BASE_API_URL set nahi hai")
        return None

    params = {}
    if API_EXTRA_PARAMS:
        params.update(dict(p.split("=", 1) for p in API_EXTRA_PARAMS.split("&") if "=" in p))
    params[API_URL_PARAM] = (
        f"https://www.youtube.com/watch?v={video_id}" if API_SEND_FULL_URL else video_id
    )
    if API_TYPE_PARAM:
        params[API_TYPE_PARAM] = API_VIDEO_VALUE if media == "video" else API_AUDIO_VALUE
    headers = {}
    if API_KEY:
        if API_KEY_PARAM:
            params[API_KEY_PARAM] = API_KEY
        if API_KEY_HEADER:
            headers[API_KEY_HEADER] = f"{API_KEY_PREFIX}{API_KEY}"

    endpoint = API_ENDPOINT if API_ENDPOINT.startswith("/") else "/" + API_ENDPOINT
    request_timeout = aiohttp.ClientTimeout(total=timeout)

    try:
        async with aiohttp.ClientSession(headers=headers) as session:
            async with session.get(
                f"{API_URL}{endpoint}", params=params, timeout=request_timeout
            ) as resp:
                if resp.status != 200:
                    print(f"[API] status {resp.status} from {API_URL}{endpoint}")
                    return None
                content_type = (resp.headers.get("Content-Type") or "").lower()
                if "json" not in content_type and "text/html" not in content_type:
                    # API seedha file bhejti hai (Shruti style)
                    if await _save_stream(resp, file_path):
                        return file_path
                    return None
                # API JSON me link deti hai -> link nikaal ke download karo
                try:
                    data = await resp.json(content_type=None)
                except Exception as je:
                    print(f"[API] json error: {je}")
                    return None
            print(f"[API] json response: {str(data)[:300]}")
            file_url = _find_link(data)
            if not file_url:
                print("[API] response me download link nahi mila")
                return None
            async with session.get(file_url, timeout=request_timeout) as file_resp:
                if file_resp.status != 200:
                    print(f"[API] file status {file_resp.status}")
                    return None
                if await _save_stream(file_resp, file_path):
                    return file_path
        return None
    except Exception as ae:
        print(f"[API] exception: {type(ae).__name__}: {ae}")
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
        return None


async def download_song(link: str) -> str:
    return await _api_download(link, "audio", "mp3", 300)


async def download_video(link: str) -> str:
    return await _api_download(link, "video", "mp4", 600)


class YouTubeAPI:
    def __init__(self):
        self.base = "https://www.youtube.com/watch?v="
        self.regex = r"(?:youtube\.com|youtu\.be)"
        self.status = "https://www.youtube.com/oembed?url="
        self.listbase = "https://youtube.com/playlist?list="
        self.reg = re.compile(r"\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])")

    async def exists(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        return bool(re.search(self.regex, link))

    async def url(self, message_1: Message) -> Union[str, None]:
        messages = [message_1]
        if message_1.reply_to_message:
            messages.append(message_1.reply_to_message)
        for message in messages:
            if message.entities:
                for entity in message.entities:
                    if entity.type == MessageEntityType.URL:
                        text = message.text or message.caption
                        return text[entity.offset: entity.offset + entity.length]
            elif message.caption_entities:
                for entity in message.caption_entities:
                    if entity.type == MessageEntityType.TEXT_LINK:
                        return entity.url
        return None

    async def details(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
            vidid = result["id"]
            duration_sec = int(time_to_seconds(duration_min)) if duration_min else 0
        return title, duration_min, duration_sec, thumbnail, vidid

    async def title(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["title"]

    async def duration(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["duration"]

    async def thumbnail(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            return result["thumbnails"][0]["url"].split("?")[0]

    async def video(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            downloaded_file = await download_video(link)
            if downloaded_file:
                return 1, downloaded_file
            return 0, "Video download failed"
        except Exception as e:
            return 0, f"Video download error: {e}"

    async def playlist(self, link, limit, user_id, videoid: Union[bool, str] = None):
        if videoid:
            link = self.listbase + link
        if "&" in link:
            link = link.split("&")[0]
        try:
            plist = await Playlist.get(link)
        except Exception:
            return []
        videos = plist.get("videos") or []
        ids = []
        for data in videos[:limit]:
            if not data:
                continue
            vid = data.get("id")
            if not vid:
                continue
            ids.append(vid)
        return ids

    async def track(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        results = VideosSearch(link, limit=1)
        for result in (await results.next())["result"]:
            title = result["title"]
            duration_min = result["duration"]
            vidid = result["id"]
            yturl = result["link"]
            thumbnail = result["thumbnails"][0]["url"].split("?")[0]
        track_details = {
            "title": title,
            "link": yturl,
            "vidid": vidid,
            "duration_min": duration_min,
            "thumb": thumbnail,
        }
        return track_details, vidid

    async def formats(self, link: str, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        ytdl_opts = {"quiet": True}
        ydl = yt_dlp.YoutubeDL(ytdl_opts)
        with ydl:
            formats_available = []
            r = ydl.extract_info(link, download=False)
            for format in r["formats"]:
                try:
                    if "dash" not in str(format["format"]).lower():
                        formats_available.append(
                            {
                                "format": format["format"],
                                "filesize": format.get("filesize"),
                                "format_id": format["format_id"],
                                "ext": format["ext"],
                                "format_note": format["format_note"],
                                "yturl": link,
                            }
                        )
                except Exception:
                    continue
        return formats_available, link

    async def slider(self, link: str, query_type: int, videoid: Union[bool, str] = None):
        if videoid:
            link = self.base + link
        if "&" in link:
            link = link.split("&")[0]
        a = VideosSearch(link, limit=10)
        result = (await a.next()).get("result")
        title = result[query_type]["title"]
        duration_min = result[query_type]["duration"]
        vidid = result[query_type]["id"]
        thumbnail = result[query_type]["thumbnails"][0]["url"].split("?")[0]
        return title, duration_min, thumbnail, vidid

    async def download(
        self,
        link: str,
        mystic,
        video: Union[bool, str] = None,
        videoid: Union[bool, str] = None,
        songaudio: Union[bool, str] = None,
        songvideo: Union[bool, str] = None,
        format_id: Union[bool, str] = None,
        title: Union[bool, str] = None,
    ) -> str:
        if videoid:
            link = self.base + link
        try:
            if video:
                downloaded_file = await download_video(link)
            else:
                downloaded_file = await download_song(link)
            if downloaded_file:
                return downloaded_file, True
            return None, False
        except Exception:
            return None, False


YouTube = YouTubeAPI()
