import asyncio
from contextlib import suppress

from pyrogram import filters
from pyrogram.enums import ChatMembersFilter, ChatMemberStatus, ChatType
from pyrogram.types import (
    CallbackQuery,
    ChatPermissions,
    ChatPrivileges,
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from string import ascii_lowercase
from typing import Dict, Union

from KOKUMUSIC import app
from KOKUMUSIC.misc import SUDOERS
from KOKUMUSIC.core.mongo import mongodb
from utils.error import capture_err
from KOKUMUSIC.utils.keyboard import ikb
from KOKUMUSIC.utils.database import save_filter
from KOKUMUSIC.utils.functions import (
    extract_user,
    extract_user_and_reason,
    time_converter,
)
from utils.permissions import adminsOnly, member_permissions
from config import BANNED_USERS

warnsdb = mongodb.warns

__MODULE__ = "Bᴀɴ"
__HELP__ = """
/ban - Ban A User
/banall - Ban All Users
/sban - Delete all messages of user that sended in group and ban the user
/tban - Ban A User For Specific Time
/unban - Unban A User
/warn - Warn A User
/swarn - Delete all the message sended in group and warn the user
/rmwarns - Remove All Warning of A User
/warns - Show Warning Of A User
/kick - Kick A User
/skick - Delete the replied message kicking its sender
/purge - Purge Messages
/purge [n] - Purge "n" number of messages from replied message
/del - Delete Replied Message
/promote - Promote A Member
/fullpromote - Promote A Member With All Rights
/demote - Demote A Member
/pin - Pin A Message
/unpin - unpin a message
/unpinall - unpinall messages
/mute - Mute A User
/tmute - Mute A User For Specific Time
/unmute - Unmute A User
/zombies - Ban Deleted Accounts
/report | @admins | @admin - Report A Message To Admins."""


async def int_to_alpha(user_id: int) -> str:
    alphabet = list(ascii_lowercase)[:10]
    text = ""
    user_id = str(user_id)
    for i in user_id:
        text += alphabet[int(i)]
    return text


async def get_warns_count() -> dict:
    chats_count = 0
    warns_count = 0
    async for chat in warnsdb.find({"chat_id": {"$lt": 0}}):
        for user in chat["warns"]:
            warns_count += chat["warns"][user]["warns"]
        chats_count += 1
    return {"chats_count": chats_count, "warns_count": warns_count}


async def get_warns(chat_id: int) -> Dict[str, int]:
    warns = await warnsdb.find_one({"chat_id": chat_id})
    if not warns:
        return {}
    return warns["warns"]


async def get_warn(chat_id: int, name: str) -> Union[bool, dict]:
    name = name.lower().strip()
    warns = await get_warns(chat_id)
    if name in warns:
        return warns[name]


async def add_warn(chat_id: int, name: str, warn: dict):
    name = name.lower().strip()
    warns = await get_warns(chat_id)
    warns[name] = warn

    await warnsdb.update_one(
        {"chat_id": chat_id}, {"$set": {"warns": warns}}, upsert=True
    )


async def remove_warns(chat_id: int, name: str) -> bool:
    warnsd = await get_warns(chat_id)
    name = name.lower().strip()
    if name in warnsd:
        del warnsd[name]
        await warnsdb.update_one(
            {"chat_id": chat_id},
            {"$set": {"warns": warnsd}},
            upsert=True,
        )
        return True
    return False


@app.on_message(filters.command(["kick", "skick"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def kickFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message)
    if not user_id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ғɪɴᴅ ᴛʜᴀᴛ ᴜsᴇʀ")
    if user_id == app.id:
        return await message.reply_text("ɪ ᴄᴀɴ'ᴛ ᴋɪᴄᴋ ᴍʏsᴇʟғ, ɪ ᴄᴀɴ ʟᴇᴀᴠᴇ ɪғ ʏᴏᴜ ᴡᴀɴᴛ.")
    if user_id in SUDOERS:
        return await message.reply_text("ʏᴏᴜ ᴡᴀɴɴᴀ ᴋɪᴄᴋ ᴛʜᴇ ᴇʟᴇᴠᴀᴛᴇᴅ ᴏɴᴇ ?")
    if user_id in [
        member.user.id
        async for member in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]:
        return await message.reply_text(
            "ɪ ᴄᴀɴ'ᴛ ᴋɪᴄᴋ ᴀɴ ᴀᴅᴍɪɴ, ʏᴏᴜ ᴋɴᴏᴡ ᴛʜᴇ ʀᴜʟᴇs, ʏᴏᴜ ᴋɴᴏᴡ ᴛʜᴇ ʀᴜʟᴇs, sᴏ ᴅᴏ ɪ "
        )
    mention = (await app.get_users(user_id)).mention
    msg = f"""
**ᴋɪᴄᴋᴇᴅ ᴜsᴇʀ:** {mention}
**ᴋɪᴄᴋᴇᴅ ʙʏ:** {message.from_user.mention if message.from_user else 'ᴀɴᴏɴᴍᴏᴜs'}
**ʀᴇᴀsᴏɴ:** {reason or 'ɴᴏ ʀᴇᴀsᴏɴ ᴘʀᴏᴠɪᴅᴇᴅ'}"""
    await message.chat.ban_member(user_id)
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg)
    await asyncio.sleep(1)
    await message.chat.unban_member(user_id)
    if message.command[0][0] == "s":
        await message.reply_to_message.delete()
        await app.delete_user_history(message.chat.id, user_id)


# Ban members


@app.on_message(
    filters.command(["ban", "sban", "tban"]) & ~filters.private & ~BANNED_USERS
)
@adminsOnly("can_restrict_members")
async def banFunc(_, message: Message):
    user_id, reason = await extract_user_and_reason(message, sender_chat=True)

    if not user_id:
        return await message.reply_text("I can't find that user.")
    if user_id == app.id:
        return await message.reply_text("I can't ban myself, i can leave if you want.")
    if user_id in SUDOERS:
        return await message.reply_text("You Wanna Ban The Elevated One?, RECONSIDER!")
    if user_id in [
        member.user.id
        async for member in app.get_chat_members(
            chat_id=message.chat.id, filter=ChatMembersFilter.ADMINISTRATORS
        )
    ]:
        return await message.reply_text(
            "I can't ban an admin, You know the rules, so do i."
        )

    try:
        mention = (await app.get_users(user_id)).mention
    except IndexError:
        mention = (
            message.reply_to_message.sender_chat.title
            if message.reply_to_message
            else "Anon"
        )

    msg = (
        f"**Banned User:** {mention}\n"
        f"**Banned By:** {message.from_user.mention if message.from_user else 'Anon'}\n"
    )
    if message.command[0][0] == "s":
        await message.reply_to_message.delete()
        await app.delete_user_history(message.chat.id, user_id)
    if message.command[0] == "tban":
        split = reason.split(None, 1)
        time_value = split[0]
        temp_reason = split[1] if len(split) > 1 else ""
        temp_ban = await time_converter(message, time_value)
        msg += f"**Banned For:** {time_value}\n"
        if temp_reason:
            msg += f"**Reason:** {temp_reason}"
        with suppress(AttributeError):
            if len(time_value[:-1]) < 3:
                await message.chat.ban_member(user_id, until_date=temp_ban)
                replied_message = message.reply_to_message
                if replied_message:
                    message = replied_message
                await message.reply_text(msg)
            else:
                await message.reply_text("You can't use more than 99")
        return
    if reason:
        msg += f"**Reason:** {reason}"
    await message.chat.ban_member(user_id)
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(msg)


# Unban members


@app.on_message(filters.command("unban") & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def unban_func(_, message: Message):
    # we don't need reasons for unban, also, we
    # don't need to get "text_mention" entity, because
    # normal users won't get text_mention if the user
    # they want to unban is not in the group.
    reply = message.reply_to_message
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("I can't find that user.")

    if reply and reply.sender_chat and reply.sender_chat != message.chat.id:
        return await message.reply_text("You cannot unban a channel")

    await message.chat.unban_member(user_id)
    umention = (await app.get_users(user_id)).mention
    replied_message = message.reply_to_message
    if replied_message:
        message = replied_message
    await message.reply_text(f"Unbanned! {umention}")


# Promote Members
from pyrogram.types import InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery


@app.on_message(
    filters.command(["promote", "fullpromote"]) & ~filters.private & ~BANNED_USERS
)
@adminsOnly("can_promote_members")
async def promoteFunc(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("I can't find that user.")

    bot = (await app.get_chat_member(message.chat.id, app.id)).privileges

    if user_id == app.id:
        return await message.reply_text("I can't promote myself.")
    if not bot:
        return await message.reply_text("I'm not an admin in this chat.")
    if not bot.can_promote_members:
        return await message.reply_text("I don't have enough permissions")

    umention = (await app.get_users(user_id)).mention
    from_user_mention = message.from_user.mention

    if message.command[0][0] == "f":
        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=bot.can_change_info,
                can_invite_users=bot.can_invite_users,
                can_delete_messages=bot.can_delete_messages,
                can_restrict_members=bot.can_restrict_members,
                can_pin_messages=bot.can_pin_messages,
                can_promote_members=bot.can_promote_members,
                can_manage_chat=bot.can_manage_chat,
                can_manage_video_chats=bot.can_manage_video_chats,
            ),
        )
        await message.reply_text(
            f"Fully Promoted! {umention} \n by {from_user_mention}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Check Admin Power", callback_data=f"check_powers_{user_id}")]]
            )
        )
    else:
        await message.chat.promote_member(
            user_id=user_id,
            privileges=ChatPrivileges(
                can_change_info=False,
                can_invite_users=bot.can_invite_users,
                can_delete_messages=bot.can_delete_messages,
                can_restrict_members=False,
                can_pin_messages=bot.can_pin_messages,
                can_promote_members=False,
                can_manage_chat=bot.can_manage_chat,
                can_manage_video_chats=bot.can_manage_video_chats,
            ),
        )
        await message.reply_text(
            f"Promoted! {umention} \n by {from_user_mention}",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Check Admin Power", callback_data=f"check_powers_{user_id}")]]
            )
        )

