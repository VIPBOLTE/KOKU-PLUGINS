import random
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.enums import ChatAction, ChatMemberStatus
from pyrogram.types import InlineKeyboardMarkup, Message, InlineKeyboardButton, CallbackQuery
from config import MONGO_DB_URI, OWNER_ID, API_ID, API_HASH, BOT_TOKEN
from config import API_ID, API_HASH, STRING1, MONGO_DB_URI
# Initialize Pyrogram Client
from KOKUMUSIC import app

# MongoDB setup
mongo_client = MongoClient(MONGO_DB_URI)
db = mongo_client["DAXXDb"]
chats_collection = db["DAXX"]  # Stores enabled chat IDs
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
        [InlineKeyboardButton("Enable", callback_data="rmchat")],
        [InlineKeyboardButton("Disable", callback_data="addchat")]
    ])
    await message.reply_text(
        f"Chat: {message.chat.title}\nChoose an option to enable/disable chatbot:",
        reply_markup=keyboard
    )


@app.on_message(
    (filters.text | filters.sticker | filters.group) & ~filters.private & ~filters.bot, group=4
)
async def chatbot_text(client: Client, message: Message):
    try:
        if (
            message.text.startswith("!")
            or message.text.startswith("/")
            or message.text.startswith("?")
            or message.text.startswith("@")
            or message.text.startswith("#")
        ):
            return
    except Exception:
        pass
    chatdb = MongoClient(MONGO_DB_URI)
    chatai = chatdb["Word"]["WordDb"]

    if not message.reply_to_message:
        DAXXdb = MongoClient(MONGO_DB_URI)
        DAXX = DAXXdb["DAXXDb"]["DAXX"]
        is_DAXX = DAXX.find_one({"chat_id": message.chat.id})
        if not is_DAXX:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            K = []
            is_chat = chatai.find({"word": message.text})
            k = chatai.find_one({"word": message.text})
            if k:
                for x in is_chat:
                    K.append(x["text"])
                hey = random.choice(K)
                is_text = chatai.find_one({"text": hey})
                Yo = is_text["check"]
                if Yo == "sticker":
                    await message.reply_sticker(f"{hey}")
                if not Yo == "sticker":
                    await message.reply_text(f"{hey}")

    if message.reply_to_message:
        DAXXdb = MongoClient(MONGO_DB_URI)
        DAXX = DAXXdb["DAXXDb"]["DAXX"]
        is_DAXX = DAXX.find_one({"chat_id": message.chat.id})
        if message.reply_to_message.from_user.id == client.id:
            if not is_DAXX:
                await client.send_chat_action(message.chat.id, ChatAction.TYPING)
                K = []
                is_chat = chatai.find({"word": message.text})
                k = chatai.find_one({"word": message.text})
                if k:
                    for x in is_chat:
                        K.append(x["text"])
                    hey = random.choice(K)
                    is_text = chatai.find_one({"text": hey})
                    Yo = is_text["check"]
                    if Yo == "sticker":
                        await message.reply_sticker(f"{hey}")
                    if not Yo == "sticker":
                        await message.reply_text(f"{hey}")
        if not message.reply_to_message.from_user.id == client.id:
            if message.sticker:
                is_chat = chatai.find_one(
                    {
                        "word": message.reply_to_message.text,
                        "id": message.sticker.file_unique_id,
                    }
                )
                if not is_chat:
                    chatai.insert_one(
                        {
                            "word": message.reply_to_message.text,
                            "text": message.sticker.file_id,
                            "check": "sticker",
                            "id": message.sticker.file_unique_id,
                        }
                    )
            if message.text:
                is_chat = chatai.find_one(
                    {"word": message.reply_to_message.text, "text": message.text}
                )
                if not is_chat:
                    chatai.insert_one(
                        {
                            "word": message.reply_to_message.text,
                            "text": message.text,
                            "check": "none",
                        }
                    )


