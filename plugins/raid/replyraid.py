from config import API_ID, API_HASH, STRING1, MONGO_DB_URI
from pyrogram import Client
app = Client(
    name = "SHUKLA",
    api_id = API_ID,
    api_hash = API_HASH,
    session_string = STRING1,
)



from typing import Dict, List, Union


import os, sys

from pyrogram import Client
from pyrogram import filters
from pytgcalls import PyTgCalls
from motor.motor_asyncio import AsyncIOMotorClient


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



