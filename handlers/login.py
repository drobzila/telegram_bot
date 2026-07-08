from telegram import Update
from telegram.ext import ContextTypes

from config import BASE_URL


async def login(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        await update.callback_query.answer()

    user_id = update.effective_user.id

    url = f"{BASE_URL}/login/{user_id}"

    await update.message.reply_text(
        "🎬 لربط حساب YouTube اضغط على الرابط التالي:\n\n"
        f"{url}\n\n"
        "⚠️ ملاحظة مهمة:\n"
        "ستظهر لك شاشة من جوجل مكتوب فيها:\n"
        "\"لم تثبت شركة Google ملكية هذا التطبيق\"\n\n"
        "هذا أمر طبيعي (التطبيق قيد المراجعة من Google)، ولإكمال الربط:\n"
        "1️⃣ اضغط \"الخيارات المتقدمة\" (Advanced) أسفل الرسالة\n"
        "2️⃣ ثم اضغط \"الانتقال إلى ... (غير آمن)\" للمتابعة\n"
        "3️⃣ أكمل السماح بالصلاحيات المطلوبة\n\n"
        "بعد ذلك سيصلك تأكيد نجاح الربط هنا في البوت تلقائياً."
    )
