from pyrogram import filters
from pymongo import MongoClient
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.server_info()
    db = client['Champu']
    rankdb = db['Rankingdb']
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# In-memory data storage
user_data = {}
today = {}

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
            today[chat_id][user_id] = {"total_messages": 1}
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

# Command to display leaderboard (default: Overall)
@app.on_message(filters.command("ranking"))
async def ranking(_, message):
    try:
        # Fetch overall leaderboard
        top_members = rankdb.find().sort("total_messages", -1).limit(10)

        response = "⬤ 📈 ᴄᴜʀʀᴇɴᴛ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, start=1):
            user_id = member["_id"]
            total_messages = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
            response += user_info
            users_data.append((user_name, total_messages))
        
        # Generate chart
        graph = generate_horizontal_bar_chart(users_data, "Overall Leaderboard")
        
        if graph:
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Today", callback_data="today"),
                        InlineKeyboardButton("Overall", callback_data="overall")
                    ]
                ]
            )
            await message.reply_photo(graph, caption=response, reply_markup=buttons, has_spoiler=True)
        else:
            await message.reply_text("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in ranking command: {e}")
        await message.reply_text("An error occurred.")

# Callback for Today leaderboard
@app.on_callback_query(filters.regex("today"))
async def today_rank(_, query):
    try:
        chat_id = query.message.chat.id
        if chat_id in today:
            users_data = [(user_id, data["total_messages"]) for user_id, data in today[chat_id].items()]
            sorted_users = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

            if sorted_users:
                response = "⬤ 📈 ᴛᴏᴅᴀʏ's ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
                user_chart_data = []
                for idx, (user_id, count) in enumerate(sorted_users, start=1):
                    try:
                        user_name = (await app.get_users(user_id)).first_name
                    except:
                        user_name = "Unknown"
                    response += f"{idx}.   {user_name} ➥ {count}\n"
                    user_chart_data.append((user_name, count))
                
                # Generate chart
                graph = generate_horizontal_bar_chart(user_chart_data, "Today's Leaderboard")
                
                if graph:
                    buttons = InlineKeyboardMarkup(
                        [
                            [
                                InlineKeyboardButton("Today", callback_data="today"),
                                InlineKeyboardButton("Overall", callback_data="overall")
                            ]
                        ]
                    )
                    await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=buttons)
                else:
                    await query.answer("Error generating chart.")
            else:
                await query.answer("No data available for today.")
        else:
            await query.answer("No data available for today.")
    except Exception as e:
        logger.error(f"Error in today_rank: {e}")
        await query.answer("An error occurred.")

# Callback for Overall leaderboard
@app.on_callback_query(filters.regex("overall"))
async def overall_rank(_, query):
    try:
        top_members = rankdb.find().sort("total_messages", -1).limit(10)
        response = "⬤ 📈 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        chart_data = []
        for idx, member in enumerate(top_members, start=1):
            user_id = member["_id"]
            total_msg = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            response += f"{idx}.   {user_name} ➥ {total_msg}\n"
            chart_data.append((user_name, total_msg))
        
        # Generate chart
        graph = generate_horizontal_bar_chart(chart_data, "Overall Leaderboard")
        
        if graph:
            buttons = InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton("Today", callback_data="today"),
                        InlineKeyboardButton("Overall", callback_data="overall")
                    ]
                ]
            )
            await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=buttons)
        else:
            await query.answer("Error generating chart.")
    except Exception as e:
        logger.error(f"Error in overall_rank: {e}")
        await query.answer("An error occurred.")
