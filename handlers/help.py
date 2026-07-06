from telegram import Update
from telegram.ext import ContextTypes


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    text = (
        "📋 الأوامر المتوفرة:\n\n"
        "/start\n"
        "/help\n"
        "/status\n"
        "/users"
    )

    await update.message.reply_text(text)
