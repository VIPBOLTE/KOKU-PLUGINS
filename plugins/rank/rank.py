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
import datetime
from concurrent.futures import ThreadPoolExecutor

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client['Champu']
    rankdb = db['Rankingdb']
    weeklydb = db['Weeklydb']
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# In-memory data storage
user_data = {}
today = {}

# Watchers
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

@app.on_message(filters.group & filters.group, group=11)
def _watcher(_, message):
    try:
        user_id = message.from_user.id    
        user_data.setdefault(user_id, {}).setdefault("total_messages", 0)
        user_data[user_id]["total_messages"] += 1    
        rankdb.update_one({"_id": user_id}, {"$inc": {"total_messages": 1}}, upsert=True)
        
        # Update weeklydb
        current_week = datetime.datetime.now().isocalendar()
        year, week_num, day = current_week
        current_week_str = f"{year}-W{week_num:02d}"
        weeklydb.update_one(
            {"user_id": user_id, "week": current_week_str},
            {"$inc": {"total_messages": 1}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error in _watcher: {e}")

# Graph generation
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

# Commands
@app.on_message(filters.command("today"))
async def today_(_, message):
    try:
        chat_id = message.chat.id
        if chat_id in today:
            users_data = [(user_id, data["total_messages"]) for user_id, data in today[chat_id].items()]
            sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]

            if sorted_users_data:
                total_messages = sum(data['total_messages'] for data in today[chat_id].values())
                response = f"⬤ 📈 ᴛᴏᴅᴀʏ's ᴛᴏᴛᴀʟ ᴍᴇssᴀɢᴇs: {total_messages}\n\n"
                
                users_chart_data = []
                for idx, (user_id, count) in enumerate(sorted_users_data, 1):
                    try:
                        user_name = (await app.get_users(user_id)).first_name
                    except:
                        user_name = "Unknown"
                    response += f"{idx}. {user_name} ➥ {count}\n"
                    users_chart_data.append((user_name, count))

                graph = generate_horizontal_bar_chart(users_chart_data, "Today's Leaderboard")
                if graph:
                    buttons = InlineKeyboardMarkup([
                        [InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                         InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                         InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today")]
                    ])
                    await message.reply_photo(graph, caption=response, reply_markup=buttons, has_spoiler=True)
                else:
                    await message.reply_text("Error generating graph.")
            else:
                await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ.")
        else:
            await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛᴏᴅᴀʏ.")
    except Exception as e:
        logger.error(f"Error in today_: {e}")
        await message.reply_text("An error occurred.")

@app.on_message(filters.command("ranking"))
async def overall_ranking(_, message):
    try:
        top_members = rankdb.find().sort("total_messages", -1).limit(10)
        response = "⬤ 📈 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, 1):
            user_id = member["_id"]
            total = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            response += f"{idx}. {user_name} ➥ {total}\n"
            users_data.append((user_name, total))
        
        graph = generate_horizontal_bar_chart(users_data, "Overall Leaderboard")
        if graph:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                 InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                 InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall")]
            ])
            await message.reply_photo(graph, caption=response, reply_markup=buttons, has_spoiler=True)
        else:
            await message.reply_text("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in ranking: {e}")
        await message.reply_text("An error occurred.")

@app.on_message(filters.command("weekly"))
@app.on_message(filters.command("weekly"))
async def weekly_ranking(_, message):
    try:
        current_week = datetime.datetime.now().isocalendar()
        year, week_num, day = current_week
        current_week_str = f"{year}-W{week_num:02d}"
        
        loop = asyncio.get_event_loop()
        top_members = await loop.run_in_executor(
            ThreadPoolExecutor(),
            lambda: list(weeklydb.find({"week": current_week_str}).sort("total_messages", -1).limit(10))
        )  # Missing parenthesis added here

        if not top_members:
            await message.reply_text("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜɪs ᴡᴇᴇᴋ.")
            return
        
        response = "⬤ 📈 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, 1):
            user_id = member["user_id"]
            total = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            response += f"{idx}. {user_name} ➥ {total}\n"
            users_data.append((user_name, total))
        
        graph = generate_horizontal_bar_chart(users_data, "Weekly Leaderboard")
        if graph:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                 InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                 InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall")]
            ])
            await message.reply_photo(graph, caption=response, reply_markup=buttons, has_spoiler=True)
        else:
            await message.reply_text("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in weekly_ranking: {e}")
        await message.reply_text("An error occurred.")
