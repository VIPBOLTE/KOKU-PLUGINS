from config import API_ID, API_HASH, STRING1, MONGO_DB_URI
from pyrogram import Client
app = Client(
    name = "SHUKLA",
    api_id = API_ID,
    api_hash = API_HASH,
    session_string = STRING1,
)
from pyrogram.types import *
from KOKUMUSIC.misc import SUDOERS
def sudo_users_only(mystic):
    async def wrapper(client, message):
        try:
            if (message.from_user.is_self or
               message.from_user.id in SUDOERS
            ):
                return await mystic(client, message)
        except:
            if (message.outgoing or
               message.from_user.id in SUDOERS
            ):
                return await mystic(client, message)
            
    return wrapper
    

from typing import Dict, List, Union


import os, sys

from pyrogram import Client
from pyrogram import filters
from pytgcalls import PyTgCalls
from motor.motor_asyncio import AsyncIOMotorClient
import logging
LOGGER = logging.getLogger("main")

def mongodbase():
    global mongodb
    try:
        LOGGER.info("Connecting To Your Database ...")
        async_client = AsyncIOMotorClient
        mongobase = async_client(MONGO_DB_URI)
        mongodb = mongobase.SHUKLA
        LOGGER.info("Conected To Your Database.")
    except:
        LOGGER.error("Failed To Connect, Please Change Your Mongo Database !")
        sys.exit()




loveraiddb = mongodb.loveraiddb

async def is_loveraid_user(user_id: int) -> bool:
    user = await loveraiddb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_loveraid_user(user_id: int) -> bool:
    is_loveraid = await is_loveraid_user(user_id)
    if is_loveraid:
        return False
    await loveraiddb.insert_one({"user_id": user_id})
    return True


async def del_loveraid_user(user_id: int) -> bool:
    is_loveraid = await is_loveraid_user(user_id)
    if not is_loveraid:
        return False
    await loveraiddb.delete_one({"user_id": user_id})
    return True
from typing import Union
from pyrogram.types import *


async def edit_or_reply(message: Message, *args, **kwargs) -> Message:
    try:
        msg = (
            message.edit_text
            if bool(message.from_user and message.from_user.is_self or message.outgoing)
            else (message.reply_to_message or message).reply_text
        )
    except:
        msg = (
            message.edit_text
            if bool(message.from_user and message.outgoing)
            else (message.reply_to_message or message).reply_text
        )
    
    return await msg(*args, **kwargs)


eor = edit_or_reply
from pyrogram import filters
from typing import Union, List

COMMAND_PREFIXES = list(getenv("COMMAND_PREFIXES", ". !").split())

def commandx(commands: Union[str, List[str]]):
    return filters.command(commands, COMMAND_PREFIXES)
cdx = commandx


@app.on_message(cdx(["lr", "lraid", "loveraid"]))
@sudo_users_only
async def add_love_raid(client, message):
    try:
        aux = await eor(message, "**🔄 Processing ...**")
        if not message.reply_to_message:
            if len(message.command) != 2:
                return await aux.edit(
                    "**🤖 Reply to a user's message or give username/user_id.**"
                )
            user = message.text.split(None, 1)[1]
            if "@" in user:
                user = user.replace("@", "")
            fulluser = await app.get_users(user)
            user_id = fulluser.id
        else:
            user_id = message.reply_to_message.from_user.id

        if user_id == message.from_user.id:
            return await aux.edit(
                "**🤣 How Fool, You Want To Activate Love Raid On Your Own ID❓**"
            )
        
        lraid = await add_loveraid_user(user_id)
        if lraid:
            return await aux.edit(
                "**🤖 Successfully Added Love Raid On This User.**"
            )
        return await aux.edit(
            "**🤖 Hey, Love Raid Already Active On This User❗**"
        )
    except Exception as e:
        print("Error: `{e}`")
        return




@app.on_message(cdx(["dlr", "dlraid", "dloveraid"]))
@sudo_users_only
async def del_love_raid(client, message):
    try:
        aux = await eor(message, "**🔄 Processing ...**")
        if not message.reply_to_message:
            if len(message.command) != 2:
                return await aux.edit(
                    "**🤖 Reply to a user's message or give username/user_id.**"
                )
            user = message.text.split(None, 1)[1]
            if "@" in user:
                user = user.replace("@", "")
            fulluser = await app.get_users(user)
            user_id = fulluser.id
        else:
            user_id = message.reply_to_message.from_user.id
        
        if user_id == message.from_user.id:
            return await aux.edit(
                "**🤣 How Fool, When I Activate Love Raid On Your ID❓**"
            )
        
        lraid = await del_loveraid_user(user_id)
        if lraid:
            return await aux.edit(
                "**🤖 Successfully Removed Love Raid From This User.**"
            )
        return await aux.edit(
            "**🤖 Hey, Love Raid Not Active On This User❗**"
        )
    except Exception as e:
        print("Error: `{e}`")
        return
