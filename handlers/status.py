import logging

from telegram import Update
from telegram.ext import ContextTypes

from drive_utils import test_connection
from drive_utils import count_videos

logger = logging.getLogger(__name__)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):

    drive_ok = test_connection()

    videos = "غير متاح"

    if drive_ok:
        try:
            videos = count_videos()
        except Exception as e:
            logger.exception(e)
            videos = "خطأ"

    text = (
        "📊 حالة النظام\n\n"
        "✅ البوت يعمل\n"
        f"{'✅' if drive_ok else '❌'} Google Drive\n"
        f"📦 الفيديوهات: {videos}"
    )

    await update.message.reply_text(text)
