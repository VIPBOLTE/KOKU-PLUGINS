from pyrogram import filters
from pymongo import MongoClient
from KOKUMUISC import app
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
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from pytz import timezone
import matplotlib.pyplot as plt
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

# In-memory data storage (will also sync with MongoDB)
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
@app.on_message(filters.group & filters.group, group=11)
def _watcher(_, message):
    try:
        user_id = message.from_user.id    
        user_data.setdefault(user_id, {}).setdefault("total_messages", 0)
        user_data[user_id]["total_messages"] += 1    
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)
        
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

# Command to display rankings
@app.on_message(filters.command("ranking"))
async def rankin(_, message):
    try:
        # Default to overall ranking
        sorted_users_data = sorted(overall.items(), key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            total_messages_count = sum(messages for user_id, messages in sorted_users_data)
            
            response = f"⬤ 📈 ᴏᴠᴇʀᴀʟʟ ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: {total_messages_count}\n\n"

            for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                try:
                    user_name = (await app.get_users(user_id)).first_name
                except:
                    user_name = "Unknown"
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info
            
            # Generate horizontal bar chart for overall leaderboard
            graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_id, total_messages in sorted_users_data], "Overall Leaderboard")
            
            if graph:
                button = InlineKeyboardMarkup(
                    [[    
                       InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ✅", callback_data="overall"),
                       InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    ],
                    [
                       InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                    ]]
                )
                await message.reply_photo(graph, caption=response, reply_markup=button)
            else:
                await message.reply_text("Error generating graph.")
        else:
            await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴏᴠᴇʀᴀʟʟ.")
    except Exception as e:
        logger.error(f"Error in rankin command: {e}")
        await message.reply_text("An error occurred while processing the command.")

@app.on_callback_query(filters.regex(r"^overall"))
async def overall_callback(client, callback_query):
    await asyncio.sleep(1)  # Sleep for 1 second
    chat_id = callback_query.message.chat.id
    sorted_users_data = sorted(overall.items(), key=lambda x: x[1], reverse=True)[:10]

    if sorted_users_data:
        total_messages_count = sum(messages for user_id, messages in sorted_users_data)
        
        response = f"⬤ 📈 ᴏᴠᴇʀᴀʟʟ ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: {total_messages_count}\n\n"

        for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
            response += user_info
        
        graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_id, total_messages in sorted_users_data], "Overall Leaderboard")
        
        if graph:
            button = InlineKeyboardMarkup(
                [[    
                   InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ✅", callback_data="overall"),
                   InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                ],
                [
                   InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                ]]
            )
            await callback_query.message.edit_media(media=InputMediaPhoto(graph))
            await callback_query.message.edit_text(response, reply_markup=button)
        else:
            await callback_query.message.reply_text("Error generating graph.")
    else:
        await callback_query.message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴏᴠᴇʀᴀʟʟ.")


@app.on_callback_query(filters.regex(r"^weekly"))
async def weekly_callback(client, callback_query):
    await asyncio.sleep(1)  # Sleep for 1 second
    chat_id = callback_query.message.chat.id
    if chat_id in weekly:
        current_week = time.strftime("%U")
        users_data = []
        for user_id, user_data in weekly[chat_id].items():
            if current_week in user_data:
                users_data.append((user_id, user_data[current_week]))

        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            total_messages_count = sum(user_data[1] for user_data in sorted_users_data)
            
            response = f"⬤ 📈 ᴡᴇᴇᴋʟʏ ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: {total_messages_count}\n\n"

            for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                try:
                    user_name = (await app.get_users(user_id)).first_name
                except:
                    user_name = "Unknown"
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info
            
            graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_id, total_messages in sorted_users_data], "Weekly Leaderboard")
            
            if graph:
                button = InlineKeyboardMarkup(
                    [[    
                       InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                       InlineKeyboardButton("ᴡᴇᴇᴋʟʏ ✅", callback_data="weekly"),
                    ],
                    [
                       InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                    ]]
                )
                await callback_query.message.edit_media(media=InputMediaPhoto(graph))
                await callback_query.message.edit_text(response, reply_markup=button)
            else:
                await callback_query.message.reply_text("Error generating graph.")
        else:
            await callback_query.message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴡᴇᴇᴋ.")
    else:
        await callback_query.message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴡᴇᴇᴋ.")

@app.on_callback_query(filters.regex(r"^today"))
async def today_callback(client, callback_query):
    await asyncio.sleep(1)  # Sleep for 1 second
    chat_id = callback_query.message.chat.id
    if chat_id in today:
        users_data = [(user_id, user_data["total_messages"]) for user_id, user_data in today[chat_id].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

        if sorted_users_data:
            total_messages_count = sum(user_data['total_messages'] for user_data in today[chat_id].values())
            
            response = f"⬤ 📈 ᴛᴏᴅᴀʏ ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: {total_messages_count}\n\n"

            for idx, (user_id, total_messages) in enumerate(sorted_users_data, start=1):
                try:
                    user_name = (await app.get_users(user_id)).first_name
                except:
                    user_name = "Unknown"
                user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
                response += user_info
            
            graph = generate_horizontal_bar_chart([(user_name, total_messages) for user_id, total_messages in sorted_users_data], "Today's Leaderboard")
            
            if graph:
                button = InlineKeyboardMarkup(
                    [[    
                       InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                       InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                    ],
                    [
                       InlineKeyboardButton("ᴛᴏᴅᴀʏ ✅", callback_data="today"),
                    ]]
                )
                await callback_query.message.edit_media(media=InputMediaPhoto(graph))
                await callback_query.message.edit_text(response, reply_markup=button)
            else:
                await callback_query.message.reply_text("Error generating graph.")
        else:
            await callback_query.message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")
    else:
        await callback_query.message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")
