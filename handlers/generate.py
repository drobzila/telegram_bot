from __future__ import annotations

import asyncio
import logging
import os
import tempfile

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.users import get_user_id, is_youtube_connected
from database.videos import create_video, update_video
from services import youtube_utils

logger = logging.getLogger(__name__)

RENDERER_URL = os.getenv("QURAN_RENDERER_URL", "").rstrip("/")
RENDERER_API_KEY = os.getenv("QURAN_RENDERER_API_KEY", "")
POLL_SECONDS = 5
MAX_WAIT_SECONDS = 30 * 60
DOWNLOAD_TIMEOUT = (15, 600)


def _headers():
    return {
        "X-Renderer-Key": RENDERER_API_KEY,
        "Accept": "application/json",
    }


async def show_generate_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not RENDERER_URL or not RENDERER_API_KEY:
        await update.message.reply_text(
            "⚠️ خدمة إنشاء الفيديو غير مهيأة بعد.\n\n"
            "تحقق من QURAN_RENDERER_URL و QURAN_RENDERER_API_KEY في إعدادات الخادم."
        )
        return

    if not is_youtube_connected(update.effective_user.id):
        await update.message.reply_text(
            "❌ يجب أولاً ربط حساب YouTube.\n\nاستخدم /login."
        )
        return

    keyboard = [
        [InlineKeyboardButton("🔒 خاص", callback_data="generate:private")],
        [InlineKeyboardButton("🔗 غير مدرج", callback_data="generate:unlisted")],
        [InlineKeyboardButton("🌍 عام", callback_data="generate:public")],
    ]

    await update.message.reply_text(
        "🎬 إنشاء فيديو قرآن عشوائي\n\n"
        "سيختار المولد آية عشوائية مناسبة، ثم ينشئ الفيديو ويرفعه مباشرة إلى YouTube.\n\n"
        "اختر مستوى الخصوصية:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


async def generate_random_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    telegram_id = update.effective_user.id
    privacy = query.data.split(":", 1)[1]
    video_db_id = None

    if not RENDERER_URL or not RENDERER_API_KEY:
        await query.edit_message_text("⚠️ خدمة إنشاء الفيديو غير مهيأة.")
        return

    if not is_youtube_connected(telegram_id):
        await query.edit_message_text("❌ يجب أولاً ربط حساب YouTube.")
        return

    internal_user_id = get_user_id(telegram_id)
    if internal_user_id is None:
        await query.edit_message_text("❌ لم يتم العثور على حسابك في قاعدة البيانات. أرسل /start ثم أعد المحاولة.")
        return

    try:
        video_db_id = await asyncio.to_thread(create_video, internal_user_id)
        if video_db_id is None:
            raise RuntimeError("تعذر إنشاء سجل الفيديو.")

        await query.edit_message_text(
            "🎬 جاري إنشاء فيديو قرآن عشوائي...\n\n"
            "⏳ قد يستغرق الرندر عدة دقائق."
        )

        response = await asyncio.to_thread(
            requests.post,
            f"{RENDERER_URL}/render",
            headers=_headers(),
            timeout=30,
        )
        response.raise_for_status()

        try:
            payload = response.json()
        except ValueError as exc:
            raise RuntimeError("خدمة الرندر أعادت استجابة غير صالحة.") from exc

        job_id = payload.get("job_id")
        if not job_id:
            raise RuntimeError("خدمة الرندر لم تُرجع job_id.")

        elapsed = 0
        last_status = None
        job = {}

        while elapsed < MAX_WAIT_SECONDS:
            await asyncio.sleep(POLL_SECONDS)
            elapsed += POLL_SECONDS

            status_response = await asyncio.to_thread(
                requests.get,
                f"{RENDERER_URL}/render/{job_id}",
                headers=_headers(),
                timeout=30,
            )
            status_response.raise_for_status()

            try:
                job = status_response.json()
            except ValueError as exc:
                raise RuntimeError("خدمة الرندر أعادت حالة غير صالحة.") from exc

            status = job.get("status")
            if status != last_status:
                logger.info("Renderer job %s status: %s", job_id, status)
                last_status = status

            if status == "failed":
                raise RuntimeError(job.get("error") or "فشل إنشاء الفيديو في خدمة الرندر.")
            if status == "completed":
                break
            if status in {"queued", "pending", "processing", "rendering"}:
                continue
            if status:
                logger.warning("Unknown renderer status for job %s: %s", job_id, status)
        else:
            raise TimeoutError("انتهت مهلة انتظار إنشاء الفيديو.")

        title = (job.get("title") or "تلاوة قرآنية عشوائية 🌿")[:100]
        await asyncio.to_thread(
            update_video,
            video_db_id,
            title=title,
            description="تلاوة قرآنية عشوائية تم إنشاؤها تلقائيًا.",
            status="rendered",
        )

        await query.edit_message_text(
            "✅ تم إنشاء الفيديو بنجاح!\n\n"
            f"📝 العنوان: {title}\n\n"
            "📤 جاري رفعه الآن إلى YouTube..."
        )

        with tempfile.NamedTemporaryFile(suffix=".mp4", delete=False) as temp_file:
            temp_path = temp_file.name

        try:
            download_response = await asyncio.to_thread(
                requests.get,
                f"{RENDERER_URL}/render/{job_id}/download",
                headers={"X-Renderer-Key": RENDERER_API_KEY},
                stream=True,
                timeout=DOWNLOAD_TIMEOUT,
            )
            download_response.raise_for_status()

            content_type = download_response.headers.get("Content-Type", "").lower()
            if "video" not in content_type and "octet-stream" not in content_type:
                raise RuntimeError("خدمة الرندر لم تُرجع ملف فيديو صالحًا.")

            def save_download():
                with open(temp_path, "wb") as output:
                    for chunk in download_response.iter_content(chunk_size=1024 * 1024):
                        if chunk:
                            output.write(chunk)
                download_response.close()

            await asyncio.to_thread(save_download)

            if os.path.getsize(temp_path) == 0:
                raise RuntimeError("ملف الفيديو الناتج فارغ.")

            with open(temp_path, "rb") as video_stream:
                youtube_video_id = await asyncio.to_thread(
                    youtube_utils.upload_video,
                    telegram_id,
                    video_stream,
                    title,
                    "تلاوة قرآنية عشوائية تم إنشاؤها تلقائيًا.",
                    privacy,
                    "video/mp4",
                )
        finally:
            if os.path.exists(temp_path):
                os.remove(temp_path)

        await asyncio.to_thread(
            update_video,
            video_db_id,
            youtube_video_id=youtube_video_id,
            status="uploaded",
        )

        await query.edit_message_text(
            "🎉 تم إنشاء الفيديو ورفعه إلى YouTube بنجاح!\n\n"
            f"📝 {title}\n\n"
            f"🔗 https://youtu.be/{youtube_video_id}"
        )

    except Exception as exc:
        logger.exception("Random Quran video generation failed")
        if video_db_id is not None:
            try:
                await asyncio.to_thread(update_video, video_db_id, status="failed")
            except Exception:
                logger.exception("Failed to mark video %s as failed", video_db_id)
        await query.edit_message_text(
            "❌ تعذر إنشاء أو رفع الفيديو.\n\n"
            "تحقق من إعدادات خدمة الرندر وYouTube ثم حاول مرة أخرى."
        )
