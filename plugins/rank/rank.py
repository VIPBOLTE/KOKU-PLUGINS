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
from datetime import datetime

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

# In-memory data storage (optional, adjust as needed)
user_data = {}

# Helper function to get current week number
def get_current_week():
    return datetime.now().isocalendar()[1]

# Watcher for today's and weekly messages
@app.on_message(filters.group, group=6)
async def today_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        current_week = get_current_week()

        # Update today's messages
        today_filter = {"_id": user_id, "chat_id": chat_id, "type": "today"}
        rankdb.update_one(today_filter, {"$inc": {"total_messages": 1}}, upsert=True)

        # Update weekly messages
        week_filter = {"_id": user_id, "chat_id": chat_id, "type": "week", "week": current_week}
        rankdb.update_one(week_filter, {"$inc": {"total_messages": 1}}, upsert=True)
    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Watcher for overall messages (per chat)
@app.on_message(filters.group, group=11)
async def overall_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Update overall messages for the user in this chat
        overall_filter = {"_id": user_id, "chat_id": chat_id, "type": "overall"}
        rankdb.update_one(overall_filter, {"$inc": {"total_messages": 1}}, upsert=True)
    except Exception as e:
        logger.error(f"Error in overall_watcher: {e}")

# Generate horizontal bar chart
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

# /ranking command handler
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    try:
        button = InlineKeyboardMarkup(
            [[
                InlineKeyboardButton("Today", callback_data="today"),
                InlineKeyboardButton("Week", callback_data="week"),
                InlineKeyboardButton("Overall", callback_data="overall")
            ]]
        )
        await message.reply_text("Select leaderboard type:", reply_markup=button)
    except Exception as e:
        logger.error(f"Error in /ranking: {e}")
        await message.reply_text("An error occurred.")

# Callback handler for leaderboard buttons
@app.on_callback_query(filters.regex("^(today|week|overall)$"))
async def leaderboard_callback(_, query):
    try:
        selection = query.data
        chat_id = query.message.chat.id
        time_frame = ""
        button_texts = ["Today", "Week", "Overall"]

        # Determine active button and fetch data
        if selection == "today":
            data = list(rankdb.find({"chat_id": chat_id, "type": "today"}).sort("total_messages", -1).limit(10))
            time_frame = "Today's Leaderboard"
            button_texts[0] = "✅ Today"
        elif selection == "week":
            current_week = get_current_week()
            data = list(rankdb.find({"chat_id": chat_id, "type": "week", "week": current_week}).sort("total_messages", -1).limit(10))
            time_frame = "This Week's Leaderboard"
            button_texts[1] = "✅ Week"
        elif selection == "overall":
            data = list(rankdb.find({"chat_id": chat_id, "type": "overall"}).sort("total_messages", -1).limit(10))
            time_frame = "Overall Leaderboard"
            button_texts[2] = "✅ Overall"

        # Prepare leaderboard text
        if not data:
            await query.answer("No data available yet.", show_alert=True)
            return

        response = f"⬤ 📈 {time_frame}\n\n"
        users_data = []
        for idx, record in enumerate(data, start=1):
            user_id = record["_id"]
            try:
                user = await app.get_users(user_id)
                user_name = user.first_name
            except:
                user_name = "Unknown"
            total_msgs = record["total_messages"]
            response += f"{idx}. {user_name} ➥ {total_msgs}\n"
            users_data.append((user_name, total_msgs))

        # Generate and send graph
        graph = generate_horizontal_bar_chart(users_data, time_frame)
        if not graph:
            await query.answer("Failed to generate graph.")
            return

        media = InputMediaPhoto(graph, caption=response)
        button = InlineKeyboardMarkup([[InlineKeyboardButton(t, callback_data=c)] for t, c in zip(button_texts, ["today", "week", "overall"])])
        
        await query.message.edit_media(media, reply_markup=button)
        await query.answer()
    except MessageNotModified:
        await query.answer()
    except Exception as e:
        logger.error(f"Leaderboard callback error: {e}")
        await query.answer("An error occurred.")
