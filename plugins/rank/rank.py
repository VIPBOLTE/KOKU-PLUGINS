from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from pymongo import MongoClient
from pymongo.errors import ConnectionFailure
import logging
import time
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
import matplotlib.pyplot as plt
import io
from KOKUMUSIC import app
# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client['Champu']
    rankdb = db['Rankingdb']
except ConnectionFailure as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# In-memory data storage
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

# Function to generate a horizontal bar chart
def generate_horizontal_bar_chart(data, title):
    users = [user[0] for user in data]
    messages = [user[1] for user in data]

    plt.figure(figsize=(10, 6))
    plt.barh(users, messages, color='skyblue')
    plt.xlabel('Total Messages')
    plt.ylabel('Users')
    plt.title(title)

    for index, value in enumerate(messages):
        plt.text(value, index, str(value))

    buf = io.BytesIO()
    plt.savefig(buf, format='png', bbox_inches='tight')
    buf.seek(0)
    plt.close()
    return buf

# Command to display ranking
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    chat_id = message.chat.id
    buttons = [
        [InlineKeyboardButton("Today ✅", callback_data="today"), 
         InlineKeyboardButton("Weekly", callback_data="weekly"), 
         InlineKeyboardButton("Overall", callback_data="overall")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)
    await message.reply_text("Choose a ranking option:", reply_markup=reply_markup)

    # Automatically show today's leaderboard
    await show_leaderboard(chat_id, message, "today")

# Function to show leaderboard based on the selected option
async def show_leaderboard(chat_id, message, option):
    if option == "today":
        leaderboard = sorted(today.get(chat_id, {}).items(), key=lambda x: x[1]["total_messages"], reverse=True)[:10]
        response = "📊 Today's Top 10 Leaderboard:\n"
        response += "\n".join([f"User  ID: {user_id}, Messages: {data['total_messages']}" for user_id, data in leaderboard])
        graph = generate_horizontal_bar_chart([(user_id, data['total_messages']) for user_id, data in leaderboard], "Today's Leaderboard")
    elif option == "weekly":
        leaderboard = {}
        for user_id, weeks in weekly.get(chat_id, {}).items():
            total_messages = sum(weeks.values())
            leaderboard[user_id] = total_messages
        leaderboard = sorted(leaderboard.items(), key=lambda x: x[1], reverse=True)[:10]
        response = "📅 Weekly Top 10 Leaderboard:\n"
        response += "\n".join([f"User  ID: {user_id}, Messages: {count}" for user_id, count in leaderboard])
        graph = generate_horizontal_bar_chart([(user_id, count) for user_id, count in leaderboard], "Weekly Leaderboard")
    elif option == "overall":
        leaderboard = sorted(overall.items(), key=lambda x: x[1], reverse=True)[:10]
        response = "📈 Overall Top 10 Leaderboard:\n"
        response += "\n".join([f"User  ID: {user_id}, Messages: {count}" for user_id, count in leaderboard])
        graph = generate_horizontal_bar_chart([(user_id, count) for user_id, count in leaderboard], "Overall Leaderboard")

    # Send the leaderboard and the graph
    await message.reply_text(response)
    await message.reply_photo(graph)

# Callback query handler for ranking buttons
@app.on_callback_query(filters.regex("^(today|weekly|overall)$"))
async def ranking_callback(client, callback_query):
    chat_id = callback_query.message.chat.id
    data = callback_query.data

    # Prepare buttons with ✅ for the selected option
    buttons = [
        [InlineKeyboardButton(f"Today {'✅' if data == 'today' else ''}", callback_data="today"), 
         InlineKeyboardButton(f"Weekly {'✅' if data == 'weekly' else ''}", callback_data="weekly"), 
         InlineKeyboardButton(f"Overall {'✅' if data == 'overall' else ''}", callback_data="overall")]
    ]
    reply_markup = InlineKeyboardMarkup(buttons)

    # Show the leaderboard for the selected option
    await show_leaderboard(chat_id, callback_query.message, data)

    # Edit the message to update the buttons
    await callback_query.message.edit_text("Choose a ranking option:", reply_markup=reply_markup)
