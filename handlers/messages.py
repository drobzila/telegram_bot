from telegram import Update
from telegram.ext import ContextTypes

from database.states import get_state, get_state_data, set_state
from database.videos import update_video
from services.upload_service import UploadService

from handlers.status import status
from handlers.login import login
from handlers.upload import start_upload
from handlers.generate import show_generate_options
from handlers.drive_upload import (
    show_drive_videos,
    handle_custom_title_text,
)

from states.state_names import (
    IDLE,
    WAITING_VIDEO,
    WAITING_TITLE,
    WAITING_DESCRIPTION,
    WAITING_DRIVE_CUSTOM_TITLE,
)


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text

    if text == "🎬 إنشاء فيديو قرآن":
        set_state(user_id, IDLE)
        return await show_generate_options(update, context)

    if text == "📤 رفع فيديو":
        set_state(user_id, IDLE)
        return await start_upload(update, context)

    if text == "📊 الحالة":
        set_state(user_id, IDLE)
        return await status(update, context)

    if text == "📂 Google Drive":
        return await show_drive_videos(update, context)

    if text == "🔗 ربط YouTube":
        return await login(update, context)

    state = get_state(user_id)

    if state == WAITING_DRIVE_CUSTOM_TITLE:
        return await handle_custom_title_text(update, context)

    if state == WAITING_VIDEO:
        if update.message.video is None:
            await update.message.reply_text("❌ الرجاء إرسال فيديو.")
            return

        UploadService.receive_video(user_id, update.message.video)
        await update.message.reply_text(
            "✅ تم استلام الفيديو.\n\n📝 الآن أرسل عنوان الفيديو."
        )
        return

    if state == WAITING_TITLE:
        title = update.message.text
        if not title:
            await update.message.reply_text("📝 أرسل عنوانًا نصيًا.")
            return

        data = get_state_data(user_id)
        update_video(data["video_id"], title=title, status="waiting_description")
        set_state(user_id, WAITING_DESCRIPTION)
        await update.message.reply_text("✍️ ممتاز.\n\nالآن أرسل وصف الفيديو.")
        return

    await update.message.reply_text("❓ اختر أحد الأزرار الموجودة في القائمة.")
