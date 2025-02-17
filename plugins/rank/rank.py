from pyrogram import Client, filters
from pyrogram.types import *
from pyrogram.errors import MessageNotModified
from pymongo import MongoClient
import logging
import pytz
from datetime import datetime, timedelta
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
import asyncio
from KOKUMUSIC import app
client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/')
db = client['Champu']
rankdb = db['Rankingdb']
weeklydb = db['WeeklyRankingdb']

# Timezone setup
timezone = pytz.timezone('Asia/Kolkata')

# In-memory storage for today's data (if necessary)
today_data = {}

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Watcher for Overall Messages (Total Messages)
@app.on_message(filters.group)
def overall_watcher(_, message):
    try:
        user_id = message.from_user.id

        # Update overall message count in MongoDB
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)

    except Exception as e:
        logger.error(f"Error in overall_watcher: {e}")

# Watcher for Today's Messages (Specific Day)
@app.on_message(filters.group)
def today_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in today_data:
            today_data[chat_id] = {}

        if user_id not in today_data[chat_id]:
            today_data[chat_id][user_id] = {"total_messages": 1}
        else:
            today_data[chat_id][user_id]["total_messages"] += 1

    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Watcher for Weekly Messages (Sunday to Saturday)
@app.on_message(filters.group)
def weekly_watcher(_, message):
    try:
        user_id = message.from_user.id
        current_time = datetime.now(timezone)
        week_start = current_time - timedelta(days=current_time.weekday())  # Get Sunday of this week
        week_start_str = week_start.strftime('%Y-%m-%d')

        # Update weekly message count in MongoDB
        weeklydb.update_one(
            {"_id": user_id, "week_start": week_start_str},
            {"$inc": {"total_messages": 1}},
            upsert=True
        )

    except Exception as e:
        logger.error(f"Error in weekly_watcher: {e}")

# Command to show ranking (Today, Weekly, Overall)
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    try:
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today")],
            [InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly")],
            [InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall")]
        ])
        await message.reply_text("⬤ 📈 ᴄʜᴏᴏsᴇ ᴀ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ:", reply_markup=button)

    except Exception as e:
        logger.error(f"Error in ranking command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Callback for Today's Leaderboard
@app.on_callback_query(filters.regex("today"))
async def today_rank(_, query):
    try:
        chat_id = query.message.chat.id
        if chat_id in today_data:
            sorted_today = sorted(today_data[chat_id].items(), key=lambda x: x[1]["total_messages"], reverse=True)
            response = "⬤ 📈 Today's Top Users\n\n"
            for idx, (user_id, data) in enumerate(sorted_today[:10], start=1):
                user_name = (await app.get_users(user_id)).first_name
                response += f"{idx}. {user_name} ➥ {data['total_messages']}\n"
            await query.message.edit_text(response)
        else:
            await query.message.edit_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")

    except Exception as e:
        logger.error(f"Error in today_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Callback for Weekly Leaderboard
@app.on_callback_query(filters.regex("weekly"))
async def weekly_rank(_, query):
    try:
        current_time = datetime.now(timezone)
        week_start = current_time - timedelta(days=current_time.weekday())  # Get Sunday of this week
        week_start_str = week_start.strftime('%Y-%m-%d')

        top_users = weeklydb.find({"week_start": week_start_str}).sort("total_messages", -1).limit(10)
        response = "⬤ 📈 Weekly Leaderboard (Sunday to Saturday)\n\n"
        for idx, user in enumerate(top_users, start=1):
            user_id = user["_id"]
            total_messages = user["total_messages"]
            user_name = (await app.get_users(user_id)).first_name
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
        
        await query.message.edit_text(response)

    except Exception as e:
        logger.error(f"Error in weekly_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Callback for Overall Leaderboard
@app.on_callback_query(filters.regex("overall"))
async def overall_rank(_, query):
    try:
        top_users = rankdb.find().sort("total_messages", -1).limit(10)
        response = "⬤ 📈 Overall Leaderboard\n\n"
        for idx, user in enumerate(top_users, start=1):
            user_id = user["_id"]
            total_messages = user["total_messages"]
            user_name = (await app.get_users(user_id)).first_name
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
        
        await query.message.edit_text(response)

    except Exception as e:
        logger.error(f"Error in overall_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")
