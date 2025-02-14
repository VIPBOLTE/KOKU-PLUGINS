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
    session_string=config.SESSION_STRING
)

# Command Handler (User Account के लिए)
@app.on_message(filters.command("raid") & filters.private)  # सिर्फ प्राइवेट चैट में कमांड
async def raid_assistant(client: Client, message: Message):
    try:
        # कमांड पार्स करें: !raid 5 @username
        args = message.text.split()
        if len(args) < 3:
            await message.reply("**Usage:**\n`!raid [count] [username]`")
            return

        count = int(args[1])
        target = args[2]

        # रैड शुरू करें
        for _ in range(count):
            try:
                await client.send_message(
                    target,
                    random.choice(RAID_MESSAGES)
                )
                await asyncio.sleep(random.uniform(0.5, 1.5)  # Anti-Flood Delay
            except FloodWait as e:
                await asyncio.sleep(e.value + 5)  # FloodWait हेंडल करें

        await message.reply(f"✅ {count} रैड मैसेज भेज दिए गए {target} को!")

    except Exception as e:
        await message.reply(f"❌ Error: {str(e)}")
