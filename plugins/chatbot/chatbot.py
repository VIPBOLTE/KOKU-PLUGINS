import random
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton, CallbackQuery
from config import MONGO_DB_URI, OWNER_ID, API_ID, API_HASH, BOT_TOKEN

# Initialize Pyrogram Client
from KOKUMUSIC import app

# MongoDB setup
mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client["DAXXDb"]
chats_collection = db["DAXX"]  # Stores enabled chat IDs
words_collection = db["WordDb"]  # Stores word-response pairs

# Admin check decorator
def is_admin(func):
    async def wrapper(client, message):
        if message.from_user.id == OWNER_ID:
            return await func(client, message)
        admin = await client.get_chat_member(message.chat.id, message.from_user.id)
        if admin.status in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
            return await func(client, message)
        await message.reply("You are not an admin!")
    return wrapper

# Callback query handler
@app.on_callback_query()
async def cb_handler(_, query: CallbackQuery):
    user_id = query.from_user.id
    chat_id = query.message.chat.id
    admin = await query.message.chat.get_member(user_id)
    
    if admin.status not in [ChatMemberStatus.OWNER, ChatMemberStatus.ADMINISTRATOR]:
        return await query.answer("You're not an admin!", show_alert=True)
    
    if query.data == "addchat":
        if chats_collection.find_one({"chat_id": chat_id}):
            await query.edit_message_text("Chatbot is already enabled.")
        else:
            chats_collection.insert_one({"chat_id": chat_id})
            await query.edit_message_text(f"Chatbot enabled by {query.from_user.mention}.")
    
    elif query.data == "rmchat":
        if not chats_collection.find_one({"chat_id": chat_id}):
            await query.edit_message_text("Chatbot is already disabled.")
        else:
            chats_collection.delete_one({"chat_id": chat_id})
            await query.edit_message_text(f"Chatbot disabled by {query.from_user.mention}.")

# Command to enable/disable chatbot
@app.on_message(filters.command("chatb") & filters.group)
@is_admin
async def chaton_(client: Client, message: Message):
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("Enable", callback_data="addchat")],
        [InlineKeyboardButton("Disable", callback_data="rmchat")]
    ])
    await message.reply_text(
        f"Chat: {message.chat.title}\nChoose an option to enable/disable chatbot:",
        reply_markup=keyboard
    )

