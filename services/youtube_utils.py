import logging
from database.oauth_tokens import get_token, save_token
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
from googleapiclient.errors import HttpError

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)

logger = logging.getLogger(__name__)

VALID_PRIVACY_STATUSES = ("private", "unlisted", "public")


def get_youtube_service(user_id):
    """يجلب توكن المستخدم من قاعدة البيانات، يجدده إذا لزم الأمر، ويعيد كائن الخدمة."""
    token = get_token(user_id)

    if token is None:
        raise Exception("لم يتم ربط حساب YouTube.")

    creds = Credentials(
        token=token["access_token"],
        refresh_token=token["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )

    # تجديد التوكن فقط إذا كان منتهياً أو غير صالح
    if not creds.valid:
        if creds.expired and creds.refresh_token:
            try:
                creds.refresh(Request())
                # حفظ التوكن الجديد المستقر في قاعدة البيانات
                save_token(
                    user_id=user_id,
                    access_token=creds.token,
                    refresh_token=creds.refresh_token or token["refresh_token"],
                    expires_at=str(creds.expiry),
                )
                logger.info(f"تم تجديد التوكن بنجاح للمستخدم {user_id}")
            except Exception as e:
                logger.error(f"فشل تجديد التوكن للمستخدم {user_id}: {e}")
                raise Exception("انتهت صلاحية الجلسة، يرجى إعادة تسجيل الدخول.")
        else:
            raise Exception("التوكن غير صالح ولا يمكن تجديده تلقائياً.")

    return build("youtube", "v3", credentials=creds)


def upload_video(
    user_id,
    file_stream,
    title,
    description,
    privacy_status,
    mime_type="video/*",
):
    """يرفع فيديو إلى يوتيوب ويعيد youtube_video_id عند النجاح."""

    if privacy_status not in VALID_PRIVACY_STATUSES:
        privacy_status = "private"

    try:
        service = get_youtube_service(user_id)
    except Exception as e:
        logger.error(f"خطأ في الحصول على صلاحيات يوتيوب للمستخدم {user_id}: {e}")
        raise

    body = {
        "snippet": {
            "title": title or "بدون عنوان",
            "description": description or "",
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    # تقسيم الملف إلى أجزاء بحجم 5 ميجابايت لضمان استقرار الرفع ومعرفة النسبة المئوية
    media = MediaIoBaseUpload(
        file_stream,
        mimetype=mime_type,
        chunksize=1024 * 1024 * 5,
        resumable=True,
    )

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None

    try:
        logger.info(f"بدء رفع الفيديو للمستخدم {user_id}...")
        while response is None:
            status, response = request.next_chunk()
            if status:
                logger.info(f"المستخدم {user_id}: تم رفع {int(status.progress() * 100)}%...")
        
        logger.info(f"تم رفع الفيديو بنجاح للمستخدم {user_id}. معرف الفيديو: {response['id']}")
        return response["id"]

    except HttpError as e:
        logger.error(
                    "YouTube HTTP Error: %s",
                    e
                )
        raise Exception(f"فشل رفع الفيديو بسبب خطأ في سيرفر يوتيوب: {e}")
    except Exception as e:
        logger.error(f"خطأ غير متوقع أثناء الرفع للمستخدم {user_id}: {e}")
        raise Exception(f"فشل رفع الفيديو: {e}")


def test_youtube_connection(user_id):
    """تختبر الاتصال بحساب يوتيوب وتجلب اسم القناة للتحقق من صحة التوكن."""
    try:
        service = get_youtube_service(user_id)

        # طلب جلب القناة الخاصة بالتوكن الحالي
        request = service.channels().list(
            part="snippet",
            mine=True
        )
        response = request.execute()

        if response.get("items"):
            channel_title = response["items"][0]["snippet"]["title"]
            return True, channel_title
        
        return False, "تم الاتصال، ولكن لم يتم العثور على قناة YouTube مفعّلة في هذا الحساب."

    except Exception as e:
        logger.error(f"فشل اختبار الاتصال للمستخدم {user_id}: {e}")
        return False, str(e)