# Handle callback to check and toggle admin powers
@app.on_callback_query(filters.regex(r"^check_powers_(\d+)"))
async def check_powers_callback(_, query: CallbackQuery):
    user_id = int(query.data.split("_")[2])
    bot = (await app.get_chat_member(query.message.chat.id, app.id)).privileges
    user_privileges = (await app.get_chat_member(query.message.chat.id, user_id)).privileges

    if not bot or not bot.can_promote_members:
        return await query.answer("I don't have the required permissions.", show_alert=True)

    def generate_privilege_buttons(privs):
        buttons = []
        for priv, name in [
            ("can_change_info", "Change Info"),
            ("can_invite_users", "Invite Users"),
            ("can_delete_messages", "Delete Messages"),
            ("can_restrict_members", "Restrict Members"),
            ("can_pin_messages", "Pin Messages"),
            ("can_promote_members", "Promote Members"),
            ("can_manage_chat", "Manage Chat"),
            ("can_manage_video_chats", "Manage Video Chats")
        ]:
            state = "✅ Allowed" if getattr(privs, priv, False) else "❌ Disallowed"
            buttons.append([InlineKeyboardButton(f"{name}: {state}", callback_data=f"toggle_{priv}_{user_id}")])
        buttons.append([InlineKeyboardButton("Back", callback_data="back")])
        buttons.append([InlineKeyboardButton("Close", callback_data="close")])
        return buttons

    await query.message.edit_caption(
        caption="Admin Powers:\n" + "\n".join(
            f"{name}: {'✅ Allowed' if getattr(user_privileges, priv, False) else '❌ Disallowed'}"
            for priv, name in [
                ("can_change_info", "Change Info"),
                ("can_invite_users", "Invite Users"),
                ("can_delete_messages", "Delete Messages"),
                ("can_restrict_members", "Restrict Members"),
                ("can_pin_messages", "Pin Messages"),
                ("can_promote_members", "Promote Members"),
                ("can_manage_chat", "Manage Chat"),
                ("can_manage_video_chats", "Manage Video Chats"),
            ]
        ),
        reply_markup=InlineKeyboardMarkup(generate_privilege_buttons(user_privileges))
    )

