import logging
import time

from database.oauth_tokens import get_token, save_token
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from googleapiclient.http import MediaIoBaseUpload

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

logger = logging.getLogger(__name__)

VALID_PRIVACY_STATUSES = ("private", "unlisted", "public")
UPLOAD_RETRIES = 3


def get_youtube_service(telegram_id):
    """Get a user's YouTube API service and refresh its OAuth token when needed."""
    token = get_token(telegram_id)

    if token is None:
        raise RuntimeError("لم يتم ربط حساب YouTube.")

    if not token.get("access_token"):
        raise RuntimeError("توكن YouTube غير صالح. يرجى إعادة تسجيل الدخول.")

    creds = Credentials(
        token=token["access_token"],
        refresh_token=token.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )

    if not creds.valid:
        if not creds.expired or not creds.refresh_token:
            raise RuntimeError("انتهت صلاحية جلسة YouTube. يرجى إعادة تسجيل الدخول.")
        try:
            creds.refresh(Request())
            save_token(
                telegram_id=telegram_id,
                access_token=creds.token,
                refresh_token=creds.refresh_token or token.get("refresh_token"),
                expires_at=str(creds.expiry) if creds.expiry else None,
            )
            logger.info("YouTube token refreshed for user %s", telegram_id)
        except Exception as exc:
            logger.exception("Failed to refresh YouTube token for user %s", telegram_id)
            raise RuntimeError("انتهت صلاحية جلسة YouTube، يرجى إعادة تسجيل الدخول.") from exc

    return build("youtube", "v3", credentials=creds)


def upload_video(
    telegram_id,
    file_stream,
    title,
    description,
    privacy_status,
    mime_type="video/mp4",
):
    """Upload a video to YouTube using a resumable upload."""
    if privacy_status not in VALID_PRIVACY_STATUSES:
        privacy_status = "private"

    service = get_youtube_service(telegram_id)

    body = {
        "snippet": {
            "title": (title or "بدون عنوان")[:100],
            "description": description or "",
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    media = MediaIoBaseUpload(
        file_stream,
        mimetype=mime_type,
        chunksize=5 * 1024 * 1024,
        resumable=True,
    )

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None
    retry_count = 0

    try:
        logger.info("Starting YouTube upload for user %s", telegram_id)
        while response is None:
            try:
                status, response = request.next_chunk()
                retry_count = 0
                if status:
                    logger.info(
                        "User %s: upload progress %d%%",
                        telegram_id,
                        int(status.progress() * 100),
                    )
            except HttpError as exc:
                if retry_count >= UPLOAD_RETRIES:
                    raise
                retry_count += 1
                delay = 2 ** retry_count
                logger.warning(
                    "Transient YouTube upload error for user %s; retry %d/%d in %ss: %s",
                    telegram_id,
                    retry_count,
                    UPLOAD_RETRIES,
                    delay,
                    exc,
                )
                time.sleep(delay)
            except (OSError, TimeoutError) as exc:
                if retry_count >= UPLOAD_RETRIES:
                    raise
                retry_count += 1
                delay = 2 ** retry_count
                logger.warning(
                    "Transient upload I/O error for user %s; retry %d/%d in %ss: %s",
                    telegram_id,
                    retry_count,
                    UPLOAD_RETRIES,
                    delay,
                    exc,
                )
                time.sleep(delay)

        video_id = response.get("id")
        if not video_id:
            raise RuntimeError("لم يعُد YouTube بمعرّف للفيديو بعد الرفع.")

        logger.info("YouTube upload completed for user %s: %s", telegram_id, video_id)
        return video_id

    except HttpError as exc:
        logger.error("YouTube HTTP error for user %s: %s", telegram_id, exc)
        raise RuntimeError("فشل رفع الفيديو إلى YouTube. تحقق من الصلاحيات وحالة القناة.") from exc
    except Exception as exc:
        logger.exception("Unexpected YouTube upload error for user %s", telegram_id)
        raise RuntimeError("فشل رفع الفيديو إلى YouTube.") from exc


def test_youtube_connection(telegram_id):
    """Validate the OAuth token and return the connected channel name."""
    try:
        service = get_youtube_service(telegram_id)
        response = service.channels().list(part="snippet", mine=True).execute()

        items = response.get("items") or []
        if items:
            return True, items[0]["snippet"]["title"]

        return False, "تم الاتصال، ولكن لم يتم العثور على قناة YouTube في هذا الحساب."

    except Exception as exc:
        logger.exception("YouTube connection test failed for user %s", telegram_id)
        return False, "تعذر التحقق من قناة YouTube."
