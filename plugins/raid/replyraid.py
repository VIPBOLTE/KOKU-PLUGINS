import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import FloodWait
from random import choice
import config

# Raid Messages (कस्टमाइज करें)
RAID_MESSAGES = [
    "इधर देख! 👀",
    "छेड़ने की हिम्मत? 😡",
    "जय श्री राम! 🚩",
    "तुम्हारी औकात? 🤣"
]

# Assume these lists (VERIFIED_USERS, SUDO_USER, etc.) are imported or defined somewhere in your config.
VERIFIED_USERS = set()  # Add actual verified users here
SUDO_USER = set()  # Add sudo users here
GROUP = set()  # Add blocked group IDs here

app = Client(
    "my_assistant",
    api_id=config.API_ID,
    api_hash=config.API_HASH,
    session_string=config.STRING1
)

@app.on_message(filters.command("raid") & filters.group)
async def raid_assistant(client: Client, message: Message):
    try:
        # Parsing the command arguments
        args = message.text.split()
        if len(args) < 3:
            await message.reply_text("**Usage:**\n`!raid [count] [username]`")
            return
        
        # Safely convert count to int and handle invalid input
        try:
            count = int(args[1])
        except ValueError:
            await message.reply_text("**Error:** The [count] parameter must be an integer.")
            return
        
        target = args[2]

        # Fetch user info
        try:
            user = await client.get_users(target)
        except:
            await message.reply_text("**Error:** User not found or may be deleted!")
            return

        # Check if raid is allowed
        if int(message.chat.id) in GROUP:
            await message.reply_text("**Sorry !! I can't Spam Here.**")
            return
        
        if int(user.id) in VERIFIED_USERS:
            await message.reply_text("I can't raid on my developer!")
            return
        
        if int(user.id) in SUDO_USER:
            await message.reply_text("This user is a sudo user.")
            return

        mention = user.mention

        # Start the raid
        for _ in range(count):
            try:
                # Send a random raid message
                r = f"{mention} {choice(RAID_MESSAGES)}"
                await client.send_message(message.chat.id, r)

                # Anti-flood delay
                await asyncio.sleep(random.uniform(0.5, 1.5))
                
            except FloodWait as e:
                # Handle FloodWait error by sleeping for the suggested time
                await asyncio.sleep(e.value + 5)

        # Delete the original message and send the reply
        await message.delete()  # Await delete
        await message.reply_text(f"✅ {count} रैड मैसेज भेज दिए गए {target} को!")  # Await reply_text

    except Exception as e:
        # Catch any general exception and send a reply
        await message.reply_text(f"❌ Error: {str(e)}")
