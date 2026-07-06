import logging
import threading

from flask import Flask, request  # تم تحديث المستوردات
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, PORT
from database.db import initialize_database
from database.oauth_tokens import save_token  # استيراد دالة حفظ التوكن
from database.users import set_youtube_connected  # استيراد دالة تحديث حالة المستخدم

from handlers.start import start
from handlers.login import login  # استيراد أمر تسجيل الدخول
from handlers.help import help_command
from handlers.status import status
from handlers.admin import users_list
from handlers.messages import message_router
from handlers.drive_upload import (
    on_drive_select,
    on_drive_title_choice,
    on_drive_visibility,
    on_drive_page,
)
from services.youtube_auth import build_flow  # استيراد دالة الـ OAuth

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------- خادم صغير لإبقاء Render حيًّا ومعالجة الـ OAuth ----------
web_app = Flask(__name__)

# قاموس لتخزين الـ state وربطها بـ user_id مؤقتاً
oauth_states = {}


@web_app.route("/")
def health_check():
    return "🤖 البوت يعمل بشكل طبيعي"


@web_app.route("/login/<int:user_id>")
def oauth_login(user_id):
    flow = build_flow()

    auth_url, state = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
    )

    # حفظ الـ state لربطها بالمستخدم لاحقاً عند العودة من Google
    oauth_states[state] = user_id

    return f"""
    <html>
        <script>
            window.location="{auth_url}";
        </script>
    </html>
    """


@web_app.route("/oauth2callback")
def oauth_callback():
    state = request.args.get("state")

    # التحقق من أن الـ state صالحة وموجودة لدينا لمنع هجمات CSRF
    if state not in oauth_states:
        return "Invalid state", 400

    # استخراج الـ telegram_id وحذف الـ state من الذاكرة مؤقتاً
    telegram_id = oauth_states.pop(state)

    flow = build_flow()

    flow.fetch_token(
        authorization_response=request.url
    )

    credentials = flow.credentials

    # حفظ الـ Tokens والبيانات في قاعدة البيانات بشكل دائم
    save_token(
        user_id=telegram_id,
        access_token=credentials.token,
        refresh_token=credentials.refresh_token,
        expires_at=str(credentials.expiry),
    )

    # تحديث حالة المستخدم في جدول المستخدمين ليكون متصلاً بيوتيوب
    set_youtube_connected(telegram_id)

    return """
    <h2>✅ تم ربط حساب YouTube بنجاح</h2>
    <p>يمكنك الآن العودة إلى Telegram واستخدام البوت بشكل طبيعي.</p>
    """


def run_web_server():
    web_app.run(host="0.0.0.0", port=int(PORT), threaded=True)


def build_application():
    application = Application.builder().token(BOT_TOKEN).build()

    # تسجيل المعالجات للأوامر
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))  # معالج أمر تسجيل الدخول
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("users", users_list))

    application.add_handler(
        MessageHandler(
            filters.TEXT | filters.VIDEO,
            message_router,
        )
    )

    application.add_handler(
        CallbackQueryHandler(on_drive_select, pattern=r"^drive_select:")
    )
    application.add_handler(
        CallbackQueryHandler(on_drive_title_choice, pattern=r"^drive_title:")
    )
    application.add_handler(
        CallbackQueryHandler(on_drive_visibility, pattern=r"^drive_visibility:")
    )
    application.add_handler(
        CallbackQueryHandler(on_drive_page, pattern=r"^drive_page:")
    )

    return application


def main():
    initialize_database()

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    application = build_application()

    logger.info("🚀 البوت بدأ العمل...")

    application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    main()
