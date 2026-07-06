from telegram import Update
from telegram.ext import ContextTypes

from config import BASE_URL


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    url = f"{BASE_URL}/login/{user_id}"

    await update.message.reply_text(
        "🎬 لربط حساب YouTube اضغط على الرابط التالي:\n\n"
        f"{url}"
    )
