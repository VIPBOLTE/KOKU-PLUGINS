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
    """Handle raid operations with flood control and safety checks"""
    try:
        args = message.text.split()
        reply = message.reply_to_message

        # Validate command structure
        if not ((len(args) >= 2 and not reply) or (len(args) >= 3 and reply)):
            await message.reply_text("**Usage:**\n`.command [count] [username/reply]`")
            return

        try:
            count = int(args[1])
            count = min(max(count, 1), MAX_RAID_COUNT)
        except (IndexError, ValueError):
            await message.reply_text(f"⚠️ Invalid count! Use 1-{MAX_RAID_COUNT}")
            return

        # Resolve target user
        target_user = reply.from_user if reply else await client.get_users(args[2])

        # Security checks
        chat = message.chat
        if chat.id in PROTECTED_GROUPS:
            await message.reply_text("❌ Protected group!")
            return
            
        if target_user.id in VERIFIED_SET.union(SUDOERS):
            await message.reply_text("🚫 Protected user!")
            return

        # Secure message deletion
        try:
            await message.delete()
        except Exception as del_err:
            print(f"Message deletion failed: {del_err}")

        # Raid execution with flood control
        success_count = 0
        for _ in range(count):
            try:
                await client.send_message(
                    chat.id,
                    f"{target_user.mention} {random.choice(raid_messages)}"
                )
                success_count += 1
                await asyncio.sleep(base_delay * random.uniform(0.7, 1.3))
            except FloodWait as e:
                await asyncio.sleep(e.value + 5)
            except (UserIsBlocked, PeerIdInvalid):
                await message.reply_text("❌ Blocked or invalid peer!")
                break
            except Exception as e:
                print(f"Error during raid: {str(e)}")
                await asyncio.sleep(1)

        # Completion report
        await client.send_message(
            message.from_user.id,
            f"✅ Raid completed: {success_count}/{count} messages sent",
            disable_notification=True
        )

    except Exception as main_err:
        await message.reply_text(f"⚡ Critical error: {str(main_err)}")
        print(f"Main error: {main_err}")

# Command handlers with fixed syntax
@Client.on_message(filters.command("pbiraid", prefixes=".") & SUDOERS)
async def pbiraid_handler(client: Client, message: Message):
    """Handle power biraids"""
    await perform_raid(client, message, PBIRAID, 0.35)

@Client.on_message(filters.command("oneword", prefixes=".") & SUDOERS)
async def oneword_handler(client: Client, message: Message):
    """Single-word raids"""
    await perform_raid(client, message, OneWord, 0.25)

@Client.on_message(filters.command("hiraid", prefixes=".") & SUDOERS)
async def hiraid_handler(client: Client, message: Message):
    """High-intensity raids"""
    await perform_raid(client, message, HIRAID, 0.3)

@Client.on_message(filters.command("raid", prefixes=".") & SUDOERS)
async def raid_handler(client: Client, message: Message):
    """Standard raid operations"""
    await perform_raid(client, message, RAID, 0.4)