# Toggle admin power
@app.on_callback_query(filters.regex(r"^toggle_(.+)_(\d+)"))
async def toggle_power_callback(_, query: CallbackQuery):
    power, user_id = query.data.split("_")[1], int(query.data.split("_")[2])
    bot = (await app.get_chat_member(query.message.chat.id, app.id)).privileges

    if not bot or not getattr(bot, power, False):
        return await query.answer("I have no this power to give anyone", show_alert=True)

    # Get current user privileges
    current_privs = (await app.get_chat_member(query.message.chat.id, user_id)).privileges

    # Toggle the selected power
    new_privs = ChatPrivileges(
        can_change_info=current_privs.can_change_info,
        can_invite_users=current_privs.can_invite_users,
        can_delete_messages=current_privs.can_delete_messages,
        can_restrict_members=current_privs.can_restrict_members,
        can_pin_messages=current_privs.can_pin_messages,
        can_promote_members=current_privs.can_promote_members,
        can_manage_chat=current_privs.can_manage_chat,
        can_manage_video_chats=current_privs.can_manage_video_chats
    )
    setattr(new_privs, power, not getattr(current_privs, power))

    # Apply the new privileges
    await query.message.chat.promote_member(
        user_id=user_id,
        privileges=new_privs
    )

    await query.answer(
        f"{'Allowed' if getattr(new_privs, power) else 'Disallowed'} {power.replace('_', ' ').capitalize()}",
        show_alert=True
    )

    # Update the buttons and caption
    await check_powers_callback(_, query)

@app.on_callback_query(filters.regex(r"^close"))
async def close_callback(_, query: CallbackQuery):
    await query.message.delete()

@app.on_callback_query(filters.regex(r"^back"))
async def back_callback(_, query: CallbackQuery):
    await query.message.edit_caption("Action cancelled.")


# Demote Member


