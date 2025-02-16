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
@app.on_message(filters.group & filters.group, group=6)
def today_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        if chat_id in today and user_id in today[chat_id]:
            today[chat_id][user_id]["total_messages"] += 1
        else:
            if chat_id not in today:
                today[chat_id] = {}
            if user_id not in today[chat_id]:
                today[chat_id][user_id] = {"total_messages": 1}
            else:
                today[chat_id][user_id]["total_messages"] = 1
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
            data = today.get(chat_id, {})
            time_frame = "Today's Leaderboard"
        elif selection == "week":
            data = week.get(chat_id, {})  # You'll need to track weekly data
            time_frame = "This Week's Leaderboard"
        elif selection == "overall":
            data = rankdb.find().sort("total_messages", -1).limit(10)
            time_frame = "Overall Leaderboard"

        # Sort the data
        sorted_data = sorted(data.items(), key=lambda x: x[1]["total_messages"] if isinstance(x[1], dict) else x[1], reverse=True)
        
        if sorted_data:
            response = f"⬤ 📈 {time_frame}\n\n"
            users_data = []
            for idx, (user_id, total_messages) in enumerate(sorted_data[:10], start=1):
                if isinstance(total_messages, dict):
                    total_messages = total_messages["total_messages"]
                try:
                    user_name = (await app.get_users(user_id)).first_name
                except:
                    user_name = "Unknown"
                
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info
                users_data.append((user_name, total_messages))

            # Generate the graph
            graph = generate_horizontal_bar_chart(users_data, time_frame)
            if graph:
                # Modify buttons with checkmark based on selection
                button = InlineKeyboardMarkup(
                    [[
                        InlineKeyboardButton(f"✅ Today", callback_data="today"),
                        InlineKeyboardButton(f"Week", callback_data="week"),
                        InlineKeyboardButton(f"Overall", callback_data="overall")
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
