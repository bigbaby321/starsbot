from telegram import Update
from telegram.ext import Updater, CommandHandler, CallbackContext
from tinydb import TinyDB, Query
from datetime import datetime
import os

TOKEN = os.environ.get("TOKEN")
db = TinyDB("users.json")
User = Query()

def start(update: Update, context: CallbackContext):
    update.message.reply_text("👋 Bot Telegram USDT đã hoạt động!")

def main():
    updater = Updater(TOKEN, use_context=True)
    dp = updater.dispatcher
    dp.add_handler(CommandHandler("start", start))
    updater.start_polling()
    updater.idle()

if __name__ == "__main__":
    main()
