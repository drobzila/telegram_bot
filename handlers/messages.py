from telegram import Update
from telegram.ext import ContextTypes
from services.upload_service import UploadService
from handlers.status import status
from handlers.upload import start_upload

from states.state_names import (
    WAITING_VIDEO,
    WAITING_TITLE,
)


async def message_router(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    state = get_state(update.effective_user.id)

    # ----------------------------------
    # انتظار إرسال الفيديو
    # ----------------------------------

    if state == WAITING_VIDEO:

        from database.states import (
            get_state_data
        )

        from database.videos import (
            update_video
        )

        from states.state_names import (
            WAITING_DESCRIPTION
        )

        if update.message.video is None:

            await update.message.reply_text(
                "❌ الرجاء إرسال فيديو."
            )

            return
        
    if state == WAITING_TITLE:

    title = update.message.text

    if not title:

        await update.message.reply_text(
            "📝 أرسل عنوانًا نصيًا."
        )

        return

    data = get_state_data(
        update.effective_user.id
    )

    update_video(

        data["video_id"],

        title=title,

        status="waiting_description"

    )

    set_state(

        update.effective_user.id,

        WAITING_DESCRIPTION

    )

    await update.message.reply_text(

        "✍️ ممتاز.\n\n"
        "الآن أرسل وصف الفيديو."

    )

    return

        telegram_video = update.message.video

        UploadService.receive_video(

            update.effective_user.id,

            telegram_video
        )

        await update.message.reply_text(
            "✅ تم استلام الفيديو.\n\n"
            "📝 الآن أرسل عنوان الفيديو."
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
