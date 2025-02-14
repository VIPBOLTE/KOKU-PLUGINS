import base64
import httpx
import os
import config 
from ChampuMusic import app
from pyrogram import Client, filters
import pyrogram
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup

import aiofiles, aiohttp, requests

async def image_loader(image: str, link: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(link) as resp:
            if resp.status == 200:
                f = await aiofiles.open(image, mode="wb")
                await f.write(await resp.read())
                await f.close()
                return image
            return image

@app.on_message(filters.command("upscale", prefixes="/"))
async def upscale_image(client, message):
    chat_id = message.chat.id
    replied = message.reply_to_message
    if not replied:
        return await message.reply_text("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀɴ ɪᴍᴀɢᴇ ...")
    if not replied.photo:
        return await message.reply_text("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀɴ ɪᴍᴀɢᴇ ...")

    aux = await message.reply_text("ɪɴᴄʀᴇᴀsɪɴɢ ǫᴜᴀʟɪᴛʏ ᴏғ ɪᴍᴀɢᴇ...")
    image = await replied.download()

    try:
        # Use the DeepAI API to upscale the image
        response = requests.post(
            "https://api.deepai.org/api/torch-srgan",
            files={
                'image': open(image, 'rb'),
            },
            headers={'api-key': 'bf9ee957-9fad-46f5-a403-3e96ca9004e4'}
        )
        response.raise_for_status()  # Raise an exception for HTTP errors

        data = response.json()
        image_link = data.get("output_url")

        if image_link:
            downloaded_image = await image_loader(image, image_link)
            await aux.delete()
            return await message.reply_document(downloaded_image)
        else:
            await aux.edit_text("ғᴀɪʟᴇᴅ ᴛᴏ ɢᴇᴛ ᴛʜᴇ ᴏᴜᴛᴘᴜᴛ ɪᴍᴀɢᴇ ʟɪɴᴋ.")
    except requests.exceptions.RequestException as e:
        await aux.edit_text(f"ʀᴇǫᴜᴇsᴛ ғᴀɪʟᴇᴅ: {str(e)}")
    except Exception as e:
        await aux.edit_text(f"ᴀɴ ᴜɴᴇxᴘᴇᴄᴛᴇᴅ ᴇʀʀᴏʀ ᴏᴄᴄᴜʀʀᴇᴅ: {str(e)}")
        

