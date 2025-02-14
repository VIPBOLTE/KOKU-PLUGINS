from pyrogram import Client, filters
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from pyrogram.errors import FloodWait
from ChampuMusic import app
from config import LOGGER_ID
from ChampuMusic.utils.database import get_assistant
import asyncio
import random

DEFAULT_REACTION_LIST = ['👍', '❤️', '😂', '😮', '😢', '🔥', '🎉']

async def send_log(message: str, chat_id: int, chat_title: str, message_id: int):
    try:
        channel_button = InlineKeyboardMarkup([[
            InlineKeyboardButton(text="ɢᴏ ᴛᴏ ᴍᴇssᴀɢᴇ", url=f"https://t.me/c/{str(chat_id)[4:]}/{message_id}")
        ]])
        await app.send_message(
            LOGGER_ID,
            f"{message}\n\nᴄʜᴀɴɴᴇʟ: {chat_title}\nᴄʜᴀɴɴᴇʟ ɪᴅ: `{chat_id}`\nᴍᴇssᴀɢᴇ ɪᴅ: `{message_id}`",
            reply_markup=channel_button
        )
    except Exception as e:
        print(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʟᴏɢ: {e}")

async def get_channel_reactions(chat_id):
    return DEFAULT_REACTION_LIST

async def retry_with_backoff(func, *args, max_retries=5, initial_delay=1, **kwargs):
    retries = 0
    while retries < max_retries:
        try:
            return await func(*args, **kwargs)
        except FloodWait as e:
            retries += 1
            delay = initial_delay * (2 ** retries) + random.uniform(0, 1)
            await send_log(
                f"ғʟᴏᴏᴅᴡᴀɪᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ. ʀᴇᴛʀʏɪɴɢ ɪɴ {delay:.2f} sᴇᴄᴏɴᴅs...",
                kwargs.get('chat_id', 'Unknown'),
                kwargs.get('chat_title', 'Unknown'),
                kwargs.get('message_id', 'Unknown')
            )
            await asyncio.sleep(delay)
        except Exception as e:
            # Log the error and return None to indicate failure
            print(f"ᴇʀʀᴏʀ ɪɴ ʀᴇᴛʀʏ_ᴡɪᴛʜ_ʙᴀᴄᴋᴏғғ: {str(e)}")
            return None
    raise Exception(f"ғᴀɪʟᴇᴅ ᴀғᴛᴇʀ {max_retries} ʀᴇᴛʀɪᴇs")

async def send_reaction_with_fallback(client, chat_id, message_id, emoji, max_retries=3):
    for _ in range(max_retries):
        try:
            await client.send_reaction(chat_id=chat_id, message_id=message_id, emoji=emoji)
            return  # Success, exit the function
        except Exception as e:
            print(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇᴀᴄᴛɪᴏɴ {emoji}: {str(e)}")
            # Select a new random emoji
            emoji = random.choice(DEFAULT_REACTION_LIST)
    raise Exception(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇᴀᴄᴛɪᴏɴ ᴀғᴛᴇʀ {max_retries} ᴀᴛᴛᴇᴍᴘᴛs")
async def send_reaction_with_fallback(client, chat_id, message_id, emoji, max_retries=3):
    if emoji not in DEFAULT_REACTION_LIST:
        print(f"ɪɴᴠᴀʟɪᴅ ᴇᴍᴏᴊɪ ᴀᴛᴛᴇᴍᴘᴛᴇᴅ: {emoji}")
        return  # Skip sending if emoji is invalid

    for attempt in range(max_retries):
        try:
            print(f"ᴀᴛᴛᴇᴍᴘᴛɪɴɢ ᴛᴏ sᴇɴᴅ ʀᴇᴀᴄᴛɪᴏɴ: {emoji} to ᴍᴇssᴀɢᴇ ɪᴅ: {message_id} ɪɴ ᴄʜᴀᴛ ɪᴅ: {chat_id}")
            await client.send_reaction(chat_id=chat_id, message_id=message_id, emoji=emoji)
            print(f"sᴜᴄᴄᴇssғᴜʟʟʏ sᴇɴᴛ ʀᴇᴀᴄᴛɪᴏɴ: {emoji}")  # Log only on success
            return  # Success, exit the function
        except FloodWait as e:
            wait_time = e.x  # Get the wait time from the FloodWait exception
            print(f"ғʟᴏᴏᴅᴡᴀɪᴛ ᴅᴇᴛᴇᴄᴛᴇᴅ. ᴡᴀɪᴛɪɴɢ ғᴏʀ {wait_time} sᴇᴄᴏɴᴅs ʙᴇғᴏʀᴇ ʀᴇᴛʀʏɪɴɢ...")
            await asyncio.sleep(wait_time)  # Wait for the specified time
        except Exception as e:
            print(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇᴀᴄᴛɪᴏɴ {emoji}: {str(e)}")
            # Select a new random emoji
            emoji = random.choice(DEFAULT_REACTION_LIST)
    
    raise Exception(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇᴀᴄᴛɪᴏɴ ᴀғᴛᴇʀ {max_retries} ᴀᴛᴛᴇᴍᴘᴛs")

@app.on_message(filters.command("react"))
async def react_to_message(client, message: Message):
    if message.reply_to_message:
        try:
            allowed_reactions = await get_channel_reactions(message.chat.id)
        
            if not allowed_reactions:
                await message.chat.send_message(
                    f"ɴᴏ ʀᴇᴀᴄᴛɪᴏɴs ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ɪɴ ᴛʜɪs ɢʀᴏᴜᴘ.",
                    message.chat.id,
                    message.chat.title,
                    message.id
                )
                return
            
            assistant = await get_assistant(message.chat.id)
            # Attempt to send reaction with the assistant if available
            if assistant:
                bot_group_react = random.choice(allowed_reactions)
                try:
                    await send_reaction_with_fallback(
                        assistant,
                        message.chat.id,
                        message.reply_to_message.id,
                        bot_group_react
                    )
                except Exception as e:
                    print(f"ᴀssɪsᴛᴀɴᴛ ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴀᴄᴛ: {str(e)}")
            
            # Attempt to send reaction with the client (bot)
            assistant_group_react = random.choice(allowed_reactions)
            try:
                await send_reaction_with_fallback(
                    client,
                    message.chat.id,
                    message.reply_to_message.id,
                    assistant_group_react
                )
            except Exception as e:
                print(f"ᴄʟɪᴇɴᴛ ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴀᴄᴛ: {str(e)}")
        
        except Exception as e:
            await message.reply(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ʀᴇᴀᴄᴛɪᴏɴ. ᴇʀʀᴏʀ: {str(e)}")
        
        finally:
            try:
                await message.delete()  # Delete the command message
            except Exception as e:
                print(f"ғᴀɪʟᴇᴅ ᴛᴏ ᴅᴇʟᴇᴛᴇ ᴍᴇssᴀɢᴇ: {str(e)}")
    else:
        await message.reply("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ʀᴇᴀᴄᴛ ᴛᴏ ɪᴛ.")

@app.on_message(filters.channel)
async def auto_react_to_channel_post(client, message: Message):
    try:
        allowed_reactions = await get_channel_reactions(message.chat.id)
        
        if not allowed_reactions:
            await send_log(
                f"ɴᴏ ʀᴇᴀᴄᴛɪᴏɴs ᴀᴠᴀɪʟᴀʙʟᴇ ғᴏʀ ᴛʜɪs ᴄʜᴀɴɴᴇʟ.",
                message.chat.id,
                message.chat.title,
                message.id
            )
            return
        
        selected_react = random.choice(allowed_reactions)
        print(f"sᴇʟᴇᴄᴛᴇᴅ ʀᴇᴀᴄᴛɪᴏɴ ғᴏʀ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ: {selected_react}")

        # Attempt to react with the bot first
        try:
            await send_reaction_with_fallback(
                client,
                message.chat.id,
                message.id,
                selected_react
            )
        except Exception as e:
            print(f"ᴄʟɪᴇɴᴛ ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴀᴄᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ: {str(e)}")

        # Then, attempt to react with the assistant if available
        assistant = await get_assistant(message.chat.id)
        if assistant:
            assistant_reaction = random.choice(allowed_reactions)
            print(f"sᴇʟᴇᴄᴛᴇᴅ ʀᴇᴀᴄᴛɪᴏɴ ғᴏʀ ᴀssɪsᴛᴀɴᴛ: {assistant_reaction}")
            try:
                await send_reaction_with_fallback(
                    assistant,
                    message.chat.id,
                    message.id,
                    assistant_reaction
                )
            except Exception as e:
                print(f"ᴀssɪsᴛᴀɴᴛ ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴀᴄᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ: {str(e)}")
        
        await send_log(
            f"ʀᴇᴀᴄᴛᴇᴅ ᴛᴏ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ {selected_react}",
            message.chat.id,
            message.chat.title,
            message.id
        )
    except Exception as e:
        await send_log(
            f"ғᴀɪʟᴇᴅ ᴛᴏ ʀᴇᴀᴄᴛ ᴛᴏ ᴄʜᴀɴɴᴇʟ ᴘᴏsᴛ. ᴇʀʀᴏʀ: {str(e)}",
            message.chat.id,
            message.chat.title,
            message.id
        )