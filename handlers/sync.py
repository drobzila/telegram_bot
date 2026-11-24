from telegram import Update
from telegram.ext import ContextTypes


SCHEDULER_NOT_READY_MESSAGE = (
    "⚠️ النشر التلقائي لم يُفعّل بعد.\n\n"
    "يجب أولاً تحديد مصدر الفيديوهات وبناء عامل جدولة يعيد تشغيل المهام "
    "بعد إعادة تشغيل الخادم. لذلك لم نحفظ حالة تفعيل مضللة ولن نعرض أن "
    "المزامنة تعمل قبل اكتمالها."
)


async def sync_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(SCHEDULER_NOT_READY_MESSAGE)


async def sync_count_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(SCHEDULER_NOT_READY_MESSAGE)
