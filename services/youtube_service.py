from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

from config import (
    GOOGLE_CLIENT_ID,
    GOOGLE_CLIENT_SECRET,
)

from database.oauth_tokens import get_token


SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload"
]


def get_youtube_service(user_id):

    token = get_token(user_id)

    if token is None:
        return None

    credentials = Credentials(
        token=token["access_token"],
        refresh_token=token["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=GOOGLE_CLIENT_ID,
        client_secret=GOOGLE_CLIENT_SECRET,
        scopes=SCOPES,
    )

    # التحقق من انتهاء الصلاحية وتجديد التوكن تلقائيًا وحفظه
    if credentials.expired and credentials.refresh_token:
        credentials.refresh(Request())

        # استيراد وحفظ التوكن الجديد لتجنب انتهاء الجلسة مستقبلاً
        from database.oauth_tokens import save_token

        save_token(
            telegram_id,
            credentials.token,
            credentials.refresh_token,
            str(credentials.expiry),
        )

    return build(
        "youtube",
        "v3",
        credentials=credentials,
    )
