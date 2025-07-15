import os
import logging
from fastapi import FastAPI, Request
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
import openai

# Setup
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # Example: https://your-app.onrender.com

openai.api_key = OPENAI_API_KEY

# Logging
logging.basicConfig(level=logging.INFO)

# FastAPI app
app = FastAPI()

# Telegram bot
telegram_app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

# Handlers
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Hello! I'm your GPT-3.5 chatbot 🤖")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_msg = update.message.text
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": user_msg}]
        )
        reply = response.choices[0].message.content.strip()
    except Exception as e:
        reply = f"⚠️ Error: {str(e)}"
    await update.message.reply_text(reply)

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

# FastAPI webhook endpoint
@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    update = Update.de_json(data, telegram_app.bot)
    await telegram_app.process_update(update)
    return {"ok": True}

# Set Telegram webhook on startup
@app.on_event("startup")
async def on_startup():
    await telegram_app.bot.set_webhook(f"{WEBHOOK_URL}/webhook")
    logging.info("✅ Webhook set!")

# 🟢 Uvicorn entry point for Render deployment
import uvicorn

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run("chatgpt_telegram_bot:app", host="0.0.0.0", port=port)
