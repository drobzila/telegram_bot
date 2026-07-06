import io
import logging

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

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


def list_videos():
    """يعيد قائمة بملفات الفيديو الموجودة داخل مجلد Drive المحدد."""

    service = get_drive_service()

    query = (
        f"'{DRIVE_FOLDER_ID}' in parents "
        "and trashed=false "
        "and mimeType contains 'video/'"
    )

    files = []
    page_token = None

    while True:
        response = service.files().list(
            q=query,
            fields="nextPageToken, files(id, name, mimeType, size)",
            pageToken=page_token,
        ).execute()

        files.extend(response.get("files", []))

        page_token = response.get("nextPageToken")

        if not page_token:
            break

    return files


def get_video_info(file_id):
    """يعيد معلومات ملف فيديو واحد (الاسم، النوع)."""

    service = get_drive_service()

    return service.files().get(
        fileId=file_id,
        fields="id, name, mimeType, size",
    ).execute()


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


def delete_video(file_id):
    """يحذف ملف فيديو من Drive نهائيًا."""

    service = get_drive_service()
    service.files().delete(fileId=file_id).execute()
