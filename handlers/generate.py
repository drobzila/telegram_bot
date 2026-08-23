from __future__ import annotations

import asyncio
import io
import logging
import os

import requests
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes

from database.users import is_youtube_connected
from services import youtube_utils

logger = logging.getLogger(__name__)

RENDERER_URL = os.getenv("QURAN_RENDERER_URL", "").rstrip("/")
RENDERER_API_KEY = os.getenv("QURAN_RENDERER_API_KEY", "")
POLL_SECONDS = 5
MAX_WAIT_SECONDS = 30 * 60


def _headers():
    return {"X-Renderer-Key": RENDERER_API_KEY}


async def show_generate_options(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not RENDERER_URL or not RENDERER_API_KEY:
        await update.message.reply_text(
            "⚠️ خدمة إنشاء الفيديو غير مهيأة بعد.\n\n"
            "تحقق من QURAN_RENDERER_URL و QURAN_RENDERER_API_KEY في Render."
        )
        return

    if not is_youtube_connected(update.effective_user.id):
        await update.message.reply_text(
            "❌ يجب أولاً ربط حساب YouTube.\n\nاستخدم زر 🔗 ربط YouTube."
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

    user_id = update.effective_user.id
    privacy = query.data.split(":", 1)[1]

    if not RENDERER_URL or not RENDERER_API_KEY:
        await query.edit_message_text("⚠️ خدمة إنشاء الفيديو غير مهيأة.")
        return

    if not is_youtube_connected(user_id):
        await query.edit_message_text("❌ يجب أولاً ربط حساب YouTube.")
        return

    try:
        await query.edit_message_text(
            "🎬 جاري إنشاء فيديو قرآن عشوائي...\n\n"
            "⏳ قد يستغرق الرندر عدة دقائق. لا تغلق المحادثة."
        )

        response = await asyncio.to_thread(
            requests.post,
            f"{RENDERER_URL}/render",
            headers=_headers(),
            timeout=30,
        )
        response.raise_for_status()
        job_id = response.json()["job_id"]

        elapsed = 0
        last_status = None
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
            job = status_response.json()
            status = job.get("status")

            if status != last_status:
                logger.info("Renderer job %s status: %s", job_id, status)
                last_status = status

            if status == "failed":
                raise RuntimeError(job.get("error") or "فشل الرندر")

            if status == "completed":
                break
        else:
            raise TimeoutError("انتهت مهلة انتظار الرندر")

        title = job.get("title") or "تلاوة قرآنية عشوائية 🌿"
        await query.edit_message_text(
            "✅ تم إنشاء الفيديو بنجاح!\n\n"
            f"📝 العنوان: {title}\n\n"
            "📤 جاري رفعه الآن إلى YouTube..."
        )

        download_response = await asyncio.to_thread(
            requests.get,
            f"{RENDERER_URL}/render/{job_id}/download",
            headers=_headers(),
            timeout=120,
        )
        download_response.raise_for_status()
        video_stream = io.BytesIO(download_response.content)
        video_stream.seek(0)

        youtube_video_id = await asyncio.to_thread(
            youtube_utils.upload_video,
            user_id,
            video_stream,
            title,
            "تلاوة قرآنية عشوائية تم إنشاؤها تلقائيًا.",
            privacy,
            "video/mp4",
        )

        await query.edit_message_text(
            "🎉 تم إنشاء الفيديو ورفعه إلى YouTube بنجاح!\n\n"
            f"📝 {title}\n\n"
            f"🔗 https://youtu.be/{youtube_video_id}"
        )

    except Exception as exc:
        logger.exception("Random Quran video generation failed")
        await query.edit_message_text(
            "❌ تعذر إنشاء أو رفع الفيديو.\n\n"
            f"التفاصيل: {exc}"
        )
