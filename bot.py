import logging
import threading
import asyncio

from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand, Update
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
)

from config import BOT_TOKEN, PORT
from database.db import initialize_database
from database.oauth_tokens import save_token
from database.users import set_youtube_connected

from handlers.start import start
from handlers.login import login
from handlers.help import help_command
from handlers.status import status
from handlers.admin import users_list, pending_deletions_list
from handlers.messages import message_router
from handlers.upload import upload_to_youtube
from handlers.generate import generate_random_video
from handlers.drive_upload import (
    on_drive_select,
    on_drive_title_choice,
    on_drive_visibility,
    on_drive_page,
)
from handlers.sync import sync_handler, sync_count_handler
from services.youtube_auth import build_flow
from services.youtube_utils import test_youtube_connection

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)

web_app = Flask(__name__)
oauth_flows = {}
tg_application = None
tg_loop = None


@web_app.route("/")
def health_check():
    return "🤖 البوت يعمل بشكل طبيعي"


@web_app.route("/login/<int:user_id>")
def oauth_login(user_id):
    try:
        flow = build_flow()
        auth_url, state = flow.authorization_url(access_type="offline", prompt="consent")
        oauth_flows[state] = {"user_id": user_id, "flow": flow}
        return f'<html><script>window.location="{auth_url}";</script></html>'
    except Exception:
        import traceback
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500


@web_app.route("/oauth2callback")
def oauth_callback():
    try:
        print("🔍 Original Request URL:", request.url)
        state = request.args.get("state")
        data = oauth_flows.pop(state, None)
        if data is None:
            return "Invalid state", 400

        telegram_id = data["user_id"]
        flow = data["flow"]
        authorization_response = request.url.replace("http://", "https://", 1)
        flow.fetch_token(authorization_response=authorization_response)
        credentials = flow.credentials

        save_token(
            telegram_id,
            credentials.token,
            credentials.refresh_token,
            str(credentials.expiry),
        )
        set_youtube_connected(telegram_id)

        ok, message = test_youtube_connection(telegram_id)
        if tg_application and tg_loop:
            if ok:
                text_msg = f"✅ تم ربط حساب YouTube بنجاح.\n\n📺 **القناة:** {message}"
                keyboard = [[InlineKeyboardButton("⚡ تفعيل المزامنة", callback_data="enable_sync")]]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                text_msg = f"❌ فشل ربط حساب YouTube.\n\n⚠️ **السبب:** {message}"
                reply_markup = None

            asyncio.run_coroutine_threadsafe(
                tg_application.bot.send_message(
                    chat_id=telegram_id,
                    text=text_msg,
                    parse_mode="Markdown",
                    reply_markup=reply_markup,
                ),
                tg_loop,
            )

        return "<h2>✅ تم معالجة طلب الربط بنجاح</h2><p>يمكنك العودة إلى Telegram.</p>"
    except Exception:
        import traceback
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500


def run_web_server():
    web_app.run(host="0.0.0.0", port=int(PORT), threaded=True)


async def post_init(application: Application):
    await application.bot.set_my_commands([
        BotCommand("start", "بدء استخدام البوت"),
        BotCommand("help", "عرض الأوامر المتاحة"),
        BotCommand("status", "حالة حسابك"),
        BotCommand("login", "ربط حساب YouTube"),
    ])


async def log_update(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user = update.effective_user
        chat = update.effective_chat
        message = update.effective_message
        update_type = "unknown"
        if update.message:
            update_type = "message"
        elif update.callback_query:
            update_type = "callback_query"
        elif update.edited_message:
            update_type = "edited_message"
        elif update.channel_post:
            update_type = "channel_post"

        logger.info(
            "📥 INCOMING UPDATE | update_id=%s | type=%s | user_id=%s | chat_id=%s | text=%r",
            update.update_id,
            update_type,
            user.id if user else None,
            chat.id if chat else None,
            message.text if message and message.text else None,
        )
    except Exception:
        logger.exception("❌ Failed to log incoming update")


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logger.error("❌ TELEGRAM HANDLER ERROR", exc_info=context.error)
    if update is not None:
        logger.error("❌ Failed update: %r", update)


def build_application():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    application.add_handler(MessageHandler(filters.ALL, log_update), group=-100)
    application.add_handler(CallbackQueryHandler(log_update), group=-100)
    application.add_error_handler(error_handler)

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("users", users_list))
    application.add_handler(CommandHandler("pending", pending_deletions_list))

    application.add_handler(MessageHandler(filters.VIDEO, upload_to_youtube))
    application.add_handler(MessageHandler(filters.TEXT, message_router))

    application.add_handler(CallbackQueryHandler(generate_random_video, pattern=r"^generate:(private|unlisted|public)$"))
    application.add_handler(CallbackQueryHandler(on_drive_select, pattern=r"^drive_select:"))
    application.add_handler(CallbackQueryHandler(on_drive_title_choice, pattern=r"^drive_title:"))
    application.add_handler(CallbackQueryHandler(on_drive_visibility, pattern=r"^drive_visibility:"))
    application.add_handler(CallbackQueryHandler(on_drive_page, pattern=r"^drive_page:"))
    application.add_handler(CallbackQueryHandler(sync_handler, pattern=r"^enable_sync$"))
    application.add_handler(CallbackQueryHandler(sync_count_handler, pattern=r"^sync_count:"))

    return application


def main():
    global tg_application, tg_loop
    initialize_database()
    threading.Thread(target=run_web_server, daemon=True).start()
    tg_application = build_application()
    logger.info("🚀 البوت بدأ العمل واستقبال التحديثات...")

    try:
        tg_loop = asyncio.get_event_loop()
    except RuntimeError:
        tg_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(tg_loop)

    tg_application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"],
    )


if __name__ == "__main__":
    main()
