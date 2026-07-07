from datetime import datetime
import io
import json
import logging
import os

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

from config import DRIVE_FOLDER_ID

logger = logging.getLogger(__name__)

SCOPES = ["https://www.googleapis.com/auth/drive"]

# كاش لحفظ كائن الخدمة وتجنب إعادة بناء الاتصال في كل طلب
_DRIVE_SERVICE_CACHE = None


def _load_service_account_credentials():
    """يحمّل بيانات حساب الخدمة من متغير البيئة GOOGLE_SERVICE_ACCOUNT_JSON
    (يحتوي على محتوى ملف الـ JSON كاملاً كنص) — وهذا هو الأسلوب المستخدم على Render.
    إذا لم يكن المتغير موجوداً، يتم الرجوع لمسار ملف محلي عبر GOOGLE_SERVICE_ACCOUNT_FILE
    (مفيد للتطوير المحلي فقط)."""
    raw_json = os.getenv("GOOGLE_SERVICE_ACCOUNT_JSON")

    if raw_json:
        info = json.loads(raw_json)
        return service_account.Credentials.from_service_account_info(
            info, scopes=SCOPES
        )

    local_path = os.getenv("GOOGLE_SERVICE_ACCOUNT_FILE")
    if local_path:
        return service_account.Credentials.from_service_account_file(
            local_path, scopes=SCOPES
        )

    raise RuntimeError(
        "لم يتم العثور على بيانات حساب خدمة Google. "
        "الرجاء تعيين متغير البيئة GOOGLE_SERVICE_ACCOUNT_JSON."
    )


def get_drive_service():
    """ينشئ أو يعيد اتصالًا مستقرًا مع Google Drive API باستخدام Service Account."""
    global _DRIVE_SERVICE_CACHE

    if _DRIVE_SERVICE_CACHE is None:
        credentials = _load_service_account_credentials()
        _DRIVE_SERVICE_CACHE = build("drive", "v3", credentials=credentials)

    return _DRIVE_SERVICE_CACHE


def test_connection():
    """يتحقق من إمكانية الاتصال بـ Google Drive باستخدام حساب الخدمة."""
    try:
        service = get_drive_service()
        service.about().get(fields="user").execute()
        return True
    except Exception as e:
        logger.exception(e)
        return False


def count_videos():
    """يعيد عدد الملفات الموجودة داخل مجلد Drive المحدد."""
    service = get_drive_service()
    query = f"'{DRIVE_FOLDER_ID}' in parents and trashed=false"

    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken,files(id)",
            pageToken=page_token,
        ).execute()

        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return len(files)


def list_videos():
    """يعيد قائمة بملفات الفيديو مرتبة من الأحدث إلى الأقدم مع تاريخ منسق وجاهز."""
    service = get_drive_service()
    query = (
        f"'{DRIVE_FOLDER_ID}' in parents "
        "and trashed=false "
        "and mimeType contains 'video/'"
    )

    files = []
    page_token = None

    # تم التعديل هنا: دمج الحقول في سطر واحد بدون مسافات أو أسطر جديدة
    FIELDS = "nextPageToken,files(id,name,mimeType,size,createdTime)"

    while True:
        response = service.files().list(
            q=query,
            orderBy="createdTime desc",
            fields=FIELDS,
            pageToken=page_token,
        ).execute()

        files.extend(response.get("files", []))
        page_token = response.get("nextPageToken")

        if not page_token:
            break

    # إضافة حقل التاريخ المنسق بشكل جميل لكل ملف فيديو داخل القائمة
    for file in files:
        if "createdTime" in file:
            dt = datetime.fromisoformat(
                file["createdTime"].replace("Z", "+00:00")
            )
            file["created"] = dt.strftime("%Y-%m-%d")

    return files


def get_video_info(file_id):
    """يعيد معلومات ملف فيديو واحد مع حقل التاريخ المنسق."""
    service = get_drive_service()
    
    # تم التعديل هنا: دمج الحقول لمنع أخطاء Google API
    info = service.files().get(
        fileId=file_id,
        fields="id,name,mimeType,size,createdTime",
    ).execute()

    # تنسيق التاريخ للملف المفرد أيضاً لتوحيد التجربة
    if "createdTime" in info:
        dt = datetime.fromisoformat(
            info["createdTime"].replace("Z", "+00:00")
        )
        info["created"] = dt.strftime("%Y-%m-%d")

    return info


def download_video(file_id):
    """يحمّل ملف فيديو من Drive ويعيده كـ BytesIO."""
    service = get_drive_service()
    request = service.files().get_media(fileId=file_id)

    buffer = io.BytesIO()
    downloader = MediaIoBaseDownload(buffer, request)

    done = False
    while not done:
        _, done = downloader.next_chunk()

    buffer.seek(0)
    return buffer


def log_video_for_manual_deletion(file_id, file_name):
    """يسجل اسم ومعرّف الفيديو في قاعدة البيانات ليتم حذفه يدوياً لاحقاً من Drive،
    بدلاً من محاولة حذفه تلقائياً عبر الـ API (والتي قد تفشل بسبب الصلاحيات).
    التخزين في قاعدة البيانات يضمن بقاء السجل حتى بعد إعادة النشر على Render."""
    from database.pending_deletions import add_pending_deletion

    add_pending_deletion(file_id, file_name)
    logger.info(f"تم تسجيل الفيديو للحذف اليدوي لاحقاً: {file_name} ({file_id})")


def delete_video(file_id):
    service = get_drive_service()

    try:
        # التأكد من وجود الملف
        info = service.files().get(
            fileId=file_id,
            fields="id,name,trashed"
        ).execute()

        logger.info(f"قبل الحذف: {info}")

        # محاولة الحذف النهائي أولاً
        try:
            service.files().delete(
                fileId=file_id,
                supportsAllDrives=True
            ).execute()
        except Exception as delete_error:
            # إذا فشل الحذف النهائي بسبب صلاحيات غير كافية،
            # نحاول كحل بديل نقل الملف إلى سلة المهملات فقط
            logger.warning(
                f"فشل الحذف النهائي للملف {file_id}، "
                f"سيتم تجربة النقل لسلة المهملات: {delete_error}"
            )
            service.files().update(
                fileId=file_id,
                body={"trashed": True},
                supportsAllDrives=True
            ).execute()
            logger.info(f"تم نقل الملف {file_id} إلى سلة المهملات بنجاح")
            return True

        # التأكد بعد الحذف
        try:
            service.files().get(
                fileId=file_id,
                fields="id,name"
            ).execute()

            logger.error("الملف مازال موجوداً بعد الحذف!")
            return False

        except Exception:
            logger.info("تم حذف الملف فعلاً")
            return True

    except Exception as e:
        logger.exception(f"فشل حذف الملف {file_id}: {e}")
        return False


# ---------- دوال مساعدة إضافية ----------

def format_size(size):
    """يحول حجم الملف بالبايت إلى صيغة مقروءة للبشر (KB, MB, GB)."""
    size = int(size)
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0

    while size >= 1024 and i < len(units) - 1:
        size /= 1024
        i += 1

    if i == 0:
        return f"{int(size)} {units[i]}"

    return f"{size:.1f} {units[i]}"


def format_date(created_time):
    """دالة احتياطية لتحويل صيغة تاريخ ISO يدوياً عند الحاجة خارج القوائم."""
    dt = datetime.fromisoformat(
        created_time.replace("Z", "+00:00")
    )
    return dt.strftime("%Y-%m-%d")
