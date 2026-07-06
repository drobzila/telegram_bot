from telegram import Update
from telegram.ext import ContextTypes

from database.states import set_state
from states.state_names import WAITING_VIDEO


async def start_upload(update: Update,
                       context: ContextTypes.DEFAULT_TYPE):

    set_state(
        update.effective_user.id,
        WAITING_VIDEO
    )

    await update.message.reply_text(

        "📤 أرسل الفيديو الآن."

    )
