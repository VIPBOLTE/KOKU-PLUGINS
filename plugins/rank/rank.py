from pyrogram import filters, Client
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
            if current_week in weekly[chat_id][user_id]:
                weekly[chat_id][user_id][current_week] += 1
            else:
                weekly[chat_id][user_id][current_week] = 1
        
        # Save to MongoDB
        save_weekly_data_to_db(chat_id, user_id, current_week, weekly[chat_id][user_id][current_week])

    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Update the _watcher function to track overall message count
@app.on_message(filters.group & filters.group , group=11)
def _watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        if user_id not in overall:
            overall[user_id] = 1
        else:
            overall[user_id] += 1

        # Notify user if they reach a new milestone
        asyncio.create_task(check_rewards(user_id, overall[user_id]))

        # Save overall data to MongoDB
        rankdb.update_one(
            {"user_id": user_id},
            {"$set": {"total_messages": overall[user_id]}},
            upsert=True
        )

    except Exception as e:
        logger.error(f"Error in _watcher: {e}")

# Command to view today's stats
@app.on_message(filters.command("today"))
@rate_limit(10)
async def today_(_, message):
    user_id = message.from_user.id
    chat_id = message.chat.id
    today_count = today.get(chat_id, {}).get(user_id, {}).get("total_messages", 0)
    response = f"📅 Today's Messages: {today_count}"
    await message.reply_text(response)

# Command to view user profile
@app.on_message(filters.command("profile"))
async def profile(_, message):
    user_id = message.from_user.id
    today_count = today.get(message.chat.id, {}).get(user_id, {}).get("total_messages", 0)
    weekly_count = weekly.get(message.chat.id, {}).get(user_id, {}).get(time.strftime("%U"), 0)
    overall_count = overall.get(user_id, 0)
    response = f"📊 Your Stats:\nToday: {today_count}\nThis Week: {weekly_count}\nOverall: {overall_count}"
    await message.reply_text(response)

# Admin command to reset data
@app.on_message(filters.command("reset_data") & filters.user(ADMIN_IDS))
async def reset_data(_, message):
    global today, weekly, overall
    today = {}
    weekly = {}
    overall = {}
    await message.reply_text("All data has been reset.")

# Command to export leaderboard
@app.on_message(filters.command("export_leaderboard"))
async def export_leaderboard(_, message):
    format = message.text.split()[1] if len(message.text.split()) > 1 else "csv"
    sorted_users = sorted(overall.items(), key=lambda x: x[1], reverse=True)
    if format == "csv":
        with open("leaderboard.csv", "w", newline="") as file:
            writer = csv.writer(file)
            writer.writerow(["User  ID", "Messages"])
            writer.writerows(sorted_users)
        await message.reply_document("leaderboard.csv")
    elif format == "json":
        with open("leaderboard.json", "w") as file:
            json.dump(dict(sorted_users), file)
        await message.reply_document("leaderboard.json")

# Function to check rewards
async def check_rewards(user_id, count):
    for milestone, reward in rewards.items():
        if count == milestone:
            await app.send_message(user_id, f"🎉 You've earned a {reward} for sending {milestone} messages!")

# Command to customize leaderboard
@app.on_message(filters.command("customize_leaderboard"))
async def customize_leaderboard(_, message):
    user_id = message.from_user.id
    emoji = message.text.split()[1] if len(message.text.split()) > 1 else "👤"
    user_data[user_id]["emoji"] = emoji
    await message.reply_text(f"Your leaderboard emoji has been set to {emoji}.")
