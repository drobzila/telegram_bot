from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main import main_keyboard

from database.users import register_user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    register_user(update.effective_user)

    text = (
        "👋 أهلاً بك.\n\n"
        "تم تسجيل حسابك بنجاح.\n\n"
        "استخدم /help لمعرفة جميع الأوامر."
    )

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard()
    )
