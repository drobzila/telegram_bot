import asyncio
import logging
import threading

from database.db import initialize_database
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN, PORT, ADMIN_IDS
from drive_utils import test_connection, count_videos
from users_store import register_user, get_all_users, count_users

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
    register_user(update.effective_user)
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
        "/count - عرض عدد الفيديوهات في مجلد Google Drive\n"
        "/users - عرض قائمة المستخدمين المسجلين (للمشرفين فقط)"
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


async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id not in ADMIN_IDS:
        await update.message.reply_text("⛔ هذا الأمر مخصص للمشرفين فقط.")
        return

    users = get_all_users()
    if not users:
        await update.message.reply_text("لا يوجد مستخدمون مسجلون بعد.")
        return

    lines = [f"👥 عدد المستخدمين المسجلين: {count_users()}\n"]
    for u in users:
        name = u.get("first_name") or ""
        username = f"@{u['username']}" if u.get("username") else "بدون اسم مستخدم"
        lines.append(f"• {name} — {username} — ID: {u['id']}")

    text = "\n".join(lines)
    # تيليجرام يحدد الرسالة بـ 4096 حرف، نقسّم إن لزم
    for i in range(0, len(text), 4000):
        await update.message.reply_text(text[i:i + 4000])


async def run_bot():
    application = Application.builder().token(BOT_TOKEN).build()
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("count", count))
    application.add_handler(CommandHandler("users", users_list))

    async with application:
        await application.start()
        await application.updater.start_polling(drop_pending_updates=True)
        logger.info("🚀 البوت بدأ العمل...")
        try:
            # يبقي البوت يعمل إلى ما لا نهاية حتى يتم إيقاف الخدمة
            await asyncio.Event().wait()
        finally:
            await application.updater.stop()
            await application.stop()


def main():
    
        initialize_database()

        threading.Thread(
            target=run_web_server,
            daemon=True
    ).start()

    asyncio.run(run_bot())
    
    # تشغيل خادم Flask في خيط منفصل حتى لا يوقف Render الخدمة
    threading.Thread(target=run_web_server, daemon=True).start()
    # asyncio.run() تُنشئ حلقة أحداث جديدة بمعزل عن أي حلقة قديمة/مفقودة،
    # وهذا يتجنب مشكلة "no current event loop" الموجودة في بايثون 3.14+
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
