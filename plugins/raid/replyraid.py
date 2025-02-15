from pymongo import MongoClient
from config import OWNER_ID, MONGO_DB_URI
import asyncio
from pyrogram import filters, Client
from pyrogram.types import *
from pyrogram import __version__
import os
import sys
import asyncio
import re
from pyrogram.enums import ChatType
from random import choice
from pyrogram import Client, filters
from pyrogram.types import Message
from utils.data import *
from pyrogram import Client, errors, filters
from pyrogram.types import ChatPermissions, Message

cli = MongoClient(MONGO_DB_URI)

RAIDS = []
async def get_ub_chats(
    client: Client,
    chat_types: list = [
        ChatType.GROUP,
        ChatType.SUPERGROUP,
        ChatType.CHANNEL,
    ],
    is_id_only=True,
):
    ub_chats = []
    async for dialog in client.get_dialogs():
        if dialog.chat.type in chat_types:
            if is_id_only:
                ub_chats.append(dialog.chat.id)
            else:
                ub_chats.append(dialog.chat)
        else:
            continue
    return ub_chats



collection = cli["Zaid"]["rraid"]


async def rraid_user(chat):
    doc = {"_id": "Rraid", "users": [chat]}
    r = await collection.find_one({"_id": "Rraid"})
    if r:
        await collection.update_one({"_id": "Rraid"}, {"$push": {"users": chat}})
    else:
        await collection.insert_one(doc)


async def get_rraid_users():
    results = await collection.find_one({"_id": "Rraid"})
    if results:
        return results["users"]
    else:
        return []


async def unrraid_user(chat):
    await collection.update_one({"_id": "Rraid"}, {"$pull": {"users": chat}})



def get_arg(message):
    msg = message.text
    msg = msg.replace(" ", "", 1) if msg[1] == " " else msg
    split = msg[1:].replace("\n", " \n").split(" ")
    if " ".join(split[1:]).strip() == "":
        return ""
    return " ".join(split[1:])
    
async def extract_userid(message, text: str):
    def is_int(text: str):
        try:
            int(text)
        except ValueError:
            return False
        return True

    text = text.strip()

    if is_int(text):
        return int(text)

    entities = message.entities
    app = message._client
    if len(entities) < 2:
        return (await app.get_users(text)).id
    entity = entities[1]
    if entity.type == "mention":
        return (await app.get_users(text)).id
    if entity.type == "text_mention":
        return entity.user.id
    return None


async def extract_user_and_reason(message, sender_chat=False):
    args = message.text.strip().split()
    text = message.text
    user = None
    reason = None
    if message.reply_to_message:
        reply = message.reply_to_message
        if not reply.from_user:
            if (
                reply.sender_chat
                and reply.sender_chat != message.chat.id
                and sender_chat
            ):
                id_ = reply.sender_chat.id
            else:
                return None, None
        else:
            id_ = reply.from_user.id

        if len(args) < 2:
            reason = None
        else:
            reason = text.split(None, 1)[1]
        return id_, reason

    if len(args) == 2:
        user = text.split(None, 1)[1]
        return await extract_userid(message, user), None

    if len(args) > 2:
        user, reason = text.split(None, 2)[1:]
        return await extract_userid(message, user), reason

    return user, reason


async def extract_user(message):
    return (await extract_user_and_reason(message))[0]


@Client.on_message(
    filters.command(["pornraid"], prefixes=["/", "!", "%", ",", "", ".", "@", "#"])
    & filters.user(OWNER_ID)
)
async def pornspam(xspam: Client, e: Message): 
    counts = e.command[0]
    if not counts:
        return await e.reply_text(usage)
    if int(e.chat.id) in GROUP:
         return await e.reply_text("**Sorry !! i Can't Spam Here.**")
    kkk = "**#Pornspam**"
    count = int(counts)
    for _ in range(count):
         prn = choice(PORM)
         if ".jpg" in prn or ".png" in prn:
              await xspam.send_photo(e.chat.id, prn, caption=kkk)
              await asyncio.sleep(0.4)
        
