import logging
import threading

from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, PORT
from drive_utils import test_connection, count_videos

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------- خادم صغير فقط لإبقاء Render Web Service حيًّا ----------
web_app = Flask(__name__)


@web_app.route("/")
def health_check():
    return "🤖 البوت يعمل بشكل طبيعي"


def run_web_server():
    web_app.run(host="0.0.0.0", port=PORT)


# ---------- أوامر البوت ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "👋 أهلاً بك!\nأنا البوت الخاص بإدارة الفيديوهات.\n"
        "استخدم /help لعرض الأوامر المتاحة."
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "📋 الأوامر المتاحة:\n\n"
        "/start - بدء البوت\n"
        "/help - عرض هذه المساعدة\n"
        "/status - عرض حالة النظام\n"
        "/count - عرض عدد الفيديوهات في مجلد Google Drive"
    )
    await update.message.reply_text(text)


async def status(update: Update, context: ContextTypes.DEFAULT_TYPE):
    drive_ok = test_connection()
    video_count = "غير متاح"
    if drive_ok:
        try:
            video_count = count_videos()
        except Exception as e:
            logger.error(f"خطأ أثناء العد: {e}")
            video_count = "خطأ في القراءة"

    text = (
        "📊 حالة النظام\n\n"
        "✅ البوت يعمل\n"
        f"{'✅' if drive_ok else '❌'} الاتصال بـ Google Drive\n"
        f"📦 عدد الفيديوهات: {video_count}"
    )
    await update.message.reply_text(text)


async def count(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        n = count_videos()
        await update.message.reply_text(f"📦 عدد الفيديوهات: {n}")
    except Exception as e:
        logger.error(f"خطأ أثناء العد: {e}")
        await update.message.reply_text(f"⚠️ حدث خطأ أثناء قراءة المجلد:\n{e}")


def main():
    # تشغيل خادم Flask في خيط منفصل حتى لا يوقف Render الخدمة
    threading.Thread(target=run_web_server, daemon=True).start()

    app = Application.builder().token(BOT_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("count", count))

    logger.info("🚀 البوت بدأ العمل...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
