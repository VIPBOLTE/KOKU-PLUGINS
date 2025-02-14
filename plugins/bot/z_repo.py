import asyncio

from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

import config
from ChampuMusic import app
from ChampuMusic.utils.database import add_served_chat, get_assistant


start_txt = """**
✪ 𝗪𝗲𝗹𝗰𝗼𝗺𝗲 𝘁𝗼 𝗖𝗵𝗮𝗺𝗽𝘂 𝗥𝗲𝗽𝗼𝘀 ✪

➲ ᴇᴀsʏ ʜᴇʀᴏᴋᴜ ᴅᴇᴘʟᴏʏᴍᴇɴᴛ ✰  
➲ ɴᴏ ʙᴀɴ ɪssᴜᴇs ✰  
➲ ᴜɴʟɪᴍɪᴛᴇᴅ ᴅʏɴᴏs ✰  
➲ 𝟸𝟺/𝟽 ʟᴀɢ-ғʀᴇᴇ ✰

► sᴇɴᴅ ᴀ sᴄʀᴇᴇɴsʜᴏᴛ ɪғ ʏᴏᴜ ғᴀᴄᴇ ᴀɴʏ ᴘʀᴏʙʟᴇᴍs!
**"""




@app.on_message(filters.command("repo"))
async def start(_, msg):
    buttons = [
        [ 
          InlineKeyboardButton("ᴀᴅᴅ ᴍᴇ", url=f"https://t.me/{app.username}?startgroup=true")
        ],
        [
          InlineKeyboardButton("ᴄʜᴧᴍᴘᴜ", url="https://t.me/TheChampu"),
          InlineKeyboardButton("sʜɪᴠᴀɴsʜᴜ", url="https://t.me/TheShivanshu"),
          ],
               [
                InlineKeyboardButton("ᴏᴡɴᴇʀ", url="https://t.me/itsmeshivanshu"),

],[
              InlineKeyboardButton("ᴍᴜsɪᴄ", url=f"https://github.com/TheChampu/ChampuMusic"),
              InlineKeyboardButton("sᴛʀɪɴɢ", url=f"https://github.com/TheChampu/ChampuString"),
              ],
[
              InlineKeyboardButton("sɪᴍᴘʟᴇ ᴍᴜsɪᴄ", url=f"https://github.com/TheChampu/TelegramMusicBot")
              ],
              [
              InlineKeyboardButton("ᴍᴀɴᴀɢᴍᴇɴᴛ", url=f"https://github.com/TheChampu/ChampuManagment"),
InlineKeyboardButton("ᴄʜᴀᴛʙᴏᴛ", url=f"https://github.com/TheChampu/ChatBot"),
]]
    
    reply_markup = InlineKeyboardMarkup(buttons)
    
    await msg.reply_photo(
        photo=config.START_IMG_URL,
        caption=start_txt,
        reply_markup=reply_markup
    )



