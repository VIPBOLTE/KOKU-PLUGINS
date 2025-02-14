from pyrogram import Client
import config
from pymongo import MongoClient

app = Client(
    name = "SHUKLA",
    api_id = config.API_ID,
    api_hash = config.API_HASH,
    session_string = config.STRING1,
)
fuckraiddb = MongoClient(MONGO_DB_URI)

async def is_fuckraid_user(user_id: int) -> bool:
    user = await fuckraiddb.find_one({"user_id": user_id})
    if not user:
        return False
    return True


async def add_fuckraid_user(user_id: int) -> bool:
    is_fuckraid = await is_fuckraid_user(user_id)
    if is_fuckraid:
        return False
    await fuckraiddb.insert_one({"user_id": user_id})
    return True


async def del_fuckraid_user(user_id: int) -> bool:
    is_fuckraid = await is_fuckraid_user(user_id)
    if not is_fuckraid:
        return False
    await fuckraiddb.delete_one({"user_id": user_id})
    return True

@app.on_message(cdx(["fr", "rr", "rraid", "fuckraid"]))
async def add_fuck_raid(client, message):
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
                "**🤣 How Fool, You Want To Activate Reply Raid On Your Own ID❓**"
            )
        
        fraid = await add_fuckraid_user(user_id)
        if fraid:
            return await aux.edit(
                "**🤖 Successfully Added Reply Raid On This User.**"
            )
        return await aux.edit(
            "**🤖 Hey, Reply Raid Already Active On This User❗**"
        )
    except Exception as e:
        print("Error: `{e}`")
        return




@app.on_message(cdx(["dfr", "drr", "drraid", "dfuckraid"]))
async def del_fuck_raid(client, message):
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
                "**🤣 How Fool, When I Activate Reply Raid On Your ID❓**"
            )
        
        fraid = await del_fuckraid_user(user_id)
        if fraid:
            return await aux.edit(
                "**🤖 Successfully Removed Reply Raid From This User.**"
            )
        return await aux.edit(
            "**🤖 Hey, Reply Raid Not Active On This User❗**"
        )
    except Exception as e:
        print("Error: `{e}`")
        return
