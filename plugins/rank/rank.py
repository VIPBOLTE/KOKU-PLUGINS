from pyrogram import Client, filters
from pyrogram.types import *
from pymongo import MongoClient
import logging
import pytz
from datetime import datetime, timedelta
import asyncio
from KOKUMUSIC import app
from pyrogram.types import *
from pyrogram.errors import MessageNotModified
from pyrogram.types import (CallbackQuery, InlineKeyboardButton,
                            InlineKeyboardMarkup, Message)
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
# MongoDB setup
client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/')
db = client['Champu']
rankdb = db['Rankingdb']
weeklydb = db['WeeklyRankingdb']
todaydb = db['TodayRankingdb']

# Timezone setup
timezone = pytz.timezone('Asia/Kolkata')

# Logging setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Combined Watcher for Today, Weekly, and Overall Messages
@app.on_message(filters.group)
def message_watcher(_, message):
    try:
        user_id = message.from_user.id
        chat_id = message.chat.id
        current_time = datetime.now(timezone)

        # Update overall message count
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)

        # Update today's message count
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        todaydb.update_one(
            {"_id": user_id, "date": today_start.strftime('%Y-%m-%d')},
            {"$inc": {"total_messages": 1}},
            upsert=True
        )

        # Update weekly message count
        week_start = current_time - timedelta(days=current_time.weekday())  # Sunday of this week
        weeklydb.update_one(
            {"_id": user_id, "week_start": week_start.strftime('%Y-%m-%d')},
            {"$inc": {"total_messages": 1}},
            upsert=True
        )

    except Exception as e:
        logger.error(f"Error in message_watcher: {e}")

# Command to show ranking (Today, Weekly, Overall)
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    try:
        button = InlineKeyboardMarkup([
            [InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today")],
            [InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly")],
            [InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall")]
        ])
        await message.reply_text("⬤ 📈 ᴄʜᴏᴏsᴇ ᴀ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ:", reply_markup=button)

    except Exception as e:
        logger.error(f"Error in ranking command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Callback for Today's Leaderboard
@app.on_callback_query(filters.regex("today"))
async def today_rank(_, query):
    try:
        current_time = datetime.now(timezone)
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
        today_start_str = today_start.strftime('%Y-%m-%d')

        top_users = todaydb.find({"date": today_start_str}).sort("total_messages", -1).limit(10)
        response = "⬤ 📈 Today's Top Users\n\n"
        for idx, user in enumerate(top_users, start=1):
            user_id = user["_id"]
            total_messages = user["total_messages"]
            user_name = (await app.get_users(user_id)).first_name
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
        
        await query.message.edit_text(response)

    except Exception as e:
        logger.error(f"Error in today_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Callback for Weekly Leaderboard
@app.on_callback_query(filters.regex("weekly"))
async def weekly_rank(_, query):
    try:
        current_time = datetime.now(timezone)
        week_start = current_time - timedelta(days=current_time.weekday())  # Sunday of this week
        week_start_str = week_start.strftime('%Y-%m-%d')

        top_users = weeklydb.find({"week_start": week_start_str}).sort("total_messages", -1).limit(10)
        response = "⬤ 📈 Weekly Leaderboard (Sunday to Saturday)\n\n"
        for idx, user in enumerate(top_users, start=1):
            user_id = user["_id"]
            total_messages = user["total_messages"]
            user_name = (await app.get_users(user_id)).first_name
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
        
        await query.message.edit_text(response)

    except Exception as e:
        logger.error(f"Error in weekly_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")

# Callback for Overall Leaderboard
@app.on_callback_query(filters.regex("overall"))
async def overall_rank(_, query):
    try:
        top_users = rankdb.find().sort("total_messages", -1).limit(10)
        response = "⬤ 📈 Overall Leaderboard\n\n"
        for idx, user in enumerate(top_users, start=1):
            user_id = user["_id"]
            total_messages = user["total_messages"]
            user_name = (await app.get_users(user_id)).first_name
            response += f"{idx}. {user_name} ➥ {total_messages}\n"
        
        await query.message.edit_text(response)

    except Exception as e:
        logger.error(f"Error in overall_rank callback: {e}")
        await query.answer("An error occurred while processing the callback.")
