import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
)

logger = logging.getLogger(__name__)

VALID_PRIVACY_STATUSES = ("private", "unlisted", "public")


def get_youtube_service():
    """ينشئ اتصالًا مع YouTube Data API باستخدام نفس refresh token.

    ملاحظة: يجب أن يكون الـ refresh token صادرًا بصلاحية
    https://www.googleapis.com/auth/youtube.upload
    وإلا سيفشل الرفع برسالة insufficientPermissions.
    """

    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )

    creds.refresh(Request())

    return build("youtube", "v3", credentials=creds)


def upload_video(file_stream, title, description, privacy_status, mime_type="video/*"):
    """يرفع فيديو إلى يوتيوب ويعيد youtube_video_id عند النجاح."""

    if privacy_status not in VALID_PRIVACY_STATUSES:
        privacy_status = "private"

    service = get_youtube_service()

    body = {
        "snippet": {
            "title": title or "بدون عنوان",
            "description": description or "",
        },
        "status": {
            "privacyStatus": privacy_status,
        },
    }

    media = MediaIoBaseUpload(
        file_stream,
        mimetype=mime_type,
        chunksize=-1,
        resumable=True,
    )

    request = service.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None

    while response is None:
        status, response = request.next_chunk()

    return response["id"]
