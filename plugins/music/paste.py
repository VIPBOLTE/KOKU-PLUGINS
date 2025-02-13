import asyncio
import re
import os
import socket
from asyncio import get_running_loop, sleep
from functools import partial
from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiohttp import ClientSession
import aiofiles
from io import BytesIO
from KOKUMUSIC import app

# Create a single ClientSession for aiohttp
aiohttpsession = ClientSession()

# Pattern for checking supported MIME types (text files)
pattern = re.compile(r"^text/|json$|yaml$|xml$|toml$|x-sh$|x-shellscript$")

# Function to generate the Carbon image from the code
async def make_carbon(code):
    url = "https://carbonara.solopov.dev/api/cook"
    async with aiohttpsession.post(url, json={"code": code}) as resp:
        image = BytesIO(await resp.read())
    image.name = "carbon.png"
    return image

# Function to send content via netcat to the server
# Refactor netcat function to async using asyncio
async def _netcat(host, port, content):
    reader, writer = await asyncio.open_connection(host, port)
    writer.write(content.encode())
    await writer.drain()
    data = await reader.read(4096)
    writer.close()
    await writer.wait_closed()
    return data.decode("utf-8").strip("\n\x00")

# Async function to paste content and retrieve the link
async def paste(content):
    link = await _netcat("ezup.dev", 9999, content)
    return link

# Function to check if the preview URL is up and running
async def isPreviewUp(preview: str) -> bool:
    for _ in range(7):
        try:
            async with aiohttpsession.head(preview, timeout=2) as resp:
                status = resp.status
                size = resp.content_length
        except asyncio.TimeoutError:
            return False
        if status == 404 or (status == 200 and size == 0):
            await asyncio.sleep(0.4)
        else:
            return status == 200
    return False

# Function to ensure the async function is running in the correct context
def ensure_event_loop():
    try:
        loop = asyncio.get_event_loop()  # Will raise an error if there's no running loop
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    return loop

# Handle the /error command when the user replies to a message
@app.on_message(filters.command("error"))
async def paste_func(_, message):
    if not message.reply_to_message:
        return await message.reply_text("**ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ /paste**")

    m = await message.reply_text("**ᴘᴀsᴛɪɴɢ ᴘʟs ᴡᴀɪᴛ 10 sᴇᴄ....**")

    if message.reply_to_message.text:
        content = str(message.reply_to_message.text)
    elif message.reply_to_message.document:
        document = message.reply_to_message.document
        if document.file_size > 1048576:
            return await m.edit("**ʏᴏᴜ ᴄᴀɴ ᴏɴʟʏ ᴘᴀsᴛᴇ ғɪʟᴇs sᴍᴀʟʟᴇʀ ᴛʜᴀɴ 1ᴍʙ.**")
        if not pattern.search(document.mime_type):
            return await m.edit("**ᴏɴʟʏ ᴛᴇxᴛ ғɪʟᴇs ᴄᴀɴ ʙᴇ ᴘᴀsᴛᴇᴅ.**")

        doc = await message.reply_to_message.download()
        async with aiofiles.open(doc, mode="r") as f:
            lines = await f.readlines()

        os.remove(doc)

        total_lines = len(lines)
        current_line = 0
        page_number = 1

        while current_line < total_lines:
            end_line = min(current_line + 50, total_lines)
            content_chunk = "".join(lines[current_line:end_line])
            carbon = await make_carbon(content_chunk)

            await m.delete()
            text = await message.reply("**✍️ᴘᴀsᴛᴇᴅ ᴏɴ ᴄᴀʀʙᴏɴ ᴘᴀɢᴇ !**")
            await asyncio.sleep(0.4)
            await text.edit("**ᴜᴘʟᴏᴀᴅɪɴɢ ᴜɴᴅᴇʀ 5 sᴇᴄ.**")
            await asyncio.sleep(0.4)
            await text.edit("**ᴜᴘʟᴏᴀᴅɪɴɢ ᴜɴᴅᴇʀ 5 sᴇᴄ....**")
            caption = f"🥀ᴛʜɪs ɪs  {page_number} ᴘᴀɢᴇ - {current_line + 1} to {end_line} ʟɪɴᴇs..\n sᴇɴᴅɪɴɢ ᴍᴏʀᴇ ʟɪɴᴇs ɪғ ʜᴀᴠᴇ ᴏɴ ɴᴇxᴛ ᴘᴀɢᴇ ᴘʟᴇᴀsᴇ ᴡᴀɪᴛ..."
            await message.reply_photo(carbon, caption=caption)
            await text.delete()
            carbon.close()

            current_line = end_line
            page_number += 1
            await sleep(1)  # Optional: Add a sleep to avoid rate limiting or being blocked

    else:
        await m.edit("**Unsupported file type. Only text files can be pasted.**")
