from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from config import GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, GOOGLE_REFRESH_TOKEN, DRIVE_FOLDER_ID

SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]


def _get_credentials():
    """
    يبني Credentials من refresh token دائم بدل تسجيل دخول تفاعلي في كل مرة.
    مكتبة google-auth تجدد access token تلقائياً عند الحاجة.
    """
    if not (GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET and GOOGLE_REFRESH_TOKEN):
        raise ValueError(
            "❌ بيانات OAuth ناقصة. تأكد من تعيين "
            "GOOGLE_CLIENT_ID و GOOGLE_CLIENT_SECRET و GOOGLE_REFRESH_TOKEN.\n"
            "شغّل get_token.py محلياً للحصول عليها أول مرة."
        )

    creds = Credentials(
        token=None,
        refresh_token=GOOGLE_REFRESH_TOKEN,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        # لا نمرر scopes هنا عمداً: عند تجديد access token عبر refresh_token
        # لا حاجة لإرسال scope، وإرساله قد يسبب خطأ invalid_scope إن لم يطابق
        # حرفياً ما مُنح أثناء التصريح الأول.
    )
    creds.refresh(Request())
    return creds


def get_drive_service():
    creds = _get_credentials()
    return build("drive", "v3", credentials=creds)


def test_connection() -> bool:
    try:
        service = get_drive_service()
        service.files().list(pageSize=1).execute()
        return True
    except Exception as e:
        print(f"⚠️ خطأ في الاتصال بـ Google Drive: {e}")
        return False


def count_videos(folder_id: str = None) -> int:
    folder_id = folder_id or DRIVE_FOLDER_ID
    service = get_drive_service()
    query = f"'{folder_id}' in parents and mimeType contains 'video/' and trashed = false"

    count = 0
    page_token = None
    while True:
        response = (
            service.files()
            .list(
                q=query,
                fields="nextPageToken, files(id, name)",
                pageToken=page_token,
                pageSize=1000,
            )
            .execute()
        )
        count += len(response.get("files", []))
        page_token = response.get("nextPageToken")
        if not page_token:
            break
    return count
