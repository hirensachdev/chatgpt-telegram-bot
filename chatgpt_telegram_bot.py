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

# ✅ ENVIRONMENT VARIABLES
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # e.g. https://your-app.onrender.com

if not all([TELEGRAM_BOT_TOKEN, OPENAI_API_KEY, WEBHOOK_URL]):
    raise RuntimeError("Missing one or more required environment variables")

# ✅ LOGGING
logging.basicConfig(level=logging.INFO)

# ✅ OpenAI Client (v1+)
client = OpenAI(api_key=OPENAI_API_KEY)

# ✅ Telegram Bot Setup
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# ✅ Command: /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("👋 Hello! I'm your ChatGPT bot. Ask me anything.")

# ✅ Handle messages
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    try:
        chat_response = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_msg}]
        )
        reply = chat_response.choices[0].message.content.strip()
    except Exception as e:
        logging.exception("OpenAI API error")
        reply = f"⚠️ Error: {str(e)}"
    await update.message.reply_text(reply)

# ✅ Register Handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# ✅ Webhook route
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# ✅ FastAPI Lifespan for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    await telegram_app.initialize()
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logging.info("🚀 Webhook set successfully")
    yield
    await telegram_app.shutdown()

# ✅ FastAPI App
app = FastAPI(lifespan=lifespan)
app.post("/webhook")(telegram_webhook)
