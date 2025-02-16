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
week = {}  # Add in-memory storage for the week data

# Watcher for today's messages
from datetime import datetime

# Helper function to get the current week number
def get_current_week():
    return datetime.now().isocalendar()[1]

# Watcher for today's messages and weekly messages
@app.on_message(filters.group & filters.group, group=6)
# Watcher for today's messages
@app.on_message(filters.group & filters.group, group=6)
def today_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        current_week = get_current_week()  # Get current week number
        
        # Update today's messages in MongoDB
        today_record = rankdb.find_one({"_id": user_id, "chat_id": chat_id, "type": "today"})
        if today_record:
            rankdb.update_one(
                {"_id": user_id, "chat_id": chat_id, "type": "today"},
                {"$inc": {"total_messages": 1}},
                upsert=True
            )
        else:
            rankdb.insert_one({
                "_id": user_id,
                "chat_id": chat_id,
                "type": "today",
                "total_messages": 1
            })
        
        # Update weekly messages
        week_record = rankdb.find_one({"_id": user_id, "chat_id": chat_id, "type": "week", "week": current_week})
        if week_record:
            rankdb.update_one(
                {"_id": user_id, "chat_id": chat_id, "type": "week", "week": current_week},
                {"$inc": {"total_messages": 1}},
                upsert=True
            )
        else:
            rankdb.insert_one({
                "_id": user_id,
                "chat_id": chat_id,
                "type": "week",
                "week": current_week,
                "total_messages": 1
            })
    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Watcher for overall messages
@app.on_message(filters.group & filters.group, group=11)
def _watcher(_, message):
    try:
        user_id = message.from_user.id    
        user_data.setdefault(user_id, {}).setdefault("total_messages", 0)
        user_data[user_id]["total_messages"] += 1    
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)
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

# Command to display the ranking with buttons
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
        await message.reply_text("Please select the leaderboard type:", reply_markup=button)
    except Exception as e:
        logger.error(f"Error in ranking command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Callback query for today, week, and overall leaderboard
@app.on_callback_query(filters.regex("^(today|week|overall)$"))
async def leaderboard_callback(_, query):
    try:
        # Get the selection
        selection = query.data
        chat_id = query.message.chat.id

        # Determine the leaderboard data based on the selected option
        if selection == "today":
            data = list(rankdb.find({"chat_id": chat_id, "type": "today"}))
            time_frame = "Today's Leaderboard"
            button_texts = [
                "✅ Today",
                "Week",
                "Overall"
            ]
        elif selection == "week":
            current_week = get_current_week()
            data = list(rankdb.find({"chat_id": chat_id, "type": "week", "week": current_week}))
            time_frame = "This Week's Leaderboard"
            button_texts = [
                "Today",
                "✅ Week",
                "Overall"
            ]
        elif selection == "overall":
            data = list(rankdb.find({"type": "overall"}).sort("total_messages", -1).limit(10))
            time_frame = "Overall Leaderboard"
            button_texts = [
                "Today",
                "Week",
                "✅ Overall"
            ]

        # Sort the data and generate the leaderboard text
        sorted_data = sorted(data, key=lambda x: x['total_messages'], reverse=True)
        
        if sorted_data:
            response = f"⬤ 📈 {time_frame}\n\n"
            users_data = []
            for idx, record in enumerate(sorted_data[:10], start=1):
                user_id = record["_id"]
                user_name = (await app.get_users(user_id)).first_name if "first_name" in await app.get_users(user_id) else "Unknown"
                total_messages = record["total_messages"]
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info
                users_data.append((user_name, total_messages))

            # Generate the graph
            graph = generate_horizontal_bar_chart(users_data, time_frame)
            if graph:
                # Modify buttons with the appropriate active button
                button = InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(button_texts[0], callback_data="today"),
                        InlineKeyboardButton(button_texts[1], callback_data="week"),
                        InlineKeyboardButton(button_texts[2], callback_data="overall")
                    ]]
                )
                await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=button)
            else:
                await query.answer("Error generating graph.")
        else:
            await query.answer(f"❅ No data available for {selection}.")
    except Exception as e:
        logger.error(f"Error in leaderboard callback: {e}")
        await query.answer("An error occurred while processing the callback.")
