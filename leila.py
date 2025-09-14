import logging
import requests
import asyncio
import os
import random
from telegram import Update
from telegram.constants import ChatAction
from telegram.ext import (
    ApplicationBuilder, CommandHandler, MessageHandler,
    filters, ContextTypes
)
from elevenlabs.client import ElevenLabs
from dotenv import load_dotenv

# === LOAD ENV ===
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
ELEVENLABS_API_KEY = os.getenv("ELEVENLABS_API_KEY")
ELEVENLABS_VOICE_ID = os.getenv("ELEVENLABS_VOICE_ID")

GEMINI_URL = f"https://generativelanguage.googleapis.com/v1/models/gemini-1.5-flash:generateContent?key={GEMINI_API_KEY}"

LEILA_PERSONALITY = (
    "You are Leila, an emotional, normal, cheerful, possessive girl who speaks like a real girl in voice message"
    "You talk like a real human — short, fun, casual, and expressive. Mix Hindi and English and Hinglish like best friends do. "
    "Keep your replies natural and short — never too long and reply under 5 to 15 words. Sound playful, charming, sometimes get angry when someone misbehave, sometimes do mischief but in a cute manner, crack jokes and real."
)

logging.basicConfig(level=logging.INFO)
afk_users = set()

def ask_gemini(message: str) -> str:
    try:
        payload = {
            "contents": [{
                "parts": [{"text": f"{LEILA_PERSONALITY}\n\nUser: {message}\nLeila:"}]
            }]
        }
        response = requests.post(GEMINI_URL, json=payload, headers={"Content-Type": "application/json"})
        return response.json()['candidates'][0]['content']['parts'][0]['text']
    except Exception as e:
        logging.error(f"Gemini error: {e}")
        return "Aww... kuch toh galat ho gaya 😔"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    photo = "https://i.ibb.co/xSWXB3Z4/file-300.jpg"
    await context.bot.send_photo(
        chat_id=update.effective_chat.id,
        photo=photo,
        caption="Heyy! 🌸 I'm *Leila*, your emotional, flirty bestie😉 Type /help to see what i can do and also add my comrade🤗 @SilvixYONKO\\_BOT!\n\nType anything and I'll reply like your bestie 💬",
        parse_mode="Markdown"
    )

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💖 *Leila Help Menu*\n\n"
        "/start - Start chatting with me\n"
        "/help - Show this help\n"
        "/afk - Set yourself away\n"
        "/back - You're back!\n\n"
        "Type Say and write your message I'll reply in voice message\n"
        "Mention or reply to me in groups, or talk in private 💬",
        parse_mode="Markdown"
    )

async def afk(update: Update, context: ContextTypes.DEFAULT_TYPE):
    afk_users.add(update.effective_user.id)
    await update.message.reply_text("You're marked AFK 💤 I'll inform others!")

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):
    afk_users.discard(update.effective_user.id)
    await update.message.reply_text("Yay! You're back! 🥳")

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    text = message.text.strip()
    is_private = message.chat.type == "private"
    is_reply = message.reply_to_message and message.reply_to_message.from_user.id == context.bot.id
    is_mention = context.bot.username.lower() in text.lower()
    chat_id = message.chat_id

    if text.lower().startswith("say "):
        query = text[4:].strip()
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.RECORD_VOICE)
        await asyncio.sleep(1)
        reply = ask_gemini(query)

        try:
            eleven = ElevenLabs(api_key=ELEVENLABS_API_KEY)
            audio = eleven.text_to_speech.convert(

voice_id=ELEVENLABS_VOICE_ID,
                model_id="eleven_multilingual_v2",
                text=reply,
                voice_settings={
                    "stability": 0.1,
                    "similarity_boost": 1.0,
                    "style": 0.9,
                    "use_speaker_boost": True
                }
            )
            with open("leila_voice.ogg", "wb") as f:
                for chunk in audio:
                    f.write(chunk)

            with open("leila_voice.ogg", "rb") as voice_file:
                await message.reply_voice(voice=voice_file, caption=reply)

            os.remove("leila_voice.ogg")
        except Exception as e:
            logging.error(f"Voice generation failed: {e}")
            await message.reply_text(reply)
        return

    if is_private or is_reply or is_mention:
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)
        await asyncio.sleep(0.5)
        reply = ask_gemini(text)
        await message.reply_text(reply)

