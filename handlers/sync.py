from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from database.youtube_settings import enable_sync
from database.users import get_user_id


async def sync_handler(update, context):

    query = update.callback_query
    await query.answer()

    keyboard = [
        [
            InlineKeyboardButton(
                "1 فيديو يومياً",
                callback_data="sync_count:1"
            )
        ],
        [
            InlineKeyboardButton(
                "2 فيديو يومياً",
                callback_data="sync_count:2"
            )
        ],
        [
            InlineKeyboardButton(
                "3 فيديوهات يومياً",
                callback_data="sync_count:3"
            )
        ],
        [
            InlineKeyboardButton(
                "4 فيديوهات يومياً",
                callback_data="sync_count:4"
            )
        ],
        [
            InlineKeyboardButton(
                "5 فيديوهات يومياً",
                callback_data="sync_count:5"
            )
        ],
    ]

    await query.edit_message_text(
        "📅 اختر عدد الفيديوهات التي تريد نشرها يومياً:",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


async def sync_count_handler(update, context):

    query = update.callback_query
    await query.answer()

    count = int(
        query.data.split(":")[1]
    )

    telegram_id = query.from_user.id
    user_id = get_user_id(telegram_id)

    if user_id is None:
        await query.edit_message_text(
            "⚠️ يجب عليك بدء البوت أولاً باستخدام الأمر /start قبل تفعيل المزامنة."
        )
        return

    # سيتم استبدالها لاحقاً بحساب أوقات ذكي
    times = {
        1: ["08:00"],
        2: ["08:00", "20:00"],
        3: ["08:00", "14:00", "20:00"],
        4: ["08:00", "12:00", "16:00", "20:00"],
        5: ["08:00", "11:00", "14:00", "17:00", "20:00"],
    }


    enable_sync(
        user_id,
        count,
        times[count]
    )


    await query.edit_message_text(
        f"""
✅ تم تفعيل المزامنة

📤 عدد الفيديوهات يومياً:
{count}

⏰ أوقات النشر:
{chr(10).join(times[count])}
"""
    )
