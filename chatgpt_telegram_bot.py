import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler, filters, ContextTypes
)
import openai

# Setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app.onrender.com

openai.api_key = OPENAI_API_KEY

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI app
app = FastAPI()

# Telegram app
application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Handle /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your GPT-3.5 chatbot 🤖")

# Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    logging.info(f"User said: {user_msg}")
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "user", "content": user_msg}
            ]
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"

    await update.message.reply_text(reply)

# Telegram handlers
application.add_handler(CommandHandler("start", start))
application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook endpoint
@app.post("/webhook")
async def telegram_webhook(req: Request):
    data = await req.json()
    update = Update.de_json(data, application.bot)
    await application.process_update(update)
    return {"ok": True}

# Initialize the bot on app startup
@app.on_event("startup")
async def startup():
    await application.initialize()
    logging.info("Bot initialized on startup ✅")
