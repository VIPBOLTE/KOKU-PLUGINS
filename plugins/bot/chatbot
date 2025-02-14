import random
import asyncio
import logging
from pyrogram import enums, filters
from pyrogram.types import ChatMemberUpdated
from pymongo import MongoClient
from ChampuMusic import app
from ChampuMusic.utils.database import get_assistant
from config import MONGO_DB_URI

# Configure logging
logging.basicConfig(level=logging.INFO)
LOGGER = logging.getLogger(__name__)

# Define the log group chat ID
LOG_GROUP_ID = -1001423108989  # Replace with your actual log group chat ID

# Constants
OWNER_ID = 6399386263  # Replace with the actual owner ID
SPAM_THRESHOLD = 3
SPAM_WINDOW_SECONDS = 5
MAX_SPAM_WARNINGS = 3

# Database setup
db_client = MongoClient(MONGO_DB_URI)
group_db = db_client.telegram_bot.approved_groups
user_db = db_client.telegram_bot.users

# In-memory tracking for spam protection
user_last_message_time = {}
user_command_count = {}
user_spam_warnings = {}

# Response messages
RESPONSES = [
    "Hii! Kaise ho? 😊",
    "Main thik hoon, tum kaise ho? 🌸",
    "Wow, yeh toh amazing hai! 😍",
    "Acha yeh batao, aur kya chal raha hai? 🧐",
    "Tumhare baare mein aur jaan ne ka mann kar raha hai! 🥰",
    "Sach mein, mazaa aa gaya! ❤️",
    "Aapki baatein hamesha achhi lagti hain! 🥀",
    "Mujhe yeh pasand aaya! 🤗"
]

# Function to send logs to the log group
async def send_log_to_group(chat_id, message):
    try:
        userbot = await get_assistant(chat_id)
        await userbot.send_message(LOG_GROUP_ID, message)
    except Exception as e:
        LOGGER.error(f"Failed to send log to log group: {e}")

# Helper Functions
async def is_group_approved(chat_id):
    """Check if a group is approved."""
    group = group_db.find_one({"chat_id": chat_id})
    return bool(group)

async def set_group_approval(chat_id, state):
    """Set the approval status of a group."""
    if state:
        group_db.update_one({"chat_id": chat_id}, {"$set": {"approved": True}}, upsert=True)
    else:
        group_db.delete_one({"chat_id": chat_id})

async def is_user_banned(user_id):
    """Check if a user is banned."""
    user = user_db.find_one({"user_id": user_id})
    return bool(user and user.get("banned", False))

async def ban_user(user_id):
    """Ban a user."""
    user_db.update_one({"user_id": user_id}, {"$set": {"banned": True}}, upsert=True)

async def unban_user(user_id):
    """Unban a user."""
    user_db.update_one({"user_id": user_id}, {"$unset": {"banned": ""}}, upsert=True)

# Command to approve/disapprove groups
@app.on_message(filters.command("approvegroup") & ~filters.private)
async def approve_group(_, message):
    """Approve or disapprove a group."""
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Only the owner can manage group approvals!")

    if len(message.command) != 2:
        return await message.reply("⚙️ Usage: `/approvegroup [on|off]`")

    state = message.command[1].lower()
    if state not in ["on", "off"]:
        return await message.reply("❌ Invalid state! Use 'on' or 'off'.")

    chat_id = message.chat.id
    if state == "on":
        await set_group_approval(chat_id, True)
        await message.reply(f"✅ Group `{message.chat.title}` approved for bot interaction!")
    else:
        await set_group_approval(chat_id, False)
        await message.reply(f"🚫 Group `{message.chat.title}` disapproved!")

# Command to ban/unban users
@app.on_message(filters.command("banuser") & ~filters.private)
async def ban_user_command(_, message):
    """Ban or unban a user."""
    if message.from_user.id != OWNER_ID:
        return await message.reply("❌ Only the owner can manage user bans!")

    if len(message.command) != 2:
        return await message.reply("⚙️ Usage: `/banuser [user_id]`")

    user_id = int(message.command[1])
    if await is_user_banned(user_id):
        await unban_user(user_id)
        await message.reply(f"👋 User  `{user_id}` has been unbanned!")
    else:
        await ban_user(user_id)
        await message.reply(f"🚫 User `{user_id}` has been banned!")

# Updated error handling in the reply_to_messages function
@app.on_message(filters.text & ~filters.private)
async def reply_to_messages(_, message):
    """Reply to messages in approved groups."""
    chat_id = message.chat.id

    if not await is_group_approved(chat_id):
        return

    if message.from_user and message.from_user.is_self:
        return

    user_id = message.from_user.id

    if await is_user_banned(user_id):
        return await message.reply("🚫 You are banned from using this bot.")

    current_time = asyncio.get_event_loop().time()

    # Spam protection
    last_message_time = user_last_message_time.get(user_id, 0)
    if current_time - last_message_time < SPAM_WINDOW_SECONDS:
        user_command_count[user_id] = user_command_count.get(user_id, 0) + 1
        if user_command_count[user_id] > SPAM_THRESHOLD:
            user_spam_warnings[user_id] = user_spam_warnings.get(user_id, 0) + 1
            if user_spam_warnings[user_id] >= MAX_SPAM_WARNINGS:
                await ban_user(user_id)
                await message.reply("🚫 You have been banned for spamming.")
                return
            await message.reply("⚠️ Please avoid spamming. Try again after a while.")
            return
    else:
        user_command_count[user_id] = 1

    user_last_message_time[user_id] = current_time

    # Respond with a random message
    response = random.choice(RESPONSES)
    try:
        await asyncio.sleep(random.randint(15, 20))  # Delay of 15–20 seconds
        userbot = await get_assistant(chat_id)
        await userbot.send_message(chat_id, response)
    except Exception as e:
        error_message = f"Error in replying: {e}"
        LOGGER.error(error_message)
        await send_log_to_group(chat_id, error_message)