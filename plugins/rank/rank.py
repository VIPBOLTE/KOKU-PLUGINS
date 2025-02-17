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
import logging
from datetime import datetime, timedelta
import pytz

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection with error handling
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/')
    client.server_info()  # Test connection
    db = client['Champu']
    rankdb = db['Rankingdb']
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Time zone for India (or your preferred time zone)
IST = pytz.timezone("Asia/Kolkata")

# Helper function to get today's date and start of the week
def get_today_date():
    today = datetime.now(IST)
    return today.date()

def get_start_of_week():
    today = datetime.now(IST)
    start_of_week = today - timedelta(days=today.weekday())  # Monday
    return start_of_week.date()

# In-memory data storage
user_data = {}
today = {}
weekly = {}

# Watcher for today's messages
@app.on_message(filters.group & filters.group, group=6)
def today_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        today_date = get_today_date()

        if chat_id not in today:
            today[chat_id] = {}
        
        if user_id not in today[chat_id]:
            today[chat_id][user_id] = {"total_messages": 0, "date": today_date}
        
        # Update today's message count
        today[chat_id][user_id]["total_messages"] += 1
    except Exception as e:
        logger.error(f"Error in today_watcher: {e}")

# Watcher for weekly messages
@app.on_message(filters.group & filters.group, group=11)
def weekly_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        start_of_week = get_start_of_week()

        if chat_id not in weekly:
            weekly[chat_id] = {}

        if user_id not in weekly[chat_id]:
            weekly[chat_id][user_id] = {"total_messages": 0, "start_of_week": start_of_week}

        # Check if the week has changed
        if weekly[chat_id][user_id]["start_of_week"] != start_of_week:
            weekly[chat_id][user_id] = {"total_messages": 0, "start_of_week": start_of_week}

        # Update weekly message count
        weekly[chat_id][user_id]["total_messages"] += 1
    except Exception as e:
        logger.error(f"Error in weekly_watcher: {e}")

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

# Command to display the ranking
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    try:
        # Create buttons for Today, Weekly, and Overall
        button = InlineKeyboardMarkup(
            [
                [InlineKeyboardButton("Today", callback_data="today")],
                [InlineKeyboardButton("Weekly", callback_data="weekly")],
                [InlineKeyboardButton("Overall", callback_data="overall")]
            ]
        )
        await message.reply_text("⬤ 📈 Choose a leaderboard:", reply_markup=button)
    except Exception as e:
        logger.error(f"Error in ranking command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Callback query for today's leaderboard
@app.on_callback_query(filters.regex("today"))
async def today_rank(_, query):
    try:
        chat_id = query.message.chat.id
        if chat_id in today:
            users_data = [(user_id, user_data["total_messages"]) for user_id, user_data in today[chat_id].items()]
            sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

            if sorted_users_data:
                response = "⬤ 📈 Today's Leaderboard\n\n"
                for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                    try:
                        user_name = (await app.get_users(user_id)).first_name
                    except:
                        user_name = "Unknown"
                    user_info = f"{idx}. {user_name} ➥ {total_messages}\n"
                    response += user_info
                
                # Generate horizontal bar chart
                graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_id, total_messages in sorted_users_data], "Today's Leaderboard")
                
                if graph:
                    button = InlineKeyboardMarkup([[InlineKeyboardButton("Overall Leaderboard", callback_data="overall")]])
                    await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=button)
                else:
                    await query.answer("Error generating graph.")
            else:
                await query.answer("No data available for today.")
        else:
            await query.answer("No data available for today.")
    except Exception as e:
        logger.error(f"Error in today_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Callback query for weekly leaderboard
@app.on_callback_query(filters.regex("weekly"))
async def weekly_rank(_, query):
    try:
        chat_id = query.message.chat.id
        if chat_id in weekly:
            users_data = [(user_id, user_data["total_messages"]) for user_id, user_data in weekly[chat_id].items()]
            sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

            if sorted_users_data:
                response = "⬤ 📈 Weekly Leaderboard\n\n"
                for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                    try:
                        user_name = (await app.get_users(user_id)).first_name
                    except:
                        user_name = "Unknown"
                    user_info = f"{idx}. {user_name} ➥ {total_messages}\n"
                    response += user_info
                
                # Generate horizontal bar chart
                graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_id, total_messages in sorted_users_data], "Weekly Leaderboard")
                
                if graph:
                    button = InlineKeyboardMarkup([[InlineKeyboardButton("Overall Leaderboard", callback_data="overall")]])
                    await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=button)
                else:
                    await query.answer("Error generating graph.")
            else:
                await query.answer("No data available for this week.")
        else:
            await query.answer("No data available for this week.")
    except Exception as e:
        logger.error(f"Error in weekly_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Callback query for overall leaderboard
@app.on_callback_query(filters.regex("overall"))
async def overall_rank(_, query):
    try:
        top_members = rankdb.find().sort("total_messages", -1).limit(10)

        response = "⬤ 📈 Overall Leaderboard\n\n"
        users_data = []
        for idx, member in enumerate(top_members, start=1):
            user_id = member["_id"]
            total_messages = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"

            user_info = f"{idx}. {user_name} ➥ {total_messages}\n"
            response += user_info
            users_data.append((user_name, total_messages))
        
        # Generate horizontal bar chart
        graph = generate_horizontal_bar_chart(users_data, "Overall Leaderboard")
        
        if graph:
            button = InlineKeyboardMarkup([[InlineKeyboardButton("Today Leaderboard", callback_data="today")]])
            await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=button)
        else:
            await query.answer("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in overall_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")
