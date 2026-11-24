from telegram import Update
from telegram.ext import ContextTypes

from database.states import clear_state, set_state
from database.users import is_youtube_connected
from states.state_names import WAITING_VIDEO


async def start_upload(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if not is_youtube_connected(user_id):
        await update.effective_message.reply_text(
            "❌ يجب أولاً ربط حساب YouTube باستخدام /login."
        )
        return

    clear_state(user_id)
    set_state(user_id, WAITING_VIDEO)
    await update.effective_message.reply_text(
        "📤 أرسل الفيديو الذي تريد رفعه إلى YouTube."
    )
