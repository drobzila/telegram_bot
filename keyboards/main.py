from telegram import ReplyKeyboardMarkup


def main_keyboard():

    keyboard = [

        ["📤 رفع فيديو"],

        ["🔗 ربط YouTube", "📂 Google Drive"],

        ["⚙️ الإعدادات", "👤 حسابي"],

        ["📊 الحالة"]

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )
