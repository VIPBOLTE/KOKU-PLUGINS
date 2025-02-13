import logging
from pyrogram import enums, filters
from KOKUMUSIC import app

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

BOT_ID = app.me.id

@app.on_message(filters.command(["unbanall", "nbanall", "ba"], prefixes=["/", "!", ".", "U", "u"]))
async def unban_all(_, msg):
    chat_id = msg.chat.id
    user_id = msg.from_user.id
    x = 0

    # Get bot's permissions in the chat
    try:
        bot = await app.get_chat_member(chat_id, BOT_ID)
        if bot is None:
            await msg.reply_text("I could not fetch bot information.")
            return
    except Exception as e:
        logger.error(f"Error fetching bot info: {e}")
        await msg.reply_text("There was an error fetching bot information.")
        return

    # Check if bot has permissions to restrict members
    bot_permission = bot.privileges and bot.privileges.can_restrict_members if bot.privileges else False

    # Get user information and their permissions
    try:
        user = await app.get_chat_member(chat_id, user_id)
        if user is None:
            await msg.reply_text("I could not fetch your information.")
            return
    except Exception as e:
        logger.error(f"Error fetching user info: {e}")
        await msg.reply_text("There was an error fetching your information.")
        return

    # Check if user has permissions to restrict members
    user_permission = user.privileges and user.privileges.can_restrict_members if user.privileges else False

    # Only proceed if both bot and user have the necessary permissions
    if bot_permission and user_permission:
        try:
            banned_users = []
            # Fetch all banned users in the chat
            async for m in app.get_chat_members(chat_id, filter=enums.ChatMembersFilter.BANNED):
                banned_users.append(m.user.id)

            ok = await app.send_message(
                chat_id,
                f"Total **{len(banned_users)}** users found to unban.\n**Started unbanning..**",
            )

            # Unban users in batches
            for user_id in banned_users:
                try:
                    await app.unban_chat_member(chat_id, user_id)
                    x += 1

                    if x % 5 == 0:
                        await ok.edit_text(f"Unbanned {x} out of {len(banned_users)} users.")
                except Exception as e:
                    logger.error(f"Error unbanning user {user_id}: {e}")
                    pass

            await ok.edit_text(f"Unbanned all {len(banned_users)} users.")
        except Exception as e:
            logger.error(f"Error processing banned users: {e}")
            await msg.reply_text("There was an error while unbanning users.")
    else:
        await msg.reply_text(
            "ᴇɪᴛʜᴇʀ ɪ ᴅᴏɴ'ᴛ ʜᴀᴠᴇ ᴛʜᴇ ʀɪɢʜᴛ ᴛᴏ ʀᴇsᴛʀɪᴄᴛ ᴜsᴇʀs ᴏʀ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ɪɴ sᴜᴅᴏ ᴜsᴇʀs ᴏʀ ʏᴏᴜ ᴀʀᴇ ɴᴏᴛ ᴀ ɴᴇᴄᴇssᴀʀʏ ᴀᴅᴍɪɴ"
        )

__MODULE__ = "ᴜɴʙᴀɴᴀʟʟ"
__HELP__ = """
**Uɴʙᴀɴ A**

Tʜɪs ᴍᴏᴅᴜʟᴇ ᴀʟʟᴏᴡs ᴀᴅᴍɪɴɪsᴛʀᴀᴛᴏʀs ᴡɪᴛʜ ʀᴇsᴛʀɪᴄᴛɪᴏɴ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴜɴʙᴀɴ ᴜsᴇʀs ɪɴ ᴀ ɢʀᴏᴜᴘ ᴀᴛ ᴏɴᴄᴇ.

Cᴏᴍᴍᴀɴᴅs:
- /ᴜɴʙᴀɴᴀʟʟ: Sᴛᴀʀᴛ ᴜɴʙᴀɴɴɪɴɢ ᴀʟʟ ʙᴀɴɴᴇᴅ ᴜsᴇʀs ɪɴ ᴛʜᴇ ɢʀᴏᴜᴘ.

Nᴏᴛᴇ:
- Oɴʟʏ ᴀᴅᴍɪɴs ᴡɪᴛʜ ʀᴇsᴛʀɪᴄᴛɪᴏɴ ᴘᴇʀᴍɪssɪᴏɴs ᴄᴀɴ ᴜsᴇ ᴛʜɪs ᴄᴏᴍᴍᴀɴᴅ.
- Tʜᴇ ʙᴏᴛ ᴍᴜsᴛ ʜᴀᴠᴇ ᴛʜᴇ ɴᴇᴄᴇssᴀʀʏ ᴘᴇʀᴍɪssɪᴏɴs ᴛᴏ ᴜɴʙᴀɴ ᴜsᴇʀs.
"""
