import logging
import threading
import asyncio  # ضروري لإرسال الرسائل من الفلاسك إلى بيئة التليجرام غير المتزامنة

from flask import Flask, request
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, BotCommand
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, PORT
from database.db import initialize_database
from database.oauth_tokens import save_token
from database.users import get_user, set_youtube_connected

from handlers.start import start
from handlers.login import login
from handlers.help import help_command
from handlers.status import status
from handlers.admin import users_list, pending_deletions_list
from handlers.messages import message_router
from handlers.upload import upload_to_youtube
from handlers.drive_upload import (
    on_drive_select,
    on_drive_title_choice,
    on_drive_visibility,
    on_drive_page,
)
# استيراد معالجات المزامنة الجديدة
from handlers.sync import sync_handler, sync_count_handler
from services.youtube_auth import build_flow
# استيراد دالة فحص الاتصال وقراءة اسم القناة
from services.youtube_utils import test_youtube_connection

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


# ---------- خادم صغير لإبقاء Render حيًّا ومعالجة الـ OAuth ----------
web_app = Flask(__name__)

# قاموس لحفظ الـ user_id وكائن الـ flow الخاص بكل عملية مصادقة بشكل مؤقت
oauth_flows = {}

# متغيرات عالمية لمشاركة كائن تطبيق التليجرام والـ Loop مع خادم Flask
tg_application = None
tg_loop = None


@web_app.route("/")
def health_check():
    return "🤖 البوت يعمل بشكل طبيعي"


@web_app.route("/login/<int:user_id>")
def oauth_login(user_id):
    try:
        flow = build_flow()

        auth_url, state = flow.authorization_url(
            access_type="offline",
            prompt="consent",
        )

        # حفظ الـ telegram_id مباشرة هنا
        oauth_flows[state] = {
            "user_id": user_id, 
            "flow": flow,
        }

        return f"""
        <html>
            <script>
                window.location="{auth_url}";
            </script>
        </html>
        """
    except Exception as e:
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

        telegram_id = data["user_id"] # هذا هو الـ telegram_id مباشرة
        flow = data["flow"]

        # تحويل الرابط إلى https إجباري ليتوافق مع معايير Google
        authorization_response = request.url.replace("http://", "https://", 1)

        try:
            flow.fetch_token(authorization_response=authorization_response)
        except Exception:
            if hasattr(flow.oauth2session, "token"):
                print("TOKEN:", flow.oauth2session.token)
            if hasattr(flow.oauth2session, "_client"):
                print("CLIENT:", flow.oauth2session._client.__dict__)
            raise

        credentials = flow.credentials

        # 1. حفظ التوكن الجديد في قاعدة البيانات مباشرة عبر الـ telegram_id النظيف
        save_token(
            telegram_id,
            credentials.token,
            credentials.refresh_token,
            str(credentials.expiry),
        )

        # 2. تحديث حالة المستخدم في قاعدة البيانات
        set_youtube_connected(telegram_id)

        # 3. فحص صلاحية التوكن فوراً واختبار جلب اسم القناة
        ok, message = test_youtube_connection(telegram_id)

        # 4. إرسال الرسالة إلى تليجرام بشكل آمن عبر الـ Loop المشترك المتفق عليه (tg_loop)
        if tg_application and tg_loop:
            if ok:
                text_msg = f"✅ تم ربط حساب YouTube بنجاح.\n\n📺 **القناة:** {message}"
                keyboard = [
                    [
                        InlineKeyboardButton(
                            "⚡ تفعيل المزامنة",
                            callback_data="enable_sync"
                        )
                    ]
                ]
                reply_markup = InlineKeyboardMarkup(keyboard)
            else:
                text_msg = f"❌ فشل ربط حساب YouTube.\n\n⚠️ **السبب:** {message}"
                reply_markup = None
            
            # دفع المهمة لبيئة الـ Loop المحددة مسبقاً لمنع التجميد أو الانهيار
            asyncio.run_coroutine_threadsafe(
                tg_application.bot.send_message(
                    chat_id=telegram_id, 
                    text=text_msg, 
                    parse_mode="Markdown",
                    reply_markup=reply_markup
                ),
                tg_loop
            )

        return """
        <h2>✅ تم معالجة طلب الربط بنجاح</h2>
        <p>يمكنك الآن العودة إلى تطبيق Telegram واستخدام البوت بشكل طبيعي.</p>
        """
    except Exception as e:
        import traceback
        traceback.print_exc()
        return f"<pre>{traceback.format_exc()}</pre>", 500


def run_web_server():
    web_app.run(host="0.0.0.0", port=int(PORT), threaded=True)


async def post_init(application: Application):
    """يسجّل قائمة الأوامر المقترحة (الصندوق الذي يظهر عند كتابة /)."""
    await application.bot.set_my_commands([
        BotCommand("start", "بدء استخدام البوت"),
        BotCommand("help", "عرض الأوامر المتاحة"),
        BotCommand("status", "حالة حسابك"),
        BotCommand("login", "ربط حساب YouTube"),
    ])


def build_application():
    application = Application.builder().token(BOT_TOKEN).post_init(post_init).build()

    # تسجيل المعالجات للأوامر (Commands)
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("login", login))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("status", status))
    application.add_handler(CommandHandler("users", users_list))
    application.add_handler(CommandHandler("pending", pending_deletions_list))

    # معالج الفيديوهات (يستقبل الفيديوهات أولاً)
    application.add_handler(
        MessageHandler(
            filters.VIDEO,
            upload_to_youtube,
        )
    )

    # معالج النصوص (يتعامل مع الرسائل النصية المتبقية)
    application.add_handler(
        MessageHandler(
            filters.TEXT,
            message_router,
        )
    )

    # معالجات الأزرار التفاعلية (Inline Keyboards) لقوقل درايف
    application.add_handler(CallbackQueryHandler(on_drive_select, pattern=r"^drive_select:"))
    application.add_handler(CallbackQueryHandler(on_drive_title_choice, pattern=r"^drive_title:"))
    application.add_handler(CallbackQueryHandler(on_drive_visibility, pattern=r"^drive_visibility:"))
    application.add_handler(CallbackQueryHandler(on_drive_page, pattern=r"^drive_page:"))

    # معالجات المزامنة مع YouTube
    application.add_handler(
        CallbackQueryHandler(
            sync_handler,
            pattern=r"^enable_sync$"
        )
    )

    # زر البدء الإرشادي: /start -> ربط YouTube
    application.add_handler(
        CallbackQueryHandler(
            login,
            pattern=r"^guided_login$"
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            sync_count_handler,
            pattern=r"^sync_count:"
        )
    )

    return application


def main():
    global tg_application, tg_loop
    initialize_database()

    # تشغيل خادم ويب Flask في خيط منفصل لتفادي حظر البوت
    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    # بناء تطبيق البوت وإسناده للمتغير العام
    tg_application = build_application()

    logger.info("🚀 البوت بدأ العمل واستقبال التحديثات...")

    # الحصول الآمن على الـ Loop لضمان توافق خيوط الفلاسك والتليجرام
    try:
        tg_loop = asyncio.get_event_loop()
    except RuntimeError:
        tg_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(tg_loop)

    # تشغيل البوت عبر Polling وثبات التحديثات المعلقة
    tg_application.run_polling(
        drop_pending_updates=True,
        allowed_updates=["message", "callback_query"]
    )


if __name__ == "__main__":
    main()
