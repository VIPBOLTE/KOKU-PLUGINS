from pyrogram import filters
from pymongo import MongoClient
from ChampuMusic import app
from pyrogram.types import *
from pyrogram.errors import MessageNotModified
from pyrogram.types import InputMediaPhoto
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
import time
from datetime import datetime, timedelta
import logging
import matplotlib.pyplot as plt
from PIL import Image
import io

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

# In-memory data storage (for weekly and daily data)
user_data_today = {}
user_data_weekly = {}

# Function to get the current date and time
def get_current_time():
    return datetime.now()

# Function to reset daily rankings at midnight
def reset_daily_data():
    current_time = get_current_time()
    # Check if it's midnight, and reset the 'today' rankings if it is
    if current_time.hour == 0 and current_time.minute == 0:
        logger.info("Resetting daily data.")
        user_data_today.clear()

# Function to reset weekly rankings on Sunday
def reset_weekly_data():
    current_time = get_current_time()
    if current_time.weekday() == 6 and current_time.hour == 0 and current_time.minute == 0:
        logger.info("Resetting weekly data.")
        user_data_weekly.clear()

# Function to generate a leaderboard graph using PIL and matplotlib
def generate_leaderboard_image(data, title):
    try:
        users = [user[0] for user in data]
        messages = [user[1] for user in data]
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.barh(users, messages, color='skyblue')
        ax.set_xlabel('Total Messages')
        ax.set_ylabel('Users')
        ax.set_title(title)
        
        for index, value in enumerate(messages):
            ax.text(value, index, str(value))
        
        # Save the plot to a buffer in PNG format
        buf = io.BytesIO()
        plt.savefig(buf, format='png', bbox_inches='tight')
        buf.seek(0)
        plt.close()
        
        # Use PIL to open the generated image from buffer
        img = Image.open(buf)
        return img
    except Exception as e:
        logger.error(f"Error generating leaderboard image: {e}")
        return None

# Command to display rankings
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    try:
        # Fetch the "Today" leaderboard data
        sorted_today_data = sorted(user_data_today.items(), key=lambda x: x[1]["total_messages"], reverse=True)[:10]
        
        # Prepare the response
        response = "⬤ 📈 Today's Leaderboard\n\n"
        users_data = []
        for idx, (user_id, user_data) in enumerate(sorted_today_data, start=1):
            user_name = user_data.get("name", "Unknown")
            total_messages = user_data["total_messages"]
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
            users_data.append((user_name, total_messages))

        # Generate the leaderboard image
        leaderboard_img = generate_leaderboard_image(users_data, "Today's Leaderboard")
        
        if leaderboard_img:
            # Save the image into a buffer
            buf = io.BytesIO()
            leaderboard_img.save(buf, format='PNG')
            buf.seek(0)
            
            # Buttons for Today, Weekly, and Overall rankings
            button = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Today", callback_data="today"),
                        InlineKeyboardButton("Weekly", callback_data="weekly"),
                        InlineKeyboardButton("Overall", callback_data="overall"),
                    ]
                ]
            )

            # Send the image as a reply with the buttons
            await message.reply_photo(buf, caption=response, reply_markup=button)
        else:
            await message.reply_text("Error generating leaderboard graph.")
    except Exception as e:
        logger.error(f"Error in ranking command: {e}")
        await message.reply_text("An error occurred while processing the ranking.")

# Callback query for switching between Today, Weekly, and Overall rankings
@app.on_callback_query(filters.regex("^(today|weekly|overall)$"))
async def leaderboard_switch(_, query):
    try:
        ranking_type = query.data
        if ranking_type == "today":
            # Handle the "Today" leaderboard
            sorted_data = sorted(user_data_today.items(), key=lambda x: x[1]["total_messages"], reverse=True)[:10]
            leaderboard_data = "Today's Leaderboard"
        elif ranking_type == "weekly":
            # Handle the "Weekly" leaderboard (similar logic for weekly as for today)
            sorted_data = sorted(user_data_weekly.items(), key=lambda x: x[1]["total_messages"], reverse=True)[:10]
            leaderboard_data = "Weekly Leaderboard"
        else:
            # Handle the "Overall" leaderboard
            sorted_data = sorted(rankdb.find().sort("total_messages", -1).limit(10), key=lambda x: x['total_messages'], reverse=True)
            leaderboard_data = "Overall Leaderboard"

        response = f"⬤ 📈 {leaderboard_data}\n\n"
        users_data = []
        for idx, (user_id, user_data) in enumerate(sorted_data, start=1):
            user_name = user_data.get("name", "Unknown")
            total_messages = user_data["total_messages"]
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
            users_data.append((user_name, total_messages))

        # Generate the leaderboard image
        leaderboard_img = generate_leaderboard_image(users_data, leaderboard_data)
        
        if leaderboard_img:
            buf = io.BytesIO()
            leaderboard_img.save(buf, format='PNG')
            buf.seek(0)

            # Buttons for switching between Today, Weekly, and Overall rankings
            button = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Today", callback_data="today"),
                        InlineKeyboardButton("Weekly", callback_data="weekly"),
                        InlineKeyboardButton("Overall", callback_data="overall"),
                    ]
                ]
            )

            # Update the message with the new leaderboard image
            await query.message.edit_media(InputMediaPhoto(buf, caption=response), reply_markup=button)
        else:
            await query.answer("Error generating leaderboard image.")
    except Exception as e:
        logger.error(f"Error in leaderboard switch callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Watcher for new messages (updating data)
@app.on_message(filters.group)
def message_watcher(_, message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        user_name = message.from_user.first_name
        
        # Daily message counting
        user_data_today.setdefault(user_id, {"total_messages": 0, "name": user_name})
        user_data_today[user_id]["total_messages"] += 1

        # Weekly message counting
        user_data_weekly.setdefault(user_id, {"total_messages": 0, "name": user_name})
        user_data_weekly[user_id]["total_messages"] += 1
        
        # Store data to MongoDB (overall leaderboard)
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)
    except Exception as e:
        logger.error(f"Error in message watcher: {e}")

# Cron job to reset daily and weekly rankings (use a scheduled task, for example with APScheduler)
# or custom implementation of time checking to reset every midnight.

