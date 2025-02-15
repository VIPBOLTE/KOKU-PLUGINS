import logging
import asyncio
from random import choice
from pyrogram import Client, filters
from pyrogram.types import Message
import motor.motor_asyncio
import config
# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)
ass = Client(
    name = "ShuklaPlayer",
    api_id = config.API_ID,
    api_hash = config.API_HASH,
    session_string = config.STRING1,
)

# MongoDB configuration
from config import MONGO_DB_URI, OWNER_ID
GROUP = []  # Add group IDs you want to exclude
PORM = [
    "https://example.com/image1.jpg", 
    "https://example.com/image2.jpg", 
    "https://example.com/video1.mp4",
    "https://example.com/video2.mp4"
]  # Replace with your actual content URLs

# Initialize MongoDB connection
try:
    cli = motor.motor_asyncio.AsyncIOMotorClient(MONGO_DB_URI)
    db = cli.get_database()
    logger.info("MongoDB connection successful.")
except Exception as e:
    logger.error(f"MongoDB connection failed: {e}")

# Initialize Pyrogram Client

@ass.on_message(
    filters.command(["pornraid"], prefixes=["/", "!", "%", ",", ".", "@", "#"])
    & filters.user(OWNER_ID)
)
async def pornspam(xspam: Client, e: Message):
    try:
        # Debug log for incoming command
        logger.debug(f"Received pornraid command with count: {e.command[1] if len(e.command) > 1 else None}")
        
        counts = e.command[1] if len(e.command) > 1 else None
        if not counts:
            return await e.reply_text("**Usage: /pornraid <count>**")
        
        # Prevent spam in certain groups
        if int(e.chat.id) in GROUP:
            return await e.reply_text("**Sorry, I can't spam here.**")
        
        # Prepare content for spam
        kkk = "**#Pornspam**"
        count = int(counts)
        
        # Loop to send messages
        for _ in range(count):
            prn = choice(PORM)
            if ".jpg" in prn or ".png" in prn:
                await xspam.send_photo(e.chat.id, prn, caption=kkk)
                await asyncio.sleep(0.4)
            if ".mp4" in prn or ".MP4" in prn:
                await xspam.send_video(e.chat.id, prn, caption=kkk)
                await asyncio.sleep(0.4)

        # Log successful spam action
        logger.info(f"Sent {count} pornspam(s) to chat {e.chat.id}.")
    except Exception as e:
        logger.error(f"An error occurred in pornspam function: {e}")

