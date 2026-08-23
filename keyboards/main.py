from telegram import ReplyKeyboardMarkup


def main_keyboard():
    keyboard = [
        ["🎬 إنشاء فيديو قرآن", "📤 رفع فيديو"],
        ["📂 Google Drive", "🔗 ربط YouTube"],
        ["📊 الحالة"],
    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True,
    )