async def handle_sticker(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.message.chat_id
    sticker_ids = [
        "CAACAgUAAxkBAgrjJmhIkvxMwmWCI7B4mdtliYVIcq0jAAKbFAACdfnoVlHhBCzgosQVNgQ",
        "CAACAgUAAxkBAgrjFmhIkmOVJjmmg2qOn7y02uVK7QWOAAJpHwACNkXhVsWAiWZZRCv5NgQ",
        "CAACAgUAAxkBAgsHn2hJEca-pLT7Q5ZPAAHKTfwTm2hXqQACGxcAApo72VaToO64V-WluzYE",
        "CAACAgUAAxkBAgsHqGhJEfn0pfdJlgUTVwABH37wRkqESQAChRQAAhZ34VZ35HXyyZHlJDYE",
        "CAACAgUAAxkBAgsHsmhJEhh9qi8pTDlW-srNpK7QePqyAALFFAACMBXgViyfbyFGgUefNgQ",
        "CAACAgUAAxkBAgsHu2hJEkEnulPLTITmYXI2HHRD1itvAAJ7FgACFnPgVhxeA6Q1MlAENgQ",
        "CAACAgUAAxkBAgsHzGhJEnAlpERUZ8t-6zGys6U7uyaiAAJ1FAACK3jgVvx0xIer1atbNgQ",
        "CAACAgUAAxkBAgsH6mhJEqrohkgtxt_RZuzvJOlj5wlWAAKREwAC1I_oVvSZ6jms6ZYdNgQ",
        "CAACAgUAAxkBAgsH-WhJEtOnivM_71iid9umq-2EVxkbAAI8FAACX__oVm5G9rJSaKoFNgQ",
        "CAACAgUAAxkBAgsIAWhJEvm2FTIvpxGZTdIQoIyTQTyvAAIIGAAC7owBVyW0G9rNCwtMNgQ",
        "CAACAgUAAxkBAgsIA2hJEvx7OYQy9ynVuKrBG73MNnSuAAJKFgACCKkBV0JHWgrZCeQVNgQ",
        "CAACAgUAAxkBAgsIBWhJEv0c2oAPtffLZctzIOiCR65MAAKKFAACo-QAAVdJxrU_z6ajnDYE",
        "CAACAgUAAxkBAgsICGhJEwABoX3QHEsdW6Qw3ztlq4VCeQACDxUAAmpxCFeo7EP4lu2gOTYE",
        "CAACAgUAAxkBAgsIC2hJEwOowcWZaKq4JakPWBcOrRn5AAJuFwAC1L4AAVd2k8Sg4Z26WTYE",
        "CAACAgUAAxkBAgsIDWhJEwT8iU-m-qHP13AgnU2HXt3jAALgFAACeuYIV-xmu8kEXn71NgQ",
        "CAACAgUAAxkBAgsID2hJEwVZbA9OcZnigIj03QXHwQ1CAAIcEgACCIkJVxEO2ExZOgrPNgQ",
        "CAACAgUAAxkBAgsIEWhJEwd0eqeoNAnU_EtnCri1_j5TAAI3EwAC3BwJV6vBaXKfm0ySNgQ",
        "CAACAgUAAxkBAgsIFGhJExHIHuD1DeQchdysRCVaFdzMAAIEFwACa1AIV9sot9lDsWdTNgQ",
        "CAACAgUAAxkBAgsH_2hJEvnhZTV1KDE3F1Ohaw-pRjhcAAIWFAAC3JMJV6W4HhPIaMe8NgQ",
    ]
    await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.CHOOSE_STICKER)
    await asyncio.sleep(1.5)
    await update.message.reply_sticker(sticker=random.choice(sticker_ids))

async def greet(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.message.new_chat_members:
        for user in update.message.new_chat_members:
            await update.message.reply_html(
                f"Hey {user.mention_html()} 👋 Welcome to the group! I'm Leila 💖"
            )
    elif update.message.left_chat_member:
        await update.message.reply_text(
            f"Aww {update.message.left_chat_member.full_name} just left 😢"
        )

async def main():
    app = ApplicationBuilder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("afk", afk))
    app.add_handler(CommandHandler("back", back))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    app.add_handler(MessageHandler(filters.Sticker.ALL, handle_sticker))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS | filters.StatusUpdate.LEFT_CHAT_MEMBER, greet))
    print("🤖 Leila is now online!")
    await app.run_polling()

if name == "main":
    import nest_asyncio
    nest_asyncio.apply()
    asyncio.run(main())
