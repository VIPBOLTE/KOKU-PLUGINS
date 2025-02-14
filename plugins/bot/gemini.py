import requests
from KOKUAPI import api
from pyrogram import filters
from pyrogram.enums import ChatAction
from KOKUMUSIC import app


@app.on_message(filters.command(["gemini"], prefixes=["/", "!", "%", ",", "", ".", "@"]))
async def gemini_handler(client, message):
    await app.send_chat_action(message.chat.id, ChatAction.TYPING)
    
    # Extract user input
    if (
        message.text.startswith(f"/gemini@{app.username}")
        and len(message.text.split(" ", 1)) > 1
    ):
        user_input = message.text.split(" ", 1)[1]
    elif message.reply_to_message and message.reply_to_message.text:
        user_input = message.reply_to_message.text
    else:
        if len(message.command) > 1:
            user_input = " ".join(message.command[1:])
        else:
            await message.reply_text("ᴇxᴀᴍᴘʟᴇ :- `/gemini who is lord ram`")
            return

    try:
        # Call the API
        response = api.gemini(user_input)
        
        # Check if response is not None
        if response is not None and "results" in response:
            x = response["results"]
            if x:
                await message.reply_text(x, quote=True)
            else:
                await message.reply_text("sᴏʀʀʏ sɪʀ! ᴘʟᴇᴀsᴇ Tʀʏ ᴀɢᴀɪɴ")
        else:
            # Handle case where response is None or doesn't have "results"
            await message.reply_text("Sorry, no results found or API error.")
    
    except requests.exceptions.RequestException as e:
        # Log or handle the exception
        print(f"Request failed: {e}")
        await message.reply_text("There was an issue with the request. Please try again later.")
