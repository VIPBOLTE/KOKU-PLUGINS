from pyrogram import Client, filters
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from ChampuMusic import app
from pyrogram.errors import UserNotParticipant
from ChampuMusic.misc import SUDOERS

@app.on_message(filters.command("send") & SUDOERS)
async def send_message(client, message):
    # Check if the command has the correct number of arguments
    if len(message.command) < 3:
        await message.reply_text("ᴜsᴀɢᴇ: /send <username or group_id> <message>")
        return

    # Extract the username/group ID and the message
    target = message.command[1]
    msg_content = " ".join(message.command[2:])

    try:
        # Check if the bot is a member of the target chat
        bot_member = await client.get_chat_member(chat_id=target, user_id=client.me.id)

        # If the bot is not a member, inform the user
        if bot_member.status in ["left", "kicked"]:
            await message.reply_text("ɪ ᴀᴍ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏғ ᴛʜɪs ɢʀᴏᴜᴘ. ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴍᴇ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ ғɪʀsᴛ.")
            return

        # Sending the message
        sent_message = await client.send_message(chat_id=target, text=msg_content)

        # Create URLs for the message
        chat_id = sent_message.chat.id
        message_id = sent_message.id  # Use 'id' instead of 'message_id'
        message_url = f"https://t.me/c/{str(chat_id)[4:]}/{message_id}"

        # Create inline buttons
        view_button = InlineKeyboardButton(" ɢʀᴏᴜᴘ ", url=f"https://t.me/{target}")
        mention_button = InlineKeyboardButton(" ᴍᴇssᴀɢᴇ ", url=message_url)
        reply_markup = InlineKeyboardMarkup([[view_button, mention_button]])

        # Send a success message with the buttons
        await message.reply_text("ᴍᴇssᴀɢᴇ sᴇɴᴛ sᴜᴄᴄᴇssғᴜʟʟʏ!", reply_markup=reply_markup)

    except UserNotParticipant:
        # Handle the case where the bot is not a member of the chat
        await message.reply_text("ɪ ᴀᴍ ɴᴏᴛ ᴀ ᴍᴇᴍʙᴇʀ ᴏғ ᴛʜɪs ɢʀᴏᴜᴘ. ᴘʟᴇᴀsᴇ ᴀᴅᴅ ᴍᴇ ᴛᴏ ᴛʜᴇ ɢʀᴏᴜᴘ ғɪʀsᴛ.")
    except Exception as e:
        await message.reply_text(f"ᴇʀʀᴏʀ: {e}")