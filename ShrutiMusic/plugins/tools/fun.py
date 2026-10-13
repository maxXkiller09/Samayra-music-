# Copyright (c) 2025 Nand Yaduwanshi <NoxxOP>
# Location: Supaul, Bihar
#
# All rights reserved.
#
# This code is the intellectual property of Nand Yaduwanshi.
# You are not allowed to copy, modify, redistribute, or use this
# code for commercial or personal projects without explicit permission.
#
# Allowed:
# - Forking for personal learning
# - Submitting improvements via pull requests
#
# Not Allowed:
# - Claiming this code as your own
# - Re-uploading without credit or permission
# - Selling or using commercially
#
# Contact for permissions:
# Email: badboy809075@gmail.com


import random
from pyrogram import filters
from pyrogram.types import Message

from ShrutiMusic import app


@app.on_message(
    filters.command(
        [
            "dice",
            "ludo",
            "dart",
            "basket",
            "basketball",
            "football",
            "slot",
            "bowling",
            "jackpot",
        ]
    )
)
async def dice(c, m: Message):
    command = m.text.split()[0]
    if command == "/dice" or command == "/ludo":

        value = await c.send_dice(m.chat.id, reply_to_message_id=m.id)
        await value.reply_text("Tumhara score hai {0} 🎯".format(value.dice.value))

    elif command == "/dart":

        value = await c.send_dice(m.chat.id, emoji="🎯", reply_to_message_id=m.id)
        await value.reply_text("Tumhara score hai {0} 🎯".format(value.dice.value))

    elif command == "/basket" or command == "/basketball":
        basket = await c.send_dice(m.chat.id, emoji="🏀", reply_to_message_id=m.id)
        await basket.reply_text("Tumhara score hai {0} 🎯".format(basket.dice.value))

    elif command == "/football":
        value = await c.send_dice(m.chat.id, emoji="⚽", reply_to_message_id=m.id)
        await value.reply_text("Tumhara score hai {0} 🎯".format(value.dice.value))

    elif command == "/slot" or command == "/jackpot":
        value = await c.send_dice(m.chat.id, emoji="🎰", reply_to_message_id=m.id)
        await value.reply_text("Tumhara score hai {0} 🎯".format(value.dice.value))
    elif command == "/bowling":
        value = await c.send_dice(m.chat.id, emoji="🎳", reply_to_message_id=m.id)
        await value.reply_text("Tumhara score hai {0} 🎯".format(value.dice.value))


BORED_ACTIVITIES = [
    "Apne kisi purane dost ko call karo aur hal chaal poocho.",
    "Ek naya gaana dhundo aur group me share karo.",
    "10 minute ki walk pe nikal jao.",
    "Apna room saaf karo, mood fresh ho jayega.",
    "Koi nayi recipe try karo aaj.",
    "Ek chhoti si diary likhna shuru karo.",
    "Koi purani movie dekho jo bahut din se dekhni thi.",
    "Chai ya coffee banao aur aaram se piyo.",
    "Apni gallery ki purani photos dekho aur unme se best group me bhejo.",
    "Ek naya skill seekhne ke liye YouTube pe tutorial dekho.",
    "Dost ke saath group me /truth ya /dare khelo.",
    "Apne favourite gaane pe 5 minute dance karo.",
    "Kisi ko ek achha sa compliment bhejo.",
    "Ek book ke 10 page padho.",
    "Paani peeyo aur thoda stretching karo.",
]


@app.on_message(filters.command("bored", prefixes="/"))
async def bored_command(client, message):
    activity = random.choice(BORED_ACTIVITIES)
    await message.reply(f"😴 Bore ho rahe ho? Ye try karo:\n\n{activity}")


__MODULE__ = "Fᴜɴ"
__HELP__ = """
**Masti ke commands:**

• `/dice`: Dice roll karo.
• `/ludo`: Ludo ka dice phenko.
• `/dart`: Dart phenko.
• `/basket` ya `/basketball`: Basketball khelo.
• `/football`: Football khelo.
• `/slot` ya `/jackpot`: Jackpot khelo.
• `/bowling`: Bowling khelo.
• `/bored`: Bore ho rahe ho to koi idea lo.
"""
