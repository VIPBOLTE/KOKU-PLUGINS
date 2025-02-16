import html
import asyncio
import time
import io
import matplotlib.pyplot as plt
from pyrogram import Client, filters, enums
from pyrogram.types import Message, InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto, CallbackQuery
from pymongo import MongoClient
import logging
from KOKUMUSIC import app
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    mongo_client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    mongo_client.server_info()  # Test connection
    db = mongo_client['Champu']
    rankdb = db['Rankingdb']
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# In-memory storage
message_history = {}
penalized_users = {}
today_stats = {}
overall_stats = {}
chat_locks = {}


def generate_horizontal_bar_chart(data, title):
    try:
        plt.figure(figsize=(10, 6))
        users = [item[0] for item in data]
        counts = [item[1] for item in data]
        
        plt.barh(users, counts, color='#FF6B6B')
        plt.xlabel('Message Count')
        plt.title(title)
        plt.gca().invert_yaxis()
        
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        return buf
    except Exception as e:
        logger.error(f"Chart generation error: {e}")
        return None

async def get_chat_lock(chat_id):
    if chat_id not in chat_locks:
        chat_locks[chat_id] = asyncio.Lock()
    return chat_locks[chat_id]

@app.on_message(filters.group & filters.text & ~filters.bot)
async def flood_control_handler(client, message: Message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        current_time = time.time()
        
        async with (await get_chat_lock(chat_id)):
            # Check existing penalties
            if penalized_users.get(chat_id, {}).get(user_id, 0) > current_time:
                return

            # Update message history
            if chat_id not in message_history:
                message_history[chat_id] = []
            
            message_history[chat_id].append(user_id)
            if len(message_history[chat_id]) > 10:
                message_history[chat_id] = message_history[chat_id][-10:]

            # Detect flood
            if len(message_history[chat_id]) == 10 and all(uid == user_id for uid in message_history[chat_id]):
                # Apply penalty
                penalized_users.setdefault(chat_id, {})[user_id] = current_time + 600  # 10 minutes
                
                await message.reply_text(
                    f"⚠️ {html.escape(message.from_user.first_name)} को 10 मिनट के लिए म्यूट किया गया!\n"
                    "कारण: 10 लगातार संदेश भेजना"
                )
                message_history[chat_id].clear()

    except Exception as e:
        logger.error(f"Flood control error: {e}")

@app.on_message(filters.group & ~filters.bot)
async def message_counters(client, message: Message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        current_time = time.time()
        
        async with (await get_chat_lock(chat_id)):
            # Check penalty status
            if penalized_users.get(chat_id, {}).get(user_id, 0) > current_time:
                return

            # Update today's stats
            today_key = f"{chat_id}_{time.strftime('%Y-%m-%d')}"
            today_stats.setdefault(today_key, {}).setdefault(user_id, 0)
            today_stats[today_key][user_id] += 1

            # Update overall stats
            rankdb.update_one(
                {"_id": user_id},
                {"$inc": {"total_messages": 1}},
                upsert=True
            )

    except Exception as e:
        logger.error(f"Counter error: {e}")

@app.on_message(filters.command(["today", "ranking"]))
async def leaderboard_handler(client, message: Message):
    try:
        command = message.command[0]
        chat_id = message.chat.id
        
        if command == "today":
            today_key = f"{chat_id}_{time.strftime('%Y-%m-%d')}"
            users_data = sorted(
                [(k, v) for k, v in today_stats.get(today_key, {}).items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            title = "आज का लीडरबोर्ड 📊"
        else:
            users_data = []
            for doc in rankdb.find().sort("total_messages", -1).limit(10):
                users_data.append((doc["_id"], doc["total_messages"]))
            title = "कुल लीडरबोर्ड 🏆"

        # Prepare data
        leaderboard = []
        for idx, (user_id, count) in enumerate(users_data[:10], 1):
            try:
                user = await client.get_users(user_id)
                name = user.first_name
            except:
                name = "अज्ञात"
            leaderboard.append((name, count))

        # Generate chart
        chart = generate_horizontal_bar_chart(leaderboard, title)
        if not chart:
            await message.reply_text("डेटा उपलब्ध नहीं है")
            return

        # Prepare buttons
        buttons = InlineKeyboardMarkup([[
            InlineKeyboardButton(
                "आज का लीडरबोर्ड" if command == "ranking" else "कुल लीडरबोर्ड",
                callback_data="ranking" if command == "today" else "today"
            )
        ]])

        await message.reply_photo(
            photo=chart,
            caption=title,
            reply_markup=buttons
        )

    except Exception as e:
        logger.error(f"Leaderboard error: {e}")

@app.on_callback_query(filters.regex("today|ranking"))
async def update_leaderboard(client, query: CallbackQuery):
    try:
        chat_id = query.message.chat.id
        command = query.data
        
        if command == "today":
            today_key = f"{chat_id}_{time.strftime('%Y-%m-%d')}"
            users_data = sorted(
                [(k, v) for k, v in today_stats.get(today_key, {}).items()],
                key=lambda x: x[1],
                reverse=True
            )[:10]
            title = "आज का लीडरबोर्ड 📊"
        else:
            users_data = []
            for doc in rankdb.find().sort("total_messages", -1).limit(10):
                users_data.append((doc["_id"], doc["total_messages"]))
            title = "कुल लीडरबोर्ड 🏆"

        # Prepare data
        leaderboard = []
        for idx, (user_id, count) in enumerate(users_data[:10], 1):
            try:
                user = await client.get_users(user_id)
                name = user.first_name
            except:
                name = "अज्ञात"
            leaderboard.append((name, count))

        # Generate new chart
        chart = generate_horizontal_bar_chart(leaderboard, title)
        if not chart:
            await query.answer("डेटा उपलब्ध नहीं है")
            return

        # Update message
        await query.message.edit_media(
            InputMediaPhoto(chart, caption=title),
            reply_markup=InlineKeyboardMarkup([[
                InlineKeyboardButton(
                    "आज का लीडरबोर्ड" if command == "ranking" else "कुल लीडरबोर्ड",
                    callback_data="ranking" if command == "today" else "today"
                )
            ]])
        )
        await query.answer()

    except Exception as e:
        logger.error(f"Callback error: {e}")
        await query.answer("त्रुटि हुई")
