import datetime
from pymongo import MongoClient
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputMediaPhoto
import matplotlib.pyplot as plt
import io
import logging
from collections import defaultdict
from KOKUMUSIC import app
# MongoDB connection
client = MongoClient('mongodb+srv://yash:shivanshudeo@yk.6bvcjqp.mongodb.net/')
db = client['Champu']
rankdb = db['UserStats']  # We store all stats in this one collection

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Helper functions

def get_most_recent_sunday():
    """Returns the most recent Sunday (Sunday is considered the start of the week)."""
    today = datetime.date.today()
    days_since_sunday = today.weekday() + 1  # Sunday is 6, Monday is 0, ..., Saturday is 5
    most_recent_sunday = today - datetime.timedelta(days=days_since_sunday)
    return most_recent_sunday

def get_week_number_for_sunday():
    """Returns the week number starting from Sunday to Sunday."""
    most_recent_sunday = get_most_recent_sunday()
    # Calculate the number of days since the start of the year
    start_of_year = datetime.date(most_recent_sunday.year, 1, 1)
    days_since_start_of_year = (most_recent_sunday - start_of_year).days
    # Calculate the week number by dividing days by 7
    week_number = days_since_start_of_year // 7 + 1
    return most_recent_sunday, week_number

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

# Watcher for messages
@app.on_message(filters.group & filters.group, group=6)
async def message_watcher(_, message):
    try:
        chat_id = message.chat.id
        user_id = message.from_user.id
        current_date = datetime.date.today()
        most_recent_sunday, week_number = get_week_number_for_sunday()

        # Update the user's message counts for today, this week, and overall
        user_stats = rankdb.find_one({"_id": user_id})

        if not user_stats:
            user_stats = {"_id": user_id, "overall": {"total_messages": 0}, "daily": {"date": str(current_date), "total_messages": 0}, "weekly": {"start_date": str(most_recent_sunday), "total_messages": 0}}

        # Update overall message count
        rankdb.update_one({"_id": user_id}, {"$inc": {"overall.total_messages": 1}}, upsert=True)

        # Update daily message count
        if user_stats['daily']['date'] == str(current_date):
            rankdb.update_one({"_id": user_id}, {"$inc": {"daily.total_messages": 1}})
        else:
            rankdb.update_one({"_id": user_id}, {"$set": {"daily.date": str(current_date), "daily.total_messages": 1}})

        # Update weekly message count
        if user_stats['weekly']['start_date'] == str(most_recent_sunday):
            rankdb.update_one({"_id": user_id}, {"$inc": {"weekly.total_messages": 1}})
        else:
            rankdb.update_one({"_id": user_id}, {"$set": {"weekly.start_date": str(most_recent_sunday), "weekly.total_messages": 1}})
    except Exception as e:
        logger.error(f"Error in message_watcher: {e}")

# Command to display today's leaderboard
@app.on_message(filters.command("today"))
async def today_leaderboard(_, message):
    try:
        chat_id = message.chat.id
        current_date = datetime.date.today()

        top_members = rankdb.find({"daily.date": str(current_date)}).sort("daily.total_messages", -1).limit(10)

        response = "⬤ 📈 ᴛᴏᴅᴀʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, start=1):
            user_id = member["_id"]
            total_messages = member["daily"]["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"
            user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
            response += user_info
            users_data.append((user_name, total_messages))

        # Generate horizontal bar chart
        graph = generate_horizontal_bar_chart(users_data, "Today's Leaderboard")

        if graph:
            button = InlineKeyboardMarkup(
                    [[    
                       InlineKeyboardButton("ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="weekly"),
                       InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="overall"),
                    ]])
            await message.reply_photo(graph, caption=response, reply_markup=button, has_spoiler=True)
        else:
            await message.reply_text("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in today_leaderboard command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Command to display overall leaderboard
@app.on_message(filters.command("ranking"))
async def overall_leaderboard(_, message):
    try:
        top_members = rankdb.find().sort("overall.total_messages", -1).limit(10)

        response = "⬤ 📈 ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ\n\n"
        users_data = []
        for idx, member in enumerate(top_members, start=1):
            user_id = member["_id"]
            total_messages = member["overall"]["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"

            user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
            response += user_info
            users_data.append((user_name, total_messages))

        # Generate horizontal bar chart
        graph = generate_horizontal_bar_chart(users_data, "Overall Leaderboard")

        if graph:
            button = InlineKeyboardMarkup(
                    [[    
                       InlineKeyboardButton("ᴛᴏᴅᴀʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="today"),
                       InlineKeyboardButton("ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="weekly")
                    ]])
            await message.reply_photo(graph, caption=response, reply_markup=button, has_spoiler=True)
        else:
            await message.reply_text("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in overall_leaderboard command: {e}")
        await message.reply_text("An error occurred while processing the command.")

# Command to display weekly leaderboard
@app.on_message(filters.command("weekly"))
async def weekly_leaderboard(_, message):
    try:
        most_recent_sunday, week_number = get_week_number_for_sunday()

        top_members = rankdb.find({"weekly.start_date": str(most_recent_sunday)}).sort("weekly.total_messages", -1).limit(10)

        response = f"⬤ 📈 ᴡᴇᴇᴋʟʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ (Week {week_number})\n\n"
        users_data = []
        for idx, member in enumerate(top_members, start=1):
            user_id = member["_id"]
            total_messages = member["weekly"]["total_messages"]
            try:
                user_name = (await app.get_users(user_id)).first_name
            except:
                user_name = "Unknown"

            user_info = f"{idx}.   {user_name} ➥ {total_messages}\n"
            response += user_info
            users_data.append((user_name, total_messages))

        # Generate horizontal bar chart
        graph = generate_horizontal_bar_chart(users_data, f"Weekly Leaderboard - Week {week_number}")

        if graph:
            button = InlineKeyboardMarkup(
                    [[    
                       InlineKeyboardButton("ᴛᴏᴅᴀʏ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="today"),
                       InlineKeyboardButton("ᴏᴠᴇʀᴀʟʟ ʟᴇᴀᴅᴇʀʙᴏᴀʀᴅ", callback_data="overall")
                    ]])
            await message.reply_photo(graph, caption=response, reply_markup=button, has_spoiler=True)
        else:
            await message.reply_text("Error generating graph.")
    except Exception as e:
        logger.error(f"Error in weekly_leaderboard command: {e}")
        await message.reply_text("An error occurred while processing the command.")
