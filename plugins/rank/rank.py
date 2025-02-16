from pyrogram import filters
from pymongo import MongoClient
from KOKUMUSIC import app
from pyrogram.types import *
from pyrogram.errors import MessageNotModified
from pyrogram.types import InputMediaPhoto
import asyncio
import matplotlib.pyplot as plt
import io
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/', serverSelectionTimeoutMS=5000)
    client.server_info()  # Test connection
    db = client['Champu']
    rankdb = db['Rankingdb']
except Exception as e:
    logger.error(f"Failed to connect to MongoDB: {e}")
    raise

# Helper functions
def get_current_week():
    return datetime.now().isocalendar()[1]

def generate_doc_id(user_id: int, chat_id: int, type: str, week: int = None) -> str:
    """Generate unique document ID"""
    if week and type == "week":
        return f"{user_id}_{chat_id}_{type}_{week}"
    return f"{user_id}_{chat_id}_{type}"

# Message watchers
@app.on_message(filters.group, group=6)
async def message_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        current_week = get_current_week()

        # Update today's messages
        today_doc_id = generate_doc_id(user_id, chat_id, "today")
        rankdb.update_one(
            {"_id": today_doc_id},
            {"$inc": {"total_messages": 1}, "$set": {"username": message.from_user.username}},
            upsert=True
        )

        # Update weekly messages
        week_doc_id = generate_doc_id(user_id, chat_id, "week", current_week)
        rankdb.update_one(
            {"_id": week_doc_id},
            {"$inc": {"total_messages": 1}, "$set": {"username": message.from_user.username}},
            upsert=True
        )

    except Exception as e:
        logger.error(f"Error in message_watcher: {e}")

@app.on_message(filters.group, group=11)
async def overall_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id

        # Update overall messages
        overall_doc_id = generate_doc_id(user_id, chat_id, "overall")
        rankdb.update_one(
            {"_id": overall_doc_id},
            {"$inc": {"total_messages": 1}, "$set": {"username": message.from_user.username}},
            upsert=True
        )
    except Exception as e:
        logger.error(f"Error in overall_watcher: {e}")

# Leaderboard components
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

async def get_leaderboard_data(chat_id: int, type: str) -> list:
    current_week = get_current_week()
    query = {
        "_id": {
            "$regex": f"_.*_{chat_id}_{'week_' + str(current_week) if type == 'week' else type}$"
        }
    } if type != "overall" else {"_id": {"$regex": f"_.*_{chat_id}_overall$"}}

    pipeline = [
        {"$match": query},
        {"$group": {
            "_id": "$_id",
            "total_messages": {"$max": "$total_messages"},
            "user_id": {"$first": {"$toInt": {"$arrayElemAt": [{"$split": ["$_id", "_"]}, 0]}}},
            "username": {"$first": "$username"}
        }},
        {"$sort": {"total_messages": -1}},
        {"$limit": 10}
    ]

    results = []
    async for doc in rankdb.aggregate(pipeline):
        try:
            user = await app.get_users(doc["user_id"])
            name = user.first_name
        except:
            name = doc.get("username", "Unknown User")
        results.append((name, doc["total_messages"]))
    
    return results

# Command handlers
@app.on_message(filters.command("ranking"))
async def ranking_command(_, message):
    try:
        buttons = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("Today", callback_data="today"),
                InlineKeyboardButton("Week", callback_data="week"),
                InlineKeyboardButton("Overall", callback_data="overall")
            ]
        ])
        await message.reply_text("📊 Select Leaderboard Type:", reply_markup=buttons)
    except Exception as e:
        logger.error(f"Error in /ranking command: {e}")

@app.on_callback_query(filters.regex("^(today|week|overall)$"))
async def leaderboard_callback(_, query):
    try:
        chat_id = query.message.chat.id
        selection = query.data
        logger.info(f"Received callback query for {selection} leaderboard")  # Log the callback data

        time_frames = {
            "today": "Today's Leaderboard",
            "week": "Weekly Leaderboard",
            "overall": "All-Time Leaderboard"
        }
        
        # Get leaderboard data
        data = await get_leaderboard_data(chat_id, selection)
        if not data:
            await query.answer("No data available yet!", show_alert=True)
            return

        # Generate response text
        response = f"🏆 **{time_frames[selection]}**\n\n"
        for idx, (name, count) in enumerate(data, start=1):
            response += f"{idx}. {name} ➠ **{count}** messages\n"
            if idx >= 10:
                break

        # Generate graph
        graph = generate_horizontal_bar_chart(data, time_frames[selection])
        if not graph:
            await query.answer("Failed to generate visualization")
            return

        # Update buttons with active state
        active_buttons = []
        for btn_type in ["today", "week", "overall"]:
            text = f"✅ {btn_type.capitalize()}" if btn_type == selection else btn_type.capitalize()
            active_buttons.append(InlineKeyboardButton(text, callback_data=btn_type))

        await query.message.edit_media(
            media=InputMediaPhoto(graph, caption=response),
            reply_markup=InlineKeyboardMarkup([active_buttons])
        )
        await query.answer()
        
    except MessageNotModified:
        await query.answer()
    except Exception as e:
        logger.error(f"Leaderboard callback error: {e}")
        await query.answer("Error loading leaderboard")
