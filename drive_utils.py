import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import (
    DRIVE_FOLDER_ID,
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
    GOOGLE_REFRESH_TOKEN,
)

logger = logging.getLogger(__name__)


def get_drive_service():
    """ينشئ اتصالًا مع Google Drive API باستخدام refresh token."""

    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
    )

    creds.refresh(Request())

    return build("drive", "v3", credentials=creds)


def test_connection():
    """يتحقق من إمكانية الاتصال بـ Google Drive."""

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
            fields="nextPageToken, files(id)",
            pageToken=page_token,
        ).execute()

        files.extend(response.get("files", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return len(files)
