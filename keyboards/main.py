from telegram import ReplyKeyboardMarkup


def main_keyboard():

    keyboard = [

        ["📤 رفع فيديو", "📂 Google Drive"],

        ["🔗 ربط YouTube", "📊 الحالة"],

    ]

    return ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True,
        is_persistent=True
    )
