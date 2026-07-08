import asyncio
import logging
import os
from datetime import datetime, timezone

from telegram import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    Update,
)
from telegram.ext import ContextTypes

import drive_utils
from services import youtube_utils

from database.states import (
    get_state_data,
    set_state,
    set_state_data,
    clear_state,
)
from database.users import get_user
from database.videos import create_video, update_video

from states.state_names import (
    IDLE,
    WAITING_DRIVE_CUSTOM_TITLE,
)

logger = logging.getLogger(__name__)

PRIVACY_LABELS = {
    "private": "🔒 خاص",
    "unlisted": "🔗 غير مدرج",
    "public": "🌍 عام",
}

PAGE_SIZE = 20
MAX_BUTTON_LABEL = 60


def _strip_extension(filename):
    return os.path.splitext(filename)[0]


def _truncate_label(name):
    if len(name) > MAX_BUTTON_LABEL:
        return name[:MAX_BUTTON_LABEL - 1] + "…"
    return name


def _build_videos_keyboard(videos, offset):
    page = videos[offset:offset + PAGE_SIZE]

    keyboard = [
        [InlineKeyboardButton(
            _truncate_label(video["name"]),
            callback_data=f"drive_select:{video['id']}"
        )]
        for video in page
    ]

    nav_row = []
    if offset > 0:
        nav_row.append(InlineKeyboardButton(
            "◀️ السابق",
            callback_data=f"drive_page:{max(0, offset - PAGE_SIZE)}"
        ))

    if offset + PAGE_SIZE < len(videos):
        nav_row.append(InlineKeyboardButton(
            "التالي ▶️",
            callback_data=f"drive_page:{offset + PAGE_SIZE}"
        ))

    if nav_row:
        keyboard.append(nav_row)

    return InlineKeyboardMarkup(keyboard)


# ----------------------------------------------------------------
# الخطوة ١: عرض قائمة فيديوهات Drive
# ----------------------------------------------------------------

