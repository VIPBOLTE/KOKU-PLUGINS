from pyrogram import filters
from pymongo import MongoClient
from KOKUMUSIC import app
from pyrogram.types import *
from pyrogram.errors import MessageNotModified
from pyrogram.types import InputMediaPhoto
from typing import Union
import asyncio
import random
import requests
import os
import time
from pyrogram.enums import ChatType
import config
import matplotlib.pyplot as plt
import io
import logging
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

# In-memory data storage (will also sync with MongoDB)
user_data = {}
today = {}
weekly = {}

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

# Define a global variable to track overall message counts
overall = {}

# Update the _watcher function to track overall message count
@app.on_message(filters.group & filters.group, group=11)
def _watcher(_, message):
    try:
        user_id = message.from_user.id    
        user_data.setdefault(user_id, {}).setdefault("total_messages", 0)
        user_data[user_id]["total_messages"] += 1    
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)
        
        # Save overall data to MongoDB
        rankdb.update_one(
            {"_id": user_id},
            {"$inc": {"total_messages": 1}},
            upsert=True
        )
        
        # Update overall dictionary
        if user_id not in overall:
            overall[user_id] = 1
        else:
            overall[user_id] += 1
        
    except Exception as e:
        logger.error(f"Error in _watcher: {e}")

# Function to generate a horizontal bar chart
def generate_horizontal_bar_chart(data, title):
    try:
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
    except Exception as e:
        logger.error(f"Error generating graph: {e}")
        return None

# Function to generate leaderboard response and chart
async def generate_leaderboard(chat_id, leaderboard_data, period="today"):
    try:
        if leaderboard_data:
            sorted_users_data = sorted(leaderboard_data, key=lambda x: x[1], reverse=True)[:10]
            total_messages_count = sum([user[1] for user in sorted_users_data])
            response = f"⬤ 📈 ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs ᴏᴠᴇʀ ᴛʜᴇ {period}: {total_messages_count}\n\n"

            for idx, (user_name, total_messages) in enumerate(sorted_users_data, start=1):
                response += f"{idx}.   {user_name} ➥ {total_messages}\n"

            graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_name, total_messages in sorted_users_data], f"{period.capitalize()} Leaderboard")

            if graph:
                button = InlineKeyboardMarkup([
                    [InlineKeyboardButton("ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="weekly"),
                     InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="overall")]
                ])
                await message.reply_photo(graph, caption=response, reply_markup=button, has_spoiler=True)
            else:
                await message.reply_text("Error generating graph.")
        else:
            await message.reply_text(f"❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜᴇ {period}.")
    except Exception as e:
        logger.error(f"Error in generate_leaderboard: {e}")
        await message.reply_text(f"An error occurred while processing the {period} leaderboard.")

# Command to display today's leaderboard
@app.on_message(filters.command("today"))
async def today_(_, message):
    try:
        chat_id = message.chat.id
        if chat_id in today:
            await generate_leaderboard(chat_id, [(user_id, data["total_messages"]) for user_id, data in today[chat_id].items()], "today")
        else:
            await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")
    except Exception as e:
        logger.error(f"Error in today_ command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Command to display weekly leaderboard
@app.on_message(filters.command("weekly"))
async def weekly_rank(_, message):
    try:
        chat_id = message.chat.id
        if chat_id in weekly:
            current_week = time.strftime("%U")
            weekly_data = [(user_id, user_data[current_week]) for user_id, user_data in weekly[chat_id].items() if current_week in user_data]
            await generate_leaderboard(chat_id, weekly_data, "weekly")
        else:
            await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴡᴇᴇᴋ.")
    except Exception as e:
        logger.error(f"Error in weekly_rank command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Command to display overall leaderboard
@app.on_message(filters.command("overall"))
async def overall_rank(_, message):
    try:
        # Sorting the overall leaderboard by message count
        sorted_users_data = sorted(overall.items(), key=lambda x: x[1], reverse=True)[:10]
        await generate_leaderboard(None, [(user_name, total_messages) for user_name, total_messages in sorted_users_data], "overall")
    except Exception as e:
        logger.error(f"Error in overall_rank command: {e}")
        await message.reply_text("An error occurred while processing the command.")
