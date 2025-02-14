from pyrogram import Client, filters
from ChampuMusic import app
from config import OWNER_ID
from ChampuMusic.misc import SUDOERS
from pyrogram.types import Message

@app.on_message(filters.command(["post"], prefixes=["/", "."]) & SUDOERS)
async def copy_messages(_, message: Message):
    if message.reply_to_message:
        # Split the command arguments
        args = message.text.split()[1:]
        
        if args:
            try:
                # Try to get the destination group ID from the first argument
                destination_group_id = int(args[0])
            except ValueError:
                await message.reply("ɪɴᴠᴀʟɪᴅ ɢʀᴏᴜᴘ ɪᴅ. ᴘʟᴇᴀsᴇ ᴘʀᴏᴠɪᴅᴇ ᴀ ᴠᴀʟɪᴅ ɪɴᴛᴇɢᴇʀ.")
                return
        else:
            # If no argument is provided, use the default group ID
            destination_group_id = -1001423108989

        try:
            # Attempt to copy the message to the specified group
            await message.reply_to_message.copy(destination_group_id)
            await message.reply(f"ᴘᴏsᴛ sᴜᴄᴄᴇssғᴜʟʟʏ sᴇɴᴛ ᴛᴏ ɢʀᴏᴜᴘ {destination_group_id}")
        except Exception as e:
            await message.reply(f"ғᴀɪʟᴇᴅ ᴛᴏ sᴇɴᴅ ᴛʜᴇ ᴘᴏsᴛ. ᴇʀʀᴏʀ: {str(e)}")
    else:
        await message.reply("ᴘʟᴇᴀsᴇ ʀᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴛᴏ ᴘᴏsᴛ ɪᴛ.")