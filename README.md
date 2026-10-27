# Yuvika Music 🎧

A Telegram group music bot for voice-chat playback, queues, playlists, and audio/video streaming.

**Bot:** [@Yuvikamusic_bot](https://t.me/Yuvikamusic_bot)  
**Hosting target:** Render Free Web Service  
**Repository:** https://github.com/maxXkiller09/Samayra-music-

## Features

- Play tracks in Telegram group voice chats
- Queue management, skip, pause, resume, stop, and playback controls
- Audio and video playback paths
- YouTube URL validation and bounded downloads
- Queue recovery when a track fails, so later tracks can continue
- Health endpoint at `/health` for Render service checks

Playback depends on Telegram credentials, valid assistant session strings, MongoDB connectivity, and a group voice chat that the assistant account can access. The health endpoint confirms the web listener is responding; it does **not** prove that Telegram playback or MongoDB is healthy.

## Render deployment

This repository includes `render.yaml` for a Docker-based Render **Free Web Service**. Review the service settings and environment variables in the Render dashboard before deploying.

Set the required secrets in Render's Environment section. Do not paste credentials into source files or commit a `.env` file.

Important configuration:
- `API_ID` and `API_HASH`: Telegram application credentials
- `BOT_TOKEN`: token from BotFather
- `OWNER_ID`: numeric Telegram user ID of the bot owner
- `MONGO_DB_URI`: MongoDB connection string
- `LOG_GROUP_ID`: numeric Telegram log group ID
- `STRING_SESSION` and any additional `STRING_SESSION2`–`STRING_SESSION5` values used by your chosen assistant setup. Each configured slot must use a distinct session string; do not reuse the same string across slots or run the same assistant session on multiple live services at once. Startup now rejects exact duplicate strings without printing their values.
- `BASE_API_URL` and `VIDEO_DOWNLOADER_TOKEN`: only if the related download integration is configured
- `SHRUTI_API_KEY`: only if the related API integration is used

Keep secrets in Render's environment settings. If any token or session string was ever committed to Git history, rotate it; removing a file from the latest revision does not erase old Git history.

## Local checks

The repository's GitHub Actions workflow checks Python syntax, shell syntax, dependencies, and regression tests. Passing CI does not replace a live test of bot startup, MongoDB, Telegram voice-chat access, and actual playback.

## Upstream credit

Yuvika Music is based on the ShrutiMusic project by [NoxxOP](https://github.com/NoxxOP). Upstream attribution and the repository's license are retained; please review the [LICENSE](LICENSE) before redistributing or using the code.

