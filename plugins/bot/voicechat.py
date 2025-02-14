from ChampuMusic.misc import SPECIAL_ID
from pyrogram import filters
from pyrogram.enums import ChatType
from strings import get_string
from ChampuMusic import app
from pyrogram import *
from pyrogram.types import *
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message
from ChampuMusic.utils import Champubin
from ChampuMusic.utils.database import get_assistant, get_lang
import asyncio
from config import OWNER_ID
from os import getenv
from dotenv import load_dotenv
load_dotenv()
from ChampuMusic.logging import LOGGER

@app.on_message(
    filters.command(["vcuser", "vcusers", "vcmember", "vcmembers"]) & filters.admin
    & (filters.user(OWNER_ID) | filters.user(SPECIAL_ID))
)
async def vc_members(client, message):
    try:
        language = await get_lang(message.chat.id)
        _ = get_string(language)
    except:
        _ = get_string("en")
    msg = await message.reply_text(_["V_C_1"])
    userbot = await get_assistant(message.chat.id)
    TEXT = ""
    try:
        async for m in userbot.get_call_members(message.chat.id):
            chat_id = m.chat.id
            username = m.chat.username
            is_hand_raised = m.is_hand_raised
            is_video_enabled = m.is_video_enabled
            is_left = m.is_left
            is_screen_sharing_enabled = m.is_screen_sharing_enabled
            is_muted = bool(m.is_muted and not m.can_self_unmute)
            is_speaking = not m.is_muted

            if m.chat.type != ChatType.PRIVATE:
                title = m.chat.title
            else:
                try:
                    title = (await client.get_users(chat_id)).mention
                except:
                    title = m.chat.first_name

            TEXT += _["V_C_2"].format(
                title,
                chat_id,
                username,
                is_video_enabled,
                is_screen_sharing_enabled,
                is_hand_raised,
                is_muted,
                is_speaking,
                is_left,
            )
            TEXT += "\n\n"
        if len(TEXT) < 4000:
            await msg.edit(TEXT or _["V_C_3"])
        else:
            link = await Champubin(TEXT)
            await msg.edit(
                _["V_C_4"].format(link),
                disable_web_page_preview=True,
            )
    except ValueError as e:
        await msg.edit(_["V_C_5"])


# vc on
@app.on_message(filters.video_chat_started)
async def brah(_, msg):
    if msg.chat.permissions.can_send_messages:
        if msg and msg.from_user:
            user = msg.from_user
            if user.username:
                mention = f"@{user.username}"
            else:
                mention = user.mention
                await msg.reply(f"**{mention} sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ! 😊**")
        else:
            await msg.reply("sᴏᴍᴇᴏɴᴇ sᴛᴀʀᴛᴇᴅ ᴛʜᴇ ᴠᴏɪᴄᴇ ᴄʜᴀᴛ! 😊")
    else:
        LOGGER.error("ʙᴏᴛ ᴅᴏᴇs ɴᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ᴄʜᴀᴛ.")
        # You can also send a notification to the bot owner or admin here
# vc off
@app.on_message(filters.video_chat_ended)
async def brah2(_, msg):
    if msg.chat.permissions.can_send_messages:
        if msg and msg.from_user:
            user = msg.from_user
            if user.username:
                mention = f"@{user.username}"
            else:
                mention = user.mention
                await msg.reply(f"**{mention} ᴇɴᴅᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛ! 😕**")
        else:
            await msg.reply("sᴏᴍᴇᴏɴᴇ ᴇɴᴅᴇᴅ ᴛʜᴇ ᴠɪᴅᴇᴏ ᴄʜᴀᴛ! 😕")
    else:
        LOGGER.error("ʙᴏᴛ ᴅᴏᴇs ɴᴏᴛ ʜᴀᴠᴇ ᴘᴇʀᴍɪssɪᴏɴ ᴛᴏ sᴇɴᴅ ᴍᴇssᴀɢᴇs ɪɴ ᴛʜɪs ᴄʜᴀᴛ.")
        # You can also send a notification to the bot owner or admin here

@app.on_message(filters.video_chat_members_invited)
async def brah3(app: app, message: Message):
    # Check if from_user is not None
    if message.from_user:
        text = f"➻ {message.from_user.mention}\n\n**๏ ɪɴᴠɪᴛɪɴɢ ɪɴ ᴠᴄ ᴛᴏ :**\n\n**➻ **"
    else:
        text = "➻ Unknown User\n\n**๏ ɪɴᴠɪᴛɪɴɢ ɪɴ ᴠᴄ ᴛᴏ :**\n\n**➻ **"
    x = 0
    for user in message.video_chat_members_invited.users:
        try:
            text += f"[{user.first_name}](tg://user?id={user.id}) "
            x += 1
        except Exception:
            pass

    try:
        add_link = f"https://t.me/{app.username}?startgroup=true"
        reply_text = f"{text} 🤭🤭"
        userbot = await get_assistant(message.chat.id)
        await message.reply(reply_text, reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(text="๏ ᴊᴏɪɴ ᴠᴄ ๏", url=add_link)]])) 
    except Exception as e:
        print(f"Error: {e}")

####

@app.on_message(filters.command("math", prefixes="/"))
def calculate_math(client, message):
    expression = message.text.split("/math ", 1)[1]
    try:
        result = eval(expression)
        response = f"ᴛʜᴇ ʀᴇsᴜʟᴛ ɪs : {result}"
    except:
        response = "ɪɴᴠᴀʟɪᴅ ᴇxᴘʀᴇssɪᴏɴ"
    message.reply(response)





__MODULE__ = "Mᴀᴛʜ"
__HELP__ = """

## Mᴀᴛʜ Cᴏᴍᴍᴀɴᴅ Hᴇᴘ

### 1. /ᴍᴀᴛʜ [ᴇxᴘʀᴇssɪᴏɴ]
**Dᴇsᴄʀɪᴘᴛɪᴏɴ:**
Cᴀᴄᴜᴀᴛᴇs ᴛʜᴇ ʀᴇsᴜᴛ ᴏғ ᴀ ᴍᴀᴛʜᴇᴍᴀᴛɪᴄᴀ ᴇxᴘʀᴇssɪᴏɴ.

**Usᴀɢᴇ:**
/ᴍᴀᴛʜ [ᴇxᴘʀᴇssɪᴏɴ]

**Dᴇᴛᴀɪs:**
- Sᴜᴘᴘᴏʀᴛs ʙᴀsɪᴄ ᴀʀɪᴛʜᴍᴇᴛɪᴄ ᴏᴘᴇʀᴀᴛɪᴏɴs: ᴀᴅᴅɪᴛɪᴏɴ (+), sᴜʙᴛʀᴀᴄᴛɪᴏɴ (-), ᴍᴜᴛɪᴘɪᴄᴀᴛɪᴏɴ (*), ᴀɴᴅ ᴅɪᴠɪsɪᴏɴ (/).
- Rᴇᴛᴜʀɴs ᴛʜᴇ ʀᴇsᴜᴛ ᴏғ ᴛʜᴇ ᴇxᴘʀᴇssɪᴏɴ.
- Dɪsᴘᴀʏs "Iɴᴠᴀɪᴅ ᴇxᴘʀᴇssɪᴏɴ" ɪғ ᴛʜᴇ ᴇxᴘʀᴇssɪᴏɴ ɪs ɴᴏᴛ ᴠᴀɪᴅ.

"""
