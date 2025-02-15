from pyrogram import filters
from pyrogram.types import Message
from KOKUMUSIC.core.userbot import Userbot

userbot = Userbot()

@userbot.one.on_message(filters.command("hi") & filters.group)
async def hi_command(client, message: Message):
    try:
        # अपने अकाउंट से रिप्लाई भेजें
        await client.send_message(
            message.chat.id,
            "How are you? 😊"
        )
    except Exception as e:
        print(f"Error: {e}")
