import logging
import threading

from flask import Flask
from telegram.ext import (
    Application,
    CallbackQueryHandler,
    CommandHandler,
    MessageHandler,
    filters,
)

from config import BOT_TOKEN, PORT
from database.db import initialize_database

from handlers.start import start
from handlers.help import help_command
from handlers.status import status
from handlers.admin import users_list
from handlers.messages import message_router
from handlers.drive_upload import (
    on_drive_select,
    on_drive_title_choice,
    on_drive_visibility,
)

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


def build_application():
    application = Application.builder().token(BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
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

    return application


def main():
    initialize_database()

    threading.Thread(
        target=run_web_server,
        daemon=True
    ).start()

    application = build_application()

    logger.info("🚀 البوت بدأ العمل...")

    # run_polling() تُدير حلقة الأحداث بنفسها، وتسجّل تلقائيًا معالجات
    # إشارات الإيقاف (SIGTERM/SIGINT) لضمان إغلاق نظيف عند إعادة النشر،
    # وهذا يمنع تعارض "Conflict: terminated by other getUpdates request"
    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