@app.on_message(
    (filters.sticker | filters.group | filters.text) & ~filters.private & ~filters.bot, group=4
)
async def chatbot_sticker(client: Client, message: Message):
    try:
        if (
            message.text.startswith("!")
            or message.text.startswith("/")
            or message.text.startswith("?")
            or message.text.startswith("@")
            or message.text.startswith("#")
        ):
            return
    except Exception:
        pass
    chatdb = MongoClient(MONGO_DB_URI)
    chatai = chatdb["Word"]["WordDb"]

    if not message.reply_to_message:
        DAXXdb = MongoClient(MONGO_DB_URI)
        DAXX = DAXXdb["DAXXDb"]["DAXX"]
        is_DAXX = DAXX.find_one({"chat_id": message.chat.id})
        if not is_DAXX:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            K = []
            is_chat = chatai.find({"word": message.sticker.file_unique_id})
            k = chatai.find_one({"word": message.text})
            if k:
                for x in is_chat:
                    K.append(x["text"])
                hey = random.choice(K)
                is_text = chatai.find_one({"text": hey})
                Yo = is_text["check"]
                if Yo == "text":
                    await message.reply_text(f"{hey}")
                if not Yo == "text":
                    await message.reply_sticker(f"{hey}")

    if message.reply_to_message:
        DAXXdb = MongoClient(MONGO_DB_URI)
        DAXX = DAXXdb["DAXXDb"]["DAXX"]
        is_DAXX = DAXX.find_one({"chat_id": message.chat.id})
        if message.reply_to_message.from_user.id == Client.id:
            if not is_DAXX:
                await client.send_chat_action(message.chat.id, ChatAction.TYPING)
                K = []
                is_chat = chatai.find({"word": message.text})
                k = chatai.find_one({"word": message.text})
                if k:
                    for x in is_chat:
                        K.append(x["text"])
                    hey = random.choice(K)
                    is_text = chatai.find_one({"text": hey})
                    Yo = is_text["check"]
                    if Yo == "text":
                        await message.reply_text(f"{hey}")
                    if not Yo == "text":
                        await message.reply_sticker(f"{hey}")
        if not message.reply_to_message.from_user.id == Client.id:
            if message.text:
                is_chat = chatai.find_one(
                    {
                        "word": message.reply_to_message.sticker.file_unique_id,
                        "text": message.text,
                    }
                )
                if not is_chat:
                    toggle.insert_one(
                        {
                            "word": message.reply_to_message.sticker.file_unique_id,
                            "text": message.text,
                            "check": "text",
                        }
                    )
            if message.sticker:
                is_chat = chatai.find_one(
                    {
                        "word": message.reply_to_message.sticker.file_unique_id,
                        "text": message.sticker.file_id,
                    }
                )
                if not is_chat:
                    chatai.insert_one(
                        {
                            "word": message.reply_to_message.sticker.file_unique_id,
                            "text": message.sticker.file_id,
                            "check": "none",
                        }
                    )


@app.on_message(
    (filters.text | filters.sticker | filters.group) & ~filters.private & ~filters.bot, group=4
)
async def chatbot_pvt(client: Client, message: Message):
    try:
        if (
            message.text.startswith("!")
            or message.text.startswith("/")
            or message.text.startswith("?")
            or message.text.startswith("@")
            or message.text.startswith("#")
        ):
            return
    except Exception:
        pass
    chatdb = MongoClient(MONGO_DB_URI)
    chatai = chatdb["Word"]["WordDb"]
    if not message.reply_to_message:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        K = []
        is_chat = chatai.find({"word": message.text})
        for x in is_chat:
            K.append(x["text"])
        hey = random.choice(K)
        is_text = chatai.find_one({"text": hey})
        Yo = is_text["check"]
        if Yo == "sticker":
            await message.reply_sticker(f"{hey}")
        if not Yo == "sticker":
            await message.reply_text(f"{hey}")
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == client.id:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            K = []
            is_chat = chatai.find({"word": message.text})
            for x in is_chat:
                K.append(x["text"])
            hey = random.choice(K)
            is_text = chatai.find_one({"text": hey})
            Yo = is_text["check"]
            if Yo == "sticker":
                await message.reply_sticker(f"{hey}")
            if not Yo == "sticker":
                await message.reply_text(f"{hey}")


@app.on_message(
    (filters.sticker | filters.sticker | filters.group)
    & ~filters.private
    & ~filters.bot,
    group=4,
)
async def chatbot_sticker_pvt(client: Client, message: Message):
    try:
        if (
            message.text.startswith("!")
            or message.text.startswith("/")
            or message.text.startswith("?")
            or message.text.startswith("@")
            or message.text.startswith("#")
        ):
            return
    except Exception:
        pass
    chatdb = MongoClient(MONGO_DB_URI)
    chatai = chatdb["Word"]["WordDb"]
    if not message.reply_to_message:
        await client.send_chat_action(message.chat.id, ChatAction.TYPING)
        K = []
        is_chat = chatai.find({"word": message.sticker.file_unique_id})
        for x in is_chat:
            K.append(x["text"])
        hey = random.choice(K)
        is_text = chatai.find_one({"text": hey})
        Yo = is_text["check"]
        if Yo == "text":
            await message.reply_text(f"{hey}")
        if not Yo == "text":
            await message.reply_sticker(f"{hey}")
    if message.reply_to_message:
        if message.reply_to_message.from_user.id == client.id:
            await client.send_chat_action(message.chat.id, ChatAction.TYPING)
            K = []
            is_chat = chatai.find({"word": message.sticker.file_unique_id})
            for x in is_chat:
                K.append(x["text"])
            hey = random.choice(K)
            is_text = chatai.find_one({"text": hey})
            Yo = is_text["check"]
            if Yo == "text":
                await message.reply_text(f"{hey}")
            if not Yo == "text":
                await message.reply_sticker(f"{hey}")
