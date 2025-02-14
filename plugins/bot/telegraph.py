import logging
import os
from pyrogram import filters
from pyrogram.types import Message
from TheAPI import api
from ChampuMusic import app

# Setup logging
logging.basicConfig(format='%(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)

@app.on_message(filters.command(["tgm"]))
async def get_link_group(client, message):
    user = message.from_user
    logging.info(f"ʀᴇᴄᴇɪᴠᴇᴅ ᴍᴇᴅɪᴀ ғʀᴏᴍ {user.first_name}")

    # Check if the message is a reply to a media message
    if not message.reply_to_message:
        await message.reply_text("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇᴅɪᴀ ᴍᴇssᴀɢᴇ.")
        return

    media = message.reply_to_message
    file_size = 0
    if media.photo:
        file_size = media.photo.file_size
    elif media.video:
        file_size = media.video.file_size
    elif media.document:
        file_size = media.document.file_size

    if file_size > 15 * 1024 * 1024:
        await message.reply_text("ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴍᴇᴅɪᴀ ғɪʟᴇ ᴜɴᴅᴇʀ 𝟷𝟻ᴍʙ.")
        return

    try:
        text = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")

        async def progress(current, total):
            try:
                await text.edit_text(f"ᴅᴏᴡɴʟᴏᴀᴅɪɴɢ... {current * 100 / total:.1f}%")
            except Exception:
                pass

        try:
            local_path = await media.download(progress=progress)
            await text.edit_text("ᴜᴘʟᴏᴀᴅɪɴɢ ᴛᴏ ᴛᴇʟᴇɢʀᴀᴘʜ...")

            upload_result = api.upload_image(local_path)

            if isinstance(upload_result, str):
                await text.edit_text(f"ʜᴇʀᴇ ɪs ʏᴏᴜʀ ʟɪɴᴋ: {upload_result}")
            else:
                await text.edit_text(f"ғᴀɪʟᴇᴅ ᴛᴏ ᴜᴘʟᴏᴀᴅ ᴛʜᴇ ᴍᴇᴅɪᴀ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.\n\nʀᴇᴀsᴏɴ: {upload_result}")

            try:
                os.remove(local_path)
            except Exception:
                pass

        except Exception as e:
            await text.edit_text(f"ғᴀɪʟᴇᴅ ᴛᴏ ᴜᴘʟᴏᴀᴅ ᴛʜᴇ ᴍᴇᴅɪᴀ. ᴘʟᴇᴀsᴇ ᴛʀʏ ᴀɢᴀɪɴ ʟᴀᴛᴇʀ.\n\nʀᴇᴀsᴏɴ: {e}")
            try:
                os.remove(local_path)
            except Exception:
                pass
            return
    except Exception:
        pass