# Callbacks
@app.on_callback_query(filters.regex("today"))
async def today_callback(_, query):
    try:
        chat_id = query.message.chat.id
        if chat_id not in today:
            await query.answer("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ.")
            return
        
        users_data = [(user_id, data["total_messages"]) for user_id, data in today[chat_id].items()]
        sorted_users_data = sorted(users_data, key=lambda x: x[1], reverse=True)[:10]
        
        response = f"⬤ 📈 ᴛᴏᴅᴀʏ's ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_chart_data = []
        for idx, (user_id, count) in enumerate(sorted_users_data, 1):
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            response += f"{idx}. {user_name} ➥ {count}\n"
            users_chart_data.append((user_name, count))
        
        graph = generate_horizontal_bar_chart(users_chart_data, "Today's Leaderboard")
        if graph:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                 InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall"),
                 InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today")]
            ])
            await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=buttons)
        else:
            await query.answer("Error updating leaderboard.")
    except Exception as e:
        logger.error(f"Error in today_callback: {e}")
        await query.answer("An error occurred.")

@app.on_callback_query(filters.regex("overall"))
async def overall_callback(_, query):
    try:
        top_members = rankdb.find().sort("total_messages", -1).limit(10)
        response = "⬤ 📈 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, 1):
            user_id = member["_id"]
            total = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            response += f"{idx}. {user_name} ➥ {total}\n"
            users_data.append((user_name, total))
        
        graph = generate_horizontal_bar_chart(users_data, "Overall Leaderboard")
        if graph:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                 InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                 InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall")]
            ])
            await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=buttons)
        else:
            await query.answer("Error updating leaderboard.")
    except Exception as e:
        logger.error(f"Error in overall_callback: {e}")
        await query.answer("An error occurred.")

@app.on_callback_query(filters.regex("weekly"))
async def weekly_callback(_, query):
    try:
        current_week = datetime.datetime.now().isocalendar()
        year, week_num, day = current_week
        current_week_str = f"{year}-W{week_num:02d}"
        
        loop = asyncio.get_event_loop()
        top_members = await loop.run_in_executor(
            ThreadPoolExecutor(),
            lambda: list(weeklydb.find({"week": current_week_str}).sort("total_messages", -1).limit(10))
        
        if not top_members:
            await query.answer("❅ ɴᴏ ᴅᴀᴛᴀ ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜɪs ᴡᴇᴇᴋ.")
            return
        
        response = "⬤ 📈 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, 1):
            user_id = member["user_id"]
            total = member["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            response += f"{idx}. {user_name} ➥ {total}\n"
            users_data.append((user_name, total))
        
        graph = generate_horizontal_bar_chart(users_data, "Weekly Leaderboard")
        if graph:
            buttons = InlineKeyboardMarkup([
                [InlineKeyboardButton("ᴛᴏᴅᴀʏ", callback_data="today"),
                 InlineKeyboardButton("ᴡᴇᴇᴋʟʏ", callback_data="weekly"),
                 InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ", callback_data="overall")]
            ])
            await query.message.edit_media(InputMediaPhoto(graph, caption=response), reply_markup=buttons)
        else:
            await query.answer("Error updating leaderboard.")
    except Exception as e:
        logger.error(f"Error in weekly_callback: {e}")
        await query.answer("An error occurred.")
