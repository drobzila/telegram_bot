import asyncio
import logging
import os
import tempfile
from datetime import datetime

from telegram import Update
from telegram.ext import ContextTypes

from database.states import clear_state, get_state, get_state_data, set_state, set_state_data
from database.videos import update_video
from database.users import is_youtube_connected
from services.upload_service import UploadService
from services.youtube_upload import upload_video

from handlers.status import status
from handlers.login import login
from handlers.upload import start_upload
from handlers.generate import show_generate_options
from handlers.drive_upload import show_drive_videos, handle_custom_title_text

from states.state_names import (
    IDLE,
    WAITING_VIDEO,
    WAITING_TITLE,
    WAITING_DESCRIPTION,
    WAITING_DRIVE_CUSTOM_TITLE,
)

logger = logging.getLogger(__name__)


async def message_router(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.effective_message
    if message is None:
        return

    user_id = update.effective_user.id
    text = message.text or ""
    state = get_state(user_id)

    if text == "🎬 إنشاء فيديو قرآن":
        clear_state(user_id)
        set_state(user_id, IDLE)
        return await show_generate_options(update, context)

    if text == "📤 رفع فيديو":
        return await start_upload(update, context)

    if text == "📊 الحالة":
        clear_state(user_id)
        set_state(user_id, IDLE)
        return await status(update, context)

    if text == "📂 Google Drive":
        clear_state(user_id)
        return await show_drive_videos(update, context)

    if text == "🔗 ربط YouTube":
        return await login(update, context)

    if state == WAITING_DRIVE_CUSTOM_TITLE:
        return await handle_custom_title_text(update, context)

    if state == WAITING_VIDEO:
        if message.video is None:
            await message.reply_text("❌ الرجاء إرسال ملف فيديو.")
            return
        if not is_youtube_connected(user_id):
            clear_state(user_id)
            await message.reply_text("❌ اربط حساب YouTube أولاً باستخدام /login.")
            return
        try:
            UploadService.receive_video(user_id, message.video)
        except Exception:
            logger.exception("Could not save incoming video for user %s", user_id)
            clear_state(user_id)
            await message.reply_text("⚠️ تعذر حفظ الفيديو. حاول بدء الرفع من جديد.")
            return
        await message.reply_text("✅ تم استلام الفيديو.\n\n📝 أرسل عنوان الفيديو (حتى 100 حرف).")
        return

    if state == WAITING_TITLE:
        if message.video or not text.strip():
            await message.reply_text("📝 أرسل عنوان الفيديو كنص.")
            return
        title = text.strip()
        if len(title) > 100:
            await message.reply_text("⚠️ يجب ألا يتجاوز العنوان 100 حرف.")
            return
        data = get_state_data(user_id)
        if not data.get("video_id"):
            clear_state(user_id)
            await message.reply_text("⚠️ انتهت جلسة الرفع. ابدأ من جديد.")
            return
        update_video(data["video_id"], title=title, status="waiting_description")
        data["title"] = title
        set_state_data(user_id, data)
        set_state(user_id, WAITING_DESCRIPTION)
        await message.reply_text("✍️ أرسل وصف الفيديو الآن (حتى 5000 حرف).")
        return

    if state == WAITING_DESCRIPTION:
        if message.video or message.text is None:
            await message.reply_text("✍️ أرسل وصف الفيديو كنص.")
            return
        description = text.strip()
        if len(description) > 5000:
            await message.reply_text("⚠️ يجب ألا يتجاوز الوصف 5000 حرف.")
            return
        data = get_state_data(user_id)
        video_id = data.get("video_id")
        file_id = data.get("telegram_file_id")
        title = data.get("title")
        if not video_id or not file_id or not title:
            clear_state(user_id)
            await message.reply_text("⚠️ بيانات الرفع غير مكتملة. ابدأ من جديد.")
            return

        status_message = await message.reply_text("⏳ جارٍ تنزيل الفيديو ثم رفعه إلى YouTube...")
        temp_path = None
        try:
            update_video(video_id, description=description, status="uploading")
            telegram_file = await context.bot.get_file(file_id)
            with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp:
                temp_path = temp.name
            await telegram_file.download_to_drive(custom_path=temp_path)

            youtube_video_id = await asyncio.to_thread(
                upload_video,
                user_id,
                temp_path,
                title,
                description,
                "private",
            )
            update_video(
                video_id,
                youtube_video_id=youtube_video_id,
                status="uploaded",
                uploaded_at=datetime.utcnow(),
            )
            clear_state(user_id)
            await status_message.edit_text(
                "✅ تم رفع الفيديو بنجاح!\n\n"
                f"🎬 {title}\n"
                f"🔗 https://youtu.be/{youtube_video_id}"
            )
        except Exception:
            logger.exception("Telegram video upload failed for user %s", user_id)
            update_video(video_id, status="failed")
            clear_state(user_id)
            await status_message.edit_text(
                "❌ فشل رفع الفيديو إلى YouTube. لم يتم حذف الفيديو من المحادثة. "
                "تحقق من ربط الحساب وحاول مرة أخرى."
            )
        finally:
            if temp_path and os.path.exists(temp_path):
                os.remove(temp_path)
        return

    if message.video:
        await message.reply_text("📤 اختر «رفع فيديو» من القائمة أولاً، ثم أرسل الفيديو.")
        return

    await message.reply_text("❓ اختر أحد الأزرار الموجودة في القائمة.")
