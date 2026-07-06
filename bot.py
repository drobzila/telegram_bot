import asyncio
import logging
import threading

from flask import Flask
from telegram.ext import (
    Application,
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


async def run_bot():
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

    # asyncio.run() تُنشئ حلقة أحداث جديدة بمعزل عن أي حلقة قديمة/مفقودة
    asyncio.run(run_bot())


if __name__ == "__main__":
    main()
