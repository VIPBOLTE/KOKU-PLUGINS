import asyncio
import random
from pyrogram import Client, filters
from pyrogram.types import Message
from pyrogram.errors import PeerIdInvalid, UserIsBlocked, FloodWait
from typing import List

# Import project-specific modules
from KOKUMUSIC.misc import SUDOERS 
from KOKUMUSIC.cplugin.utils.data import (
    RAID,
    PBIRAID,
    OneWord,
    HIRAID,
    GROUP,
    VERIFIED_USERS
)

# Constants
MAX_RAID_COUNT = 100
VERIFIED_SET = set(VERIFIED_USERS)
PROTECTED_GROUPS = set(GROUP)

async def perform_raid(
    client: Client,
    message: Message,
    raid_messages: List[str],
    base_delay: float
):
    """Helper function to handle raid logic."""
    try:
        # Parse arguments
        args = message.text.split()
        reply = message.reply_to_message

        # Validate command format
        if (len(args) < 2 and not reply) or (len(args) < 3 and not reply):
            await message.reply_text("**Usage:**\n`.command [count] [username/reply]`")
            return

        # Extract and validate count
        try:
            count = int(args[1])
            count = min(max(count, 1), MAX_RAID_COUNT)  # Ensure count is within limits
        except (IndexError, ValueError):
            await message.reply_text(f"⚠️ Invalid count! Use 1-{MAX_RAID_COUNT}")
            return

        # Get target user
        if reply:
            user = reply.from_user
        else:
            try:
                user = await client.get_users(args[2])
            except (IndexError, PeerIdInvalid):
                await message.reply_text("❌ User not found!")
                return

        # Security checks
        chat_id = message.chat.id
        if chat_id in PROTECTED_GROUPS:
            await message.reply_text("❌ Protected group!")
            return
            
        if user.id in VERIFIED_SET:
            await message.reply_text("⚠️ Can't target verified users!")
            return
            
        if user.id in SUDOERS:
            await message.reply_text("🚫 Target is sudo user!")
            return

        # Delete command message safely
        try:
            await message.delete()
        except Exception as del_error:
            print(f"Failed to delete message: {del_error}")

        # Execute raid with flood control
        for _ in range(count):
            try:
                await client.send_message(
                    chat_id,
                    f"{user.mention} {random.choice(raid_messages)}"
                )
                # Randomized delay to avoid detection
                await asyncio.sleep(base_delay * random.uniform(0.8, 1.2))
            except FloodWait as flood:
                await asyncio.sleep(flood.value)
            except (UserIsBlocked, PeerIdInvalid) as block_error:
                await message.reply_text(f"❌ Blocked/Invalid: {block_error}")
                break
            except Exception as general_error:
                print(f"Raid error: {general_error}")
                await asyncio.sleep(1)

    except Exception as main_error:
        await message.reply_text(f"⚡ Main Error: {str(main_error)}")

# Command handlers
@Client.on_message(filters.command("pbiraid", prefixes=".") & SUDOERS)
async def pbiraid_handler(client: Client, message: Message):
    await perform_raid(client, message, PBIRAID, 0.35)

@Client.on_message(filters.command("oneword", prefixes=".") & SUDOERS)
async def oneword_handler(client: Client, message: Message):
    await perform_raid(client, message, OneWord, 0.25)

@Client.on_message(filters.command("hiraid", prefixes="." & SUDOERS)
async def hiraid_handler(client: Client, message: Message):
    await perform_raid(client, message, HIRAID, 0.3)

@Client.on_message(filters.command("raid", prefixes="." & SUDOERS)
async def raid_handler(client: Client, message: Message):
    await perform_raid(client, message, RAID, 0.4)
