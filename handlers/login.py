import secrets

from telegram import Update
from telegram.ext import ContextTypes

from config import BASE_URL
from database.oauth_states import save_state


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()

    if not BASE_URL:
        await update.effective_message.reply_text(
            "⚠️ خدمة ربط YouTube غير مهيأة حاليًا. حاول لاحقًا."
        )
        return

    login_token = secrets.token_urlsafe(32)
    save_state(login_token, update.effective_user.id)
    url = f"{BASE_URL.rstrip('/')}/login/{login_token}"

    await update.effective_message.reply_text(
        "🎬 لربط حساب YouTube اضغط على الرابط التالي:\n\n"
        f"{url}\n\n"
        "أكمل تسجيل الدخول والموافقة لدى Google، ثم ستصلك رسالة تأكيد هنا."
    )
