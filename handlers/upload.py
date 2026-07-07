import os
import tempfile

from telegram import Update
from telegram.ext import ContextTypes

from database.users import is_youtube_connected
from services.youtube_upload import upload_video
from database.db import get_connection

async def upload_to_youtube(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user

    if not is_youtube_connected(user.id):
        await update.message.reply_text(
            "❌ يجب أولاً ربط حساب YouTube.\n\nاستخدم /login"
        )
        return

    if update.message.video is None:
        await update.message.reply_text("❌ أرسل فيديو.")
        return

    status = await update.message.reply_text(
        "📥 جاري تنزيل الفيديو..."
    )

    video = await update.message.video.get_file()

    with tempfile.NamedTemporaryFile(
        suffix=".mp4",
        delete=False,
    ) as temp:

        temp_path = temp.name

    await video.download_to_drive(temp_path)

    await status.edit_text(
        "📤 جاري رفع الفيديو إلى YouTube..."
    )

    try:

        video_id = upload_video(
            user_id=user.id,
            video_path=temp_path,
            title=os.path.basename(temp_path),
            description="Uploaded بواسطة البوت",
            privacy="private",
        )

        await status.edit_text(
            f"✅ تم رفع الفيديو بنجاح\n\n"
            f"https://youtu.be/{video_id}"
        )

    finally:

        if os.path.exists(temp_path):
            os.remove(temp_path)
            
start_upload = upload_to_youtube

def add_video(
    user_id,
    path,
    title,
    description,
    time
):

    conn = get_connection()

    conn.execute("""
    INSERT INTO upload_queue
    (user_id,video_path,title,description,scheduled_time)
    VALUES(?,?,?,?,?)
    """,
    (
        user_id,
        path,
        title,
        description,
        time
    ))

    conn.commit()
    conn.close()