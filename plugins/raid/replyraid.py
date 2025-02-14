import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from random import choice

# Import your project-specific modules
from KOKUMUSIC.misc import SUDOERS as SUDO_USER
from KOKUMUSIC.cplugin.utils.data import (
    RAID,
    PBIRAID,
    OneWord,
    HIRAID,
    GROUP,
    VERIFIED_USERS
)

# ======================== PBIRAID COMMAND ========================= #
@Client.on_message(filters.command("pbiraid", prefixes=".") & filters.user(*SUDO_USER))
async def pbiraid_handler(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        
        if len(args) < 3 and not message.reply_to_message:
            await message.reply_text("**Usage:**\n`.pbiraid [count] [username/reply]`")
            return

        if message.reply_to_message:
            user = message.reply_to_message.from_user
            count = int(args[1])
        else:
            count = int(args[1])
            try:
                user = await client.get_users(args[2])
            except Exception as e:
                await message.reply_text(f"**Error:** {str(e)}")
                return

        # Validation checks
        if message.chat.id in GROUP:
            await message.reply_text("❌ I can't spam in protected groups!")
            return
            
        if user.id in VERIFIED_USERS:
            await message.reply_text("⚠️ Can't target verified users!")
            return
            
        if user.id in SUDO_USER:
            await message.reply_text("🚫 This user is in sudo list!")
            return

        # Start PBIRAID
        await message.delete()
        for _ in range(count):
            await client.send_message(
                message.chat.id,
                f"{user.mention} {random.choice(PBIRAID)}"
            )
            await asyncio.sleep(0.3)

    except Exception as e:
        await message.reply_text(f"**PBIRAID Error:** {str(e)}")

# ======================== ONEWORD COMMAND ========================= #
@Client.on_message(filters.command("oneword", prefixes=".") & filters.user(*SUDO_USER))
async def oneword_handler(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        
        if len(args) < 3 and not message.reply_to_message:
            await message.reply_text("**Usage:**\n`.oneword [count] [username/reply]`")
            return

        if message.reply_to_message:
            user = message.reply_to_message.from_user
            count = int(args[1])
        else:
            count = int(args[1])
            try:
                user = await client.get_users(args[2])
            except Exception as e:
                await message.reply_text(f"**Error:** {str(e)}")
                return

        # Validation checks
        if message.chat.id in GROUP:
            await message.reply_text("❌ I can't spam in protected groups!")
            return
            
        if user.id in VERIFIED_USERS:
            await message.reply_text("⚠️ Can't target verified users!")
            return
            
        if user.id in SUDO_USER:
            await message.reply_text("🚫 This user is in sudo list!")
            return

        # Start OneWord Raid
        await message.delete()
        for _ in range(count):
            await client.send_message(
                message.chat.id,
                f"{user.mention} {random.choice(OneWord)}"
            )
            await asyncio.sleep(0.2)

    except Exception as e:
        await message.reply_text(f"**ONEWORD Error:** {str(e)}")

# ======================== HIRAID COMMAND ========================== #
@Client.on_message(filters.command("hiraid", prefixes=".") & filters.user(*SUDO_USER))
async def hiraid_handler(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        
        if len(args) < 3 and not message.reply_to_message:
            await message.reply_text("**Usage:**\n`.hiraid [count] [username/reply]`")
            return

        if message.reply_to_message:
            user = message.reply_to_message.from_user
            count = int(args[1])
        else:
            count = int(args[1])
            try:
                user = await client.get_users(args[2])
            except Exception as e:
                await message.reply_text(f"**Error:** {str(e)}")
                return

        # Validation checks
        if message.chat.id in GROUP:
            await message.reply_text("❌ I can't spam in protected groups!")
            return
            
        if user.id in VERIFIED_USERS:
            await message.reply_text("⚠️ Can't target verified users!")
            return
            
        if user.id in SUDO_USER:
            await message.reply_text("🚫 This user is in sudo list!")
            return

        # Start HIRAID
        await message.delete()
        for _ in range(count):
            await client.send_message(
                message.chat.id,
                f"{user.mention} {random.choice(HIRAID)}"
            )
            await asyncio.sleep(0.25)

    except Exception as e:
        await message.reply_text(f"**HIRAID Error:** {str(e)}")

# ======================== MAIN RAID COMMAND ======================= #
@Client.on_message(filters.command("raid", prefixes=".") & filters.user(*SUDO_USER))
async def raid_handler(client: Client, message: Message):
    try:
        args = message.text.split(maxsplit=2)
        
        if len(args) < 3 and not message.reply_to_message:
            await message.reply_text("**Usage:**\n`.raid [count] [username/reply]`")
            return

        if message.reply_to_message:
            user = message.reply_to_message.from_user
            count = int(args[1])
        else:
            count = int(args[1])
            try:
                user = await client.get_users(args[2])
            except Exception as e:
                await message.reply_text(f"**Error:** {str(e)}")
                return

        # Validation checks
        if message.chat.id in GROUP:
            await message.reply_text("❌ I can't spam in protected groups!")
            return
            
        if user.id in VERIFIED_USERS:
            await message.reply_text("⚠️ Can't target verified users!")
            return
            
        if user.id in SUDO_USER:
            await message.reply_text("🚫 This user is in sudo list!")
            return

        # Start RAID
        await message.delete()
        for _ in range(count):
            await client.send_message(
                message.chat.id,
                f"{user.mention} {random.choice(RAID)}"
            )
            await asyncio.sleep(0.3)

    except Exception as e:
        await message.reply_text(f"**RAID Error:** {str(e)}")
