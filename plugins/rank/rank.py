from pyrogram import Client, filters
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
import matplotlib.pyplot as plt
import io
import logging
import time
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
import csv
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client['Champu']
    rankdb = db['Rankingdb']
    history_db = db['LeaderboardHistory']
except ConnectionFailure as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# In-memory data storage
user_data = {}
today = {}
weekly = {}
overall = {}

# Asia/Kolkata timezone
kolkata_tz = timezone('Asia/Kolkata')

# Scheduler to reset weekly data every Monday at 12:00 AM
scheduler = AsyncIOScheduler(timezone=kolkata_tz)

def reset_weekly_data():
    global weekly
    current_week = time.strftime("%U")
    leaderboard = sorted(overall.items(), key=lambda x: x[1], reverse=True)
    save_leaderboard_history(leaderboard, time.strftime("%Y-%m-%d"))
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

# Function to save leaderboard history
def save_leaderboard_history(leaderboard, date):
    history_db.insert_one({
        "date": date,
        "leaderboard": leaderboard
    })
    logger.info(f"Leaderboard data saved for date: {date}")

# Rate limiting decorator
user_cooldowns = {}

def rate_limit(seconds: int):
    def decorator(func):
        async def wrapper(client, message):
            user_id = message.from_user.id
            current_time = datetime.now()
            if user_id in user_cooldowns and current_time < user_cooldowns[user_id]:
                await message.reply_text(f"Please wait {seconds} seconds before using this command again.")
                return
            user_cooldowns[user_id] = current_time + timedelta(seconds=seconds)
            await func(client, message)
        return wrapper
    return decorator

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
        save_today_data_to_db(chat_id, user_id, today[chat_id][user_id]["total_messages"])

        # Track weekly messages
        current_week = time.strftime("%U")
        if chat_id not in weekly:
            weekly[chat_id] = {}

        if user_id not in weekly[chat_id]:
            weekly[chat_id][user_id] = {current_week: 1}
        else:
            if current_week not in weekly[chat_id][user_id]:
                weekly[chat_id][user_id][current_week] = 1
            else:
                weekly[chat_id][user_id][current_week] += 1

        # Save weekly data to MongoDB
        save_weekly_data_to_db(chat_id, user_id, current_week, weekly[chat_id][user_id][current_week])

    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Command to display today's leaderboard
@app.on_message(filters.command("today_leaderboard"))
async def today_leaderboard(_, message):
    chat_id = message.chat.id
    leaderboard = sorted(today.get(chat_id, {}).items(), key=lambda x: x[1]["total_messages"], reverse=True)
    response = "📊 Today's Leaderboard:\n"
    response += "\n".join([f"User  ID: {user_id}, Messages: {data['total_messages']}" for user_id, data in leaderboard])
    await message.reply_text(response)

# Command to display weekly leaderboard
@app.on_message(filters.command("weekly_leaderboard"))
async def weekly_leaderboard(_, message):
    chat_id = message.chat.id
    leaderboard = {}
    for user_id, weeks in weekly.get(chat_id, {}).items():
        total_messages = sum(weeks.values())
        leaderboard[user_id] = total_messages
    leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)
    response = "📅 Weekly Leaderboard:\n"
    response += "\n".join([f"User  ID: {user_id}, Messages: {count}" for user_id, count in leaderboard])
    await message.reply_text(response)

# Command to display historical leaderboard
@app.on_message(filters.command("history"))
async def history(_, message):
    date = message.text.split()[1] if len(message.text.split()) > 1 else time.strftime("%Y-%m-%d")
    historical_data = history_db.find_one({"date": date})
    
    if historical_data:
        leaderboard = historical_data['leaderboard']
        response = "📜 Historical Leaderboard:\n" + "\n".join([f"User  ID: {user_id}, Messages: {count}" for user_id, count in leaderboard])
    else:
        response = "No data found for the specified date."
    
    await message.reply_text(response)