async def show_drive_videos(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    clear_state(user_id)
    set_state(user_id, IDLE)

    await update.message.reply_text("⏳ جاري جلب الفيديوهات من Google Drive...")

    try:
        videos = await asyncio.to_thread(drive_utils.list_videos)
    except Exception as e:
        logger.exception(e)
        await update.message.reply_text("⚠️ تعذر الاتصال بـ Google Drive. حاول لاحقًا.")
        return

    if not videos:
        await update.message.reply_text("📂 لا توجد فيديوهات in مجلد Drive حاليًا.")
        return

    total = len(videos)
    header = "📂 اختر فيديو للرفع إلى يوتيوب:"

    if total > PAGE_SIZE:
        header += f"\n\n({total} فيديو، بحد {PAGE_SIZE} في كل صفحة)"

    await update.message.reply_text(
        header,
        reply_markup=_build_videos_keyboard(videos, offset=0),
    )


# ----------------------------------------------------------------
# التنقل بين صفحات القائمة
# ----------------------------------------------------------------

async def on_drive_page(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    offset = int(query.data.split(":", 1)[1])

    try:
        videos = await asyncio.to_thread(drive_utils.list_videos)
    except Exception as e:
        logger.exception(e)
        await query.edit_message_text("⚠️ تعذر الاتصال بـ Google Drive. حاول لاحقًا.")
        return

    if not videos:
        await query.edit_message_text("📂 لا توجد فيديوهات في مجلد Drive حاليًا.")
        return

    await query.edit_message_reply_markup(
        reply_markup=_build_videos_keyboard(videos, offset=offset)
    )


# ----------------------------------------------------------------
# الخطوة ٢: اختيار فيديو -> سؤال عن العنوان
# ----------------------------------------------------------------

async def on_drive_select(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    file_id = query.data.split(":", 1)[1]

    try:
        info = await asyncio.to_thread(drive_utils.get_video_info, file_id)
    except Exception as e:
        logger.exception(e)
        await query.edit_message_text("⚠️ تعذر جلب معلومات هذا الفيديو.")
        return

    set_state_data(
        user_id,
        {
            "drive_file_id": info["id"],
            "drive_file_name": info["name"],
            "drive_mime_type": info.get("mimeType", "video/*"),
        }
    )

    # 1️⃣ الطباعة المطلوبة الأولى: SELECT SAVE وما بعدها مباشرة
    print("SELECT SAVE:", {
        "drive_file_id": info["id"],
        "drive_file_name": info["name"],
    })
    print(get_state_data(user_id))

    current_title = _strip_extension(info["name"])

    keyboard = [
        [InlineKeyboardButton(
            f"✅ إبقاء العنوان الحالي ({current_title})",
            callback_data=f"drive_title:keep:{file_id}"
        )],
        [InlineKeyboardButton(
            "✏️ كتابة عنوان جديد",
            callback_data=f"drive_title:custom:{file_id}"
        )],
    ]

    await query.edit_message_text(
        f"🎬 الفيديو المختار: {info['name']}\n\n"
        "هل تريد إبقاء العنوان الحالي أم كتابة عنوان جديد؟",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ----------------------------------------------------------------
# الخطوة ٣: قرار العنوان (إبقاء / جديد)
# ----------------------------------------------------------------

async def on_drive_title_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    
    # 2️⃣ الطباعة المطلوبة الثانية: TITLE BEFORE في أول الدالة
    print("TITLE BEFORE:", get_state_data(user_id))

    parts = query.data.split(":")
    choice = parts[1]
    file_id = parts[2]

    data = get_state_data(user_id)

    if not data or not data.get("drive_file_id"):
        try:
            info = await asyncio.to_thread(drive_utils.get_video_info, file_id)
            data = {
                "drive_file_id": info["id"],
                "drive_file_name": info["name"],
                "drive_mime_type": info.get("mimeType", "video/*"),
            }
            set_state_data(user_id, data)
        except Exception as e:
            logger.exception(e)
            await query.edit_message_text("⚠️ انتهت صلاحية الطلب وتعذر استعادة معلومات الفيديو.")
            return

    if choice == "custom":
        set_state(user_id, WAITING_DRIVE_CUSTOM_TITLE)
        await query.edit_message_text("✏️ أرسل العنوان الجديد الآن كرسالة نصية.")
        return

    title = _strip_extension(data["drive_file_name"])
    data["title"] = title
    set_state_data(user_id, data)

    # 3️⃣ الطباعة المطلوبة الثالثة: TITLE AFTER بعد set_state_data
    print("TITLE AFTER:", get_state_data(user_id))

    await query.edit_message_text(f"✅ العنوان: {title}")
    await _ask_visibility(update, context)


async def handle_custom_title_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    title = update.message.text

    if not title:
        await update.message.reply_text("📝 أرسل عنوانًا نصيًا.")
        return

    data = get_state_data(user_id)

    if not data or not data.get("drive_file_id"):
        await update.message.reply_text(
            "⚠️ انتهت صلاحية هذا الطلب. ابدأ من جديد عبر زر Google Drive."
        )
        set_state(user_id, IDLE)
        return

    data["title"] = title
    set_state_data(user_id, data)
    set_state(user_id, IDLE)

    await update.message.reply_text(f"✅ العنوان: {title}")
    await _ask_visibility(update, context)


# ----------------------------------------------------------------
# الخطوة ٤: سؤال عن مستوى الخصوصية
# ----------------------------------------------------------------

async def _ask_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    data = get_state_data(user_id)
    file_id = data.get("drive_file_id", "")

    keyboard = [
        [InlineKeyboardButton(label, callback_data=f"drive_visibility:{value}:{file_id}")]
        for value, label in PRIVACY_LABELS.items()
    ]

    message = update.effective_message
    await message.reply_text(
        "🔐 اختر مستوى الخصوصية على يوتيوب:",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


# ----------------------------------------------------------------
# الخطوة ٥: الرفع الفعلي إلى يوتيوب ثم الحذف من Drive
# ----------------------------------------------------------------

async def on_drive_visibility(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user_id = update.effective_user.id
    
    # 4️⃣ الطباعة المطلوبة الرابعة: VISIBILITY في أول الدالة
    print("VISIBILITY:", get_state_data(user_id))

    parts = query.data.split(":")
    privacy_status = parts[1]
    file_id_from_callback = parts[2] if len(parts) > 2 else None

    data = get_state_data(user_id)
    file_id = file_id_from_callback or data.get("drive_file_id")
    
    if not file_id:
        await query.edit_message_text(
            "⚠️ انتهت صلاحية هذا الطلب. ابدأ من جديد عبر زر Google Drive."
        )
        return

    if not data or not data.get("drive_file_id"):
        try:
            info = await asyncio.to_thread(drive_utils.get_video_info, file_id)
            data = {
                "drive_file_id": info["id"],
                "drive_file_name": info["name"],
                "drive_mime_type": info.get("mimeType", "video/*"),
                "title": _strip_extension(info["name"])
            }
        except Exception:
            await query.edit_message_text("⚠️ تعذر الوصول للملف. ابدأ العملية من جديد.")
            return

    file_name = data.get("drive_file_name")
    mime_type = data.get("drive_mime_type", "video/*")
    title = data.get("title") or _strip_extension(file_name or "video")

    await query.edit_message_text(
        f"⏳ جاري رفع \"{title}\" إلى يوتيوب...\n"
        "قد يستغرق هذا بعض الوقت حسب حجم الفيديو."
    )

    user = get_user(user_id)

    if not user:
        await query.edit_message_text(
            "⚠️ يجب عليك بدء البوت أولاً باستخدام الأمر /start قبل الرفع."
        )
        return

    video_id = create_video(user["id"])

    update_video(
        video_id,
        filename=file_name,
        title=title,
        drive_file_id=file_id,
        status="uploading",
    )

    try:
        buffer = await asyncio.to_thread(drive_utils.download_video, file_id)

        youtube_video_id = await asyncio.to_thread(
            youtube_utils.upload_video,
            user_id,
            buffer,
            title,
            "",
            privacy_status,
            mime_type,
        )

    except Exception as e:
        logger.exception(e)
        update_video(video_id, status="failed")
        clear_state(user_id)

        error_text = str(e)
        auth_error_signals = [
            "unauthorized_client",
            "invalid_grant",
            "invalid_client",
            "Token has been expired or revoked",
            "لم يتم ربط حساب YouTube",
        ]

        if any(signal in error_text for signal in auth_error_signals):
            await query.message.reply_text(
                "❌ فشل رفع الفيديو لأن ربط حساب YouTube انتهت صلاحيته أو تم إلغاؤه.\n\n"
                "🔗 اضغط على زر \"ربط YouTube\" في القائمة الرئيسية لإعادة الربط، "
                "ثم أعد المحاولة.\n\n"
                "ℹ️ لم يتم حذف أي شيء من Drive."
            )
        else:
            await query.message.reply_text(
                "❌ فشل رفع الفيديو إلى يوتيوب. لم يتم حذف أي شيء من Drive.\n"
                f"تفاصيل الخطأ: {error_text}"
            )
        return

    update_video(
        video_id,
        youtube_video_id=youtube_video_id,
        status="uploaded",
        uploaded_at=datetime.now(timezone.utc).isoformat(),
    )

    await asyncio.to_thread(
        drive_utils.log_video_for_manual_deletion, file_id, file_name
    )
    drive_deleted = False

    clear_state(user_id)

    text = (
        "✅ تم رفع الفيديو بنجاح!\n\n"
        f"🔗 https://youtu.be/{youtube_video_id}\n\n"
        "📝 تم تسجيل اسم الملف في Drive ليتم حذفه يدوياً لاحقاً."
    )

    await query.message.reply_text(text)
