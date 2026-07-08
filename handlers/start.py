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

    await update.message.reply_text(
        text,
        reply_markup=main_keyboard()
    )

    step_text = (
        "🚀 للبدء، اتبع الخطوات التالية بالترتيب:\n\n"
        "1️⃣ اضغط على زر \"🔗 ربط YouTube\" في القائمة بالأسفل\n"
        "2️⃣ بعد نجاح الربط، فعّل المزامنة التلقائية\n"
        "3️⃣ ابدأ برفع فيديوهاتك من Google Drive 🎬"
    )

    await update.message.reply_text(step_text)
