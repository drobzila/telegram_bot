from telegram import Update
from telegram.ext import ContextTypes

from config import ADMIN_IDS
from database.users import count_users
from database.users import list_users


async def users_list(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id not in ADMIN_IDS:

        await update.message.reply_text(
            "⛔ ليس لديك صلاحية."
        )

        return

    users = list_users()

    if not users:

        await update.message.reply_text(
            "لا يوجد مستخدمون."
        )

        return

    lines = [
        f"👥 عدد المستخدمين: {count_users()}",
        ""
    ]

    for user in users:

        username = (
            f"@{user['username']}"
            if user["username"]
            else "-"
        )

        lines.append(
            f"• {user['first_name']} | {username} | {user['telegram_id']}"
        )

    text = "\n".join(lines)

    for i in range(0, len(text), 4000):

        await update.message.reply_text(
            text[i:i + 4000]
        )