@app.on_message(filters.command("purge") & ~filters.private)
@adminsOnly("can_delete_messages")
async def purgeFunc(_, message: Message):
    repliedmsg = message.reply_to_message
    await message.delete()

    if not repliedmsg:
        return await message.reply_text("Reply to a message to purge from.")

    cmd = message.command
    if len(cmd) > 1 and cmd[1].isdigit():
        purge_to = repliedmsg.id + int(cmd[1])
        if purge_to > message.id:
            purge_to = message.id
    else:
        purge_to = message.id

    chat_id = message.chat.id
    message_ids = []

    for message_id in range(
        repliedmsg.id,
        purge_to,
    ):
        message_ids.append(message_id)

        # Max message deletion limit is 100
        if len(message_ids) == 100:
            await app.delete_messages(
                chat_id=chat_id,
                message_ids=message_ids,
                revoke=True,  # For both sides
            )

            # To delete more than 100 messages, start again
            message_ids = []

    # Delete if any messages left
    if len(message_ids) > 0:
        await app.delete_messages(
            chat_id=chat_id,
            message_ids=message_ids,
            revoke=True,
        )


@app.on_message(filters.command("del") & ~filters.private)
@adminsOnly("can_delete_messages")
async def deleteFunc(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply To A Message To Delete It")
    await message.reply_to_message.delete()
    await message.delete()


@app.on_message(filters.command("demote") & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_promote_members")
async def demote(_, message: Message):
    user_id = await extract_user(message)
    if not user_id:
        return await message.reply_text("I can't find that user.")
    if user_id == app.id:
        return await message.reply_text("I can't demote myself.")
    if user_id in SUDOERS:
        return await message.reply_text(
            "You wanna demote the elevated one?, RECONSIDER!"
        )
    try:
        member = await app.get_chat_member(message.chat.id, user_id)
        if member.status == ChatMemberStatus.ADMINISTRATOR:
            await message.chat.promote_member(
                user_id=user_id,
                privileges=ChatPrivileges(
                    can_change_info=False,
                    can_invite_users=False,
                    can_delete_messages=False,
                    can_restrict_members=False,
                    can_pin_messages=False,
                    can_promote_members=False,
                    can_manage_chat=False,
                    can_manage_video_chats=False,
                ),
            )
            umention = (await app.get_users(user_id)).mention
            await message.reply_text(f"Demoted! {umention}")
        else:
            await message.reply_text("The person you mentioned is not an admin.")
    except Exception as e:
        await message.reply_text(e)


# Pin Messages


@app.on_message(filters.command(["unpinall"]) & filters.group & ~BANNED_USERS)
@adminsOnly("can_pin_messages")
async def pin(_, message: Message):
    if message.command[0] == "unpinall":
        return await message.reply_text(
            "Aʀᴇ ʏᴏᴜ sᴜʀᴇ ʏᴏᴜ ᴡᴀɴᴛ ᴛᴏ ᴜɴᴘɪɴ ᴀʟʟ ᴍᴇssᴀɢᴇs?",
            reply_markup=InlineKeyboardMarkup(
                [
                    [
                        InlineKeyboardButton(text="ʏᴇs", callback_data="unpin_yes"),
                        InlineKeyboardButton(text="ɴᴏ", callback_data="unpin_no"),
                    ],
                ]
            ),
        )


@app.on_callback_query(filters.regex(r"unpin_(yes|no)"))
async def callback_query_handler(_, query: CallbackQuery):
    if query.data == "unpin_yes":
        await app.unpin_all_chat_messages(query.message.chat.id)
        return await query.message.edit_text("Aʟʟ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇs ʜᴀᴠᴇ ʙᴇᴇɴ ᴜɴᴘɪɴɴᴇᴅ.")
    elif query.data == "unpin_no":
        return await query.message.edit_text(
            "Uɴᴘɪɴ ᴏғ ᴀʟʟ ᴘɪɴɴᴇᴅ ᴍᴇssᴀɢᴇs ʜᴀs ʙᴇᴇɴ ᴄᴀɴᴄᴇʟʟᴇᴅ."
        )


@app.on_message(filters.command(["pin", "unpin"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_pin_messages")
async def pin(_, message: Message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to a message to pin/unpin it.")
    r = message.reply_to_message
    if message.command[0][0] == "u":
        await r.unpin()
        return await message.reply_text(
            f"Unpinned [this]({r.link}) message.",
            disable_web_page_preview=True,
        )
    await r.pin(disable_notification=True)
    await message.reply(
        f"Pinned [this]({r.link}) message.",
        disable_web_page_preview=True,
    )
    msg = "Please check the pinned message: ~ " + f"[Check, {r.link}]"
    filter_ = dict(type="text", data=msg)
    await save_filter(message.chat.id, "~pinned", filter_)


# Mute members


@app.on_message(filters.command(["mute", "tmute"]) & ~filters.private & ~BANNED_USERS)
@adminsOnly("can_restrict_members")
async def mute(_, message: 
