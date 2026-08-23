from telegram import Update
from telegram.ext import ContextTypes
from keyboards.main import main_keyboard

from database.users import register_user


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    register_user(update.effective_user)

    text = (
        "👋 أهلاً بك.\n\n"
        "تم تسجيل حسابك بنجاح.\n\n"
        "💭 الحكمة ليست في عدد المشاهدات، وإن كان بالإمكان تحقيق ذلك، "
        "لكن الحكمة من هذا البوت هي نشر صوت القرآن الكريم، "
        "وأن يصل إلى قلوب الناس، وأن يكون في ميزان حسناتنا جميعاً.\n\n"
        "استخدم /help لمعرفة جميع الأوامر."
    )

    await update.message.reply_text(text, reply_markup=main_keyboard())

    await update.message.reply_text(
        "🚀 للبدء:\n\n"
        "1️⃣ اربط حساب YouTube من زر 🔗 ربط YouTube.\n"
        "2️⃣ اضغط 🎬 إنشاء فيديو قرآن.\n"
        "3️⃣ سيختار المولد آية عشوائية، ينشئ الفيديو، ثم يرفعه مباشرة إلى YouTube.\n\n"
        "📂 Google Drive ما زال متاحًا للرفع اليدوي، لكنه لم يعد مطلوبًا لإنشاء فيديو قرآن."
    )
