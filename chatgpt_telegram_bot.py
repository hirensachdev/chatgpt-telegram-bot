import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import (
    Application, CommandHandler, MessageHandler,
    ContextTypes, filters
)
from openai import OpenAI
from contextlib import asynccontextmanager

# Load env variables
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://yourapp.onrender.com

# Logging
logging.basicConfig(level=logging.INFO)

# OpenAI client
client = OpenAI(api_key=OPENAI_API_KEY)

# Telegram Application
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Telegram Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your GPT-3.5 bot 🤖")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    try:
        response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_msg}]
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
    await update.message.reply_text(reply)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# Webhook handler
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# Lifespan context to replace @app.on_event("startup")
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logging.info("✅ Webhook set successfully!")
    yield
    await telegram_app.shutdown()

# FastAPI App
app = FastAPI(lifespan=lifespan)

# FastAPI Route
app.post("/webhook")(telegram_webhook)
