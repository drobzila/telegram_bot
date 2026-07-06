from telegram import Update
from telegram.ext import ContextTypes

from database.states import get_state, get_state_data, set_state
from database.videos import update_video
from services.upload_service import UploadService

from handlers.status import status
from handlers.upload import start_upload

from states.state_names import (
    WAITING_VIDEO,
    WAITING_TITLE,
    WAITING_DESCRIPTION,
)


async def message_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id
    state = get_state(user_id)

    # ----------------------------------
    # انتظار إرسال الفيديو
    # ----------------------------------

    if state == WAITING_VIDEO:

        if update.message.video is None:

            await update.message.reply_text(
                "❌ الرجاء إرسال فيديو."
            )

            return

        telegram_video = update.message.video

        UploadService.receive_video(
            user_id,
            telegram_video
        )

        await update.message.reply_text(
            "✅ تم استلام الفيديو.\n\n"
            "📝 الآن أرسل عنوان الفيديو."
        )

        return

    # ----------------------------------
    # انتظار العنوان
    # ----------------------------------

    if state == WAITING_TITLE:

        title = update.message.text

        if not title:

            await update.message.reply_text(
                "📝 أرسل عنوانًا نصيًا."
            )

            return

        data = get_state_data(user_id)

        update_video(
            data["video_id"],
            title=title,
            status="waiting_description"
        )

        set_state(
            user_id,
            WAITING_DESCRIPTION
        )

        await update.message.reply_text(
            "✍️ ممتاز.\n\n"
            "الآن أرسل وصف الفيديو."
        )

        return

    # ----------------------------------
    # القائمة الرئيسية
    # ----------------------------------

    text = update.message.text

    if text == "📤 رفع فيديو":
        return await start_upload(update, context)

    if text == "📊 الحالة":
        return await status(update, context)

    await update.message.reply_text(
        "❓ اختر أحد الأزرار الموجودة في القائمة."
    )
