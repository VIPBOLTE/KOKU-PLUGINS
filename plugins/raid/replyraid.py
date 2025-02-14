import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait

import config
# Raid Messages (कस्टमाइज करें)
RAID_MESSAGES = [
    "इधर देख! 👀",
    "छेड़ने की हिम्मत? 😡",
    "जय श्री राम! 🚩",
    "तुम्हारी औकात? 🤣"
]
app = Client(
    "my_assistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.STRING_SESSION
)

@app.on_message(filters.command("raid") & filters.private)
async def raid_assistant(client: Client, message: Message):
    try:
        # Parsing the command arguments
        args = message.text.split()
        if len(args) < 3:
            await message.reply_text("**Usage:**\n`!raid [count] [username]`")
            return

        count = int(args[1])
        target = args[2]

        # Start the raid
        for _ in range(count):
            try:
                await client.send_message(
                    target,
                    random.choice(RAID_MESSAGES)
                )
                await asyncio.sleep(random.uniform(0.5, 1.5))  # Anti-flood delay
            except FloodWait as e:
                await asyncio.sleep(e.value + 5)  # Handle FloodWait

        # Delete the original message and send the reply
        await message.delete()  # Await delete
        await message.reply_text(f"✅ {count} रैड मैसेज भेज दिए गए {target} को!")  # Await reply_text

    except Exception as e:
        await message.reply_text(f"❌ Error: {str(e)}")
