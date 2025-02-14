from ChampuMusic import app
from pyrogram import filters
import nekos
import os

# Function for each command
@app.on_message(filters.command("wallpaper"))
async def wallpaper(client, message):
    try:
        await message.reply_video(nekos.img("wallpaper"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("ngif"))
async def ngif(client, message):
    try:
        await message.reply_video(nekos.img("ngif"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("tickle"))
async def tickle(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("tickle"),
                caption=f"{message.from_user.mention} ᴛɪᴄᴋʟᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("tickle"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("feed"))
async def feed(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("feed"),
                caption=f"{message.from_user.mention} ғᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("feed"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("gecg"))
async def gecg(client, message):
    try:
        await message.reply_video(nekos.img("gecg"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("gasm"))
async def gasm(client, message):
    try:
        await message.reply_video(nekos.img("gasm"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("slap"))
async def slap(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("slap"),
                caption=f"{message.from_user.mention} sʟᴀᴘᴘᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("slap"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("slap"))
async def slap(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("slap"),
                caption=f"{message.from_user.mention} sʟᴀᴘᴘᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("slap"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("lizard"))
async def lizard(client, message):
    try:
        await message.reply_video(nekos.img("lizard"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("waifu"))
async def waifu(client, message):
    try:
        await message.reply_video(nekos.img("waifu"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("pat"))
async def pat(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("pat"),
                caption=f"{message.from_user.mention} ᴘᴀᴛᴛᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("pat"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")


@app.on_message(filters.command("kiss"))
async def kiss(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("kiss"),
                caption=f"{message.from_user.mention} ᴋɪssᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("kiss"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("neko"))
async def neko(client, message):
    try:
        await message.reply_video(nekos.img("neko"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message (filters.command("spank"))
async def spank(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("spank"),
                caption=f"{message.from_user.mention} sᴘᴀɴᴋᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("spank"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("cuddle"))
async def cuddle(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("cuddle"),
                caption=f"{message.from_user.mention} ᴄᴜᴅᴅʟᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("cuddle"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("fox_girl"))
async def fox_girl(client, message):
    try:
        await message.reply_video(nekos.img("fox_girl"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("hug"))
async def hug(client, message):
    try:
        if message.reply_to_message:
            await message.reply_video(
                nekos.img("hug"),
                caption=f"{message.from_user.mention} ʜᴜɢɢᴇᴅ {message.reply_to_message.from_user.mention}",
            )
        else:
            await message.reply_video(nekos.img("hug"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("smug"))
async def smug(client, message):
    try:
        await message.reply_video(nekos.img("smug"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("goose"))
async def goose(client, message):
    try:
        await message.reply_video(nekos.img("goose"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")

@app.on_message(filters.command("woof"))
async def woof(client, message):
    try:
        await message.reply_video(nekos.img("woof"))
    except Exception as e:
        await message.reply_text(f"Error: {e}")


__MODULE__ = "Hᴜɢ"
__HELP__ = """
Tʜɪs ʙᴏᴛ ʀᴇsᴘᴏɴᴅs ᴛᴏ ᴛʜᴇ ғᴏʟʟᴏᴡɪɴɢ ᴄᴏᴍᴍᴀɴᴅs:

- /hug: Sᴇɴᴅs ᴀ ʜᴜɢɢɪɴɢ ᴀɴɪᴍᴀᴛɪᴏɴ.

**Cᴏᴍᴍᴀɴᴅs**

- /hug: Sᴇɴᴅs ᴀ ʜᴜɢɢɪɴɢ ᴀɴɪᴍᴀᴛɪᴏɴ. Iғ ᴜsᴇᴅ ᴀs ᴀ ʀᴇᴘʟʏ ᴛᴏ ᴀɴᴏᴛʜᴇʀ ᴍᴇssᴀɢᴇ, ɪᴛ ᴍᴇɴᴛɪᴏɴs ᴛʜᴇ sᴇɴᴅᴇʀ ᴀɴᴅ ʀᴇᴄɪᴘɪᴇɴᴛ ᴏғ ᴛʜᴇ ʜᴜɢ.

**Hᴏᴡ ᴛᴏ Usᴇ**

- Usᴇ /hug ᴛᴏ sᴇɴᴅ ᴀ ʜᴜɢɢɪɴɢ ᴀɴɪᴍᴀᴛɪᴏɴ.
- Rᴇᴘʟʏ ᴛᴏ ᴀ ᴍᴇssᴀɢᴇ ᴡɪᴛʜ /ʜᴜ ᴛᴏ sᴇɴᴅ ᴀ ʜᴜɢɢɪɴɢ ᴀɴɪᴍᴀᴛɪᴏɴ ᴍᴇɴᴛɪᴏɴɪɴɢ ᴛʜᴇ sᴇɴᴅᴇʀ ᴀɴᴅ ʀᴇᴄɪᴘɪᴇɴᴛ.

**Nᴏᴛᴇs**

- Eɴsᴜʀᴇ ʏᴏᴜʀ ᴄʜᴀᴛ sᴇᴛᴛɪɴɢs ᴀʟʟᴏᴡ ᴛʜᴇ ʙᴏᴛ ᴛᴏ sᴇɴᴅ ᴠɪᴅᴇᴏs/sᴛɪᴄᴋᴇʀs ᴀs ʀᴇᴘʟɪᴇs ғᴏʀ ғᴜʟʟ ғᴜɴᴄᴛɪᴏɴᴀʟɪᴛʏ."""
