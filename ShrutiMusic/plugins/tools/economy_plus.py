import html
import random
import time

from pyrogram import filters

from ShrutiMusic import app
from ShrutiMusic.plugins.tools.lovebirds import get_user_data, users_collection

PREFIX = ["/", "!", "."]
DAY = 86400


def _fmt_time(sec):
    h, rem = divmod(int(sec), 3600)
    m, _ = divmod(rem, 60)
    return f"{h} ghante {m} minute"


@app.on_message(filters.command("daily", prefixes=PREFIX))
async def daily_bonus(_, message):
    if not message.from_user:
        return
    uid = message.from_user.id
    data = await get_user_data(uid)
    now = int(time.time())
    last = int(data.get("last_daily", 0) or 0)

    if last and now - last < DAY:
        left = DAY - (now - last)
        return await message.reply_text(
            f"⏳ Aaj ka bonus le chuke ho. Agla bonus <b>{_fmt_time(left)}</b> baad milega."
        )

    streak = int(data.get("daily_streak", 0) or 0)
    streak = streak + 1 if last and now - last < 2 * DAY else 1
    reward = random.randint(20, 50) + min(streak, 7) * 5

    await users_collection.update_one(
        {"user_id": uid},
        {"$inc": {"coins": reward}, "$set": {"last_daily": now, "daily_streak": streak}},
        upsert=True,
    )
    await message.reply_text(
        f"🎁 <b>Daily Bonus!</b>\n\n💰 Tumhe mile: <b>{reward}</b> coins\n🔥 Streak: <b>{streak}</b> din\n\n"
        "Kal wapas aana, streak badhne pe bonus bhi badhta hai!"
    )


async def _resolve_target(client, message, parts):
    if message.reply_to_message and message.reply_to_message.from_user:
        return message.reply_to_message.from_user, parts[1:]
    if len(parts) >= 2:
        ref = parts[1].lstrip("@")
        try:
            user = await client.get_users(int(ref) if ref.isdigit() else ref)
            return user, parts[2:]
        except Exception:
            return None, parts[2:]
    return None, parts[1:]


@app.on_message(filters.command(["pay", "send"], prefixes=PREFIX) & filters.group)
async def pay_coins(client, message):
    if not message.from_user:
        return
    parts = message.text.split()
    target, rest = await _resolve_target(client, message, parts)
    if not target or not rest or not rest[0].isdigit():
        return await message.reply_text(
            "❌ <b>Aise use karo:</b>\nKisi ke message pe reply karke <code>/pay 50</code>\nYa <code>/pay @username 50</code>"
        )

    amount = int(rest[0])
    if amount < 1:
        return await message.reply_text("❌ Amount kam se kam 1 hona chahiye.")
    if target.id == message.from_user.id:
        return await message.reply_text("😅 Khud ko coins bhejne ka koi faayda nahi.")
    if target.is_bot:
        return await message.reply_text("🤖 Bot ko coins nahi bhej sakte.")

    await get_user_data(message.from_user.id)
    fee = amount // 20  # 5%
    result = await users_collection.update_one(
        {"user_id": message.from_user.id, "coins": {"$gte": amount}},
        {"$inc": {"coins": -amount}},
    )
    if result.modified_count == 0:
        return await message.reply_text("💸 Tumhare paas itne coins nahi hain.")

    await users_collection.update_one(
        {"user_id": target.id}, {"$inc": {"coins": amount - fee}}, upsert=True
    )
    name = html.escape(target.first_name or "Dost")
    await message.reply_text(
        f"✅ <b>{amount - fee}</b> coins <a href='tg://user?id={target.id}'>{name}</a> ko bhej diye.\n"
        f"🧾 Fee (5%): {fee} coins"
    )


__MODULE__ = "Eᴄᴏɴᴏᴍʏ+"
__HELP__ = """
**Coins ke extra commands:**

• `/daily`: Roz ka bonus lo. Roz aane pe streak badhta hai aur bonus bhi.
• `/pay [amount]`: Kisi ke message pe reply karke coins bhejo (5% fee).
• `/pay @username [amount]`: Username se coins bhejo.

Balance dekhne ke liye `/balance`, top log dekhne ke liye `/top`.
"""
