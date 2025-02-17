from pyrogram import filters
from pymongo import MongoClient
from KOKUMUSIC import app
from pyrogram.types import *
import time
import logging
import matplotlib.pyplot as plt
import io
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection with error handling
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client['Champu']
    rankdb = db['Rankingdb']
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# In-memory data storage
user_data = {}
today = {}
weekly = {}
overall = {}

# Load data from MongoDB on startup
def load_data_from_db():
    global today, weekly, overall
    try:
        # Load today's data
        today_data = rankdb.find({"date": time.strftime("%Y-%m-%d")})
        for doc in today_data:
            chat_id = doc["chat_id"]
            user_id = doc["user_id"]
            total_messages = doc["total_messages"]
            if chat_id not in today:
                today[chat_id] = {}
            today[chat_id][user_id] = {"total_messages": total_messages}

        # Load weekly data
        current_week = time.strftime("%U")
        weekly_data = rankdb.find({"week": current_week})
        for doc in weekly_data:
            chat_id = doc["chat_id"]
            user_id = doc["user_id"]
            total_messages = doc["total_messages"]
            if chat_id not in weekly:
                weekly[chat_id] = {}
            if user_id not in weekly[chat_id]:
                weekly[chat_id][user_id] = {current_week: total_messages}
            else:
                weekly[chat_id][user_id][current_week] = total_messages

        # Load overall data
        overall_data = rankdb.find({})
        for doc in overall_data:
            user_id = doc["_id"]
            total_messages = doc["total_messages"]
            overall[user_id] = total_messages

        logger.info("Data loaded from MongoDB successfully.")
    except Exception as e:
        logger.error(f"Error loading data from MongoDB: {e}")

# Load data when the bot starts
load_data_from_db()

# Asia/Kolkata timezone
kolkata_tz = timezone('Asia/Kolkata')

# Scheduler to reset weekly data every Monday at 12:00 AM
scheduler = AsyncIOScheduler(timezone=kolkata_tz)

def reset_weekly_data():
    global weekly
    weekly = {}
    reset_weekly_data_in_db()
    logger.info("Weekly data reset successfully.")

scheduler.add_job(reset_weekly_data, 'cron', day_of_week='mon', hour=0, minute=0)
scheduler.start()

# Function to save today's data to MongoDB
def save_today_data_to_db(chat_id, user_id, total_messages):
    rankdb.update_one(
        {"chat_id": chat_id, "user_id": user_id, "date": time.strftime("%Y-%m-%d")},
        {"$set": {"total_messages": total_messages}},
        upsert=True
    )

# Function to save weekly data to MongoDB
def save_weekly_data_to_db(chat_id, user_id, week, total_messages):
    rankdb.update_one(
        {"chat_id": chat_id, "user_id": user_id, "week": week},
        {"$set": {"total_messages": total_messages}},
        upsert=True
    )

# Function to reset weekly data in MongoDB
def reset_weekly_data_in_db():
    current_week = time.strftime("%U")
    rankdb.delete_many({"week": current_week})
    logger.info("Weekly data reset in database successfully.")

# Watcher for today's messages with MongoDB persistence
@app.on_message(filters.group & filters.group, group=6)
def today_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if chat_id not in today:
            today[chat_id] = {}

        if user_id not in today[chat_id]:
            today[chat_id][user_id] = {"total_messages": 1}
        else:
            today[chat_id][user_id]["total_messages"] += 1

        # Save to MongoDB
        save_today_data_to_db(chat_id , user_id, today[chat_id][user_id]["total_messages"])

        # Track weekly messages
        current_week = time.strftime("%U")
        if chat_id not in weekly:
            weekly[chat_id] = {}

        if user_id not in weekly[chat_id]:
            weekly[chat_id][user_id] = {current_week: 1}
        else:
            if current_week in weekly[chat_id][user_id]:
                weekly[chat_id][user_id][current_week] += 1
            else:
                weekly[chat_id][user_id][current_week] = 1
        
        # Save to MongoDB
        save_weekly_data_to_db(chat_id, user_id, current_week, weekly[chat_id][user_id][current_week])

    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Update the _watcher function to track overall message count
@app.on_message(filters.group & filters.group, group=11)
def _watcher(_, message):
    try:
        user_id = message.from_user.id    
        user_data.setdefault(user_id, {}).setdefault("total_messages", 0)
        user_data[user_id]["total_messages"] += 1    
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)

        # Update overall message count
        overall[user_id] = overall.get(user_id, 0) + 1

    except Exception as e:
        logger.error(f"Error in _watcher: {e}")

# Command to display rankings
@app.on_message(filters.command("ranking") & filters.group)
async def ranking_command(client, message):
    buttons = [
        [InlineKeyboardButton("Daily", callback_data="daily_rank")],
        [InlineKeyboardButton("Weekly", callback_data="weekly_rank")],
        [InlineKeyboardButton("Overall", callback_data="overall_rank")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text("Choose a leaderboard:", reply_markup=reply_markup)

# Callback query handler for daily rank
@app.on_callback_query(filters.regex("daily_rank"))
async def daily_rank_callback(client, callback_query):
    await callback_query.answer()
    chat_id = callback_query.message.chat.id
    user_id = callback_query.from_user.id

    if chat_id in today and user_id in today[chat_id]:
        total_messages = today[chat_id][user_id]["total_messages"]
        await callback_query.message.reply_text(f"Your daily messages: {total_messages}")
    else:
        await callback_query.message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴅᴀʏ.")

# Callback query handler for weekly rank
@app.on_callback_query(filters.regex("weekly_rank"))
async def weekly_rank_callback(client, callback_query):
    await callback_query.answer()
    await weekly_rank(chat_id=callback_query.message.chat.id, message=callback_query.message)

# Callback query handler for overall rank
@app.on_callback_query(filters.regex("overall_rank"))
async def overall_rank_callback(client, callback_query):
    await callback_query.answer()
    await overall_rank(chat_id=callback_query.message.chat.id, message=callback_query.message)

# Function to generate horizontal bar chart
def generate_horizontal_bar_chart(data, title):
    names, values = zip(*data)
    plt.figure(figsize=(10, 6))
    plt.barh(names, values, color='skyblue')
    plt.xlabel('Total Messages')
    plt.title(title)
    plt.tight_layout()

    # Save the plot to a BytesIO object
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    buf.seek(0)
    plt.close()
    return buf

# 
