from pyrogram.handlers import ChatMemberUpdatedHandler
from pyrogram.types import ChatMemberUpdated, Message
from typing import Union, List
from pyrogram import Client, filters
from ChampuMusic import app

# Default state for /infovc
infovc_enabled = True  # Default enabled

# Command decorator
def command(commands: Union[str, List[str]]):
    return filters.command(commands, prefixes=["/"])

# Command to toggle /infovc on/off
@app.on_message(command(["infovc"]))
async def toggle_infovc(client: Client, message: Message):
    global infovc_enabled
    if len(message.command) > 1:
        state = message.command[1].lower()
        if state == "on":
            infovc_enabled = True
            await message.reply("✅ Voice chat join notifications are now enabled.")
        elif state == "off":
            infovc_enabled = False
            await message.reply("❌ Voice chat join notifications are now disabled.")
        else:
            await message.reply("⚠️ Usage: /infovc on or /infovc off")
    else:
        await message.reply("⚠️ Usage: /infovc on or /infovc off")

# Handler to notify when users join voice chats
async def user_joined_voice_chat(client: Client, chat_member_updated: ChatMemberUpdated):
    global infovc_enabled

    if not infovc_enabled:
        return

    try:
        chat = chat_member_updated.chat
        user = chat_member_updated.new_chat_member.user

        if not chat or not user:
            return

        # Debugging logs
        print(f"🔍 ChatMemberUpdated Event Detected!")
        print(f"📌 Old Status: {chat_member_updated.old_chat_member.status}")
        print(f"📌 New Status: {chat_member_updated.new_chat_member.status}")

        # Check if the user joined a voice chat
        old_status = chat_member_updated.old_chat_member.status
        new_status = chat_member_updated.new_chat_member.status

        if old_status in ["left", "kicked", "member"] and new_status == "voice_chat_participant":
            # Construct the message
            text = (
                f"**#JoinVoiceChat**\n"
                f"👤 **Name:** {user.mention}\n"
                f"🆔 **ID:** `{user.id}`\n"
                f"🎤 **Action:** Joined a voice chat"
            )

            # Debug: Log the message before sending
            print(f"📨 Sending Message: {text}")

            # Send the message to the group
            await client.send_message(chat.id, text)
        else:
            print("⚠️ User did not join voice chat.")
    except Exception as e:
        print(f"⚠️ Error in user_joined_voice_chat: {e}")

# Add the handler for chat member updates
app.add_handler(ChatMemberUpdatedHandler(user_joined_voice_chat))
