from pathlib import Path

from google_auth_oauthlib.flow import Flow

from config import BASE_URL

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]

CLIENT_SECRET_FILE = Path(__file__).resolve().parent.parent / "client_secret.json"


def build_flow(state=None):
    if not BASE_URL:
        raise RuntimeError("BASE_URL غير مضبوط.")
    if not CLIENT_SECRET_FILE.exists():
        raise RuntimeError("ملف client_secret.json غير موجود.")

    return Flow.from_client_secrets_file(
        str(CLIENT_SECRET_FILE),
        scopes=SCOPES,
        state=state,
        redirect_uri=f"{BASE_URL.rstrip('/')}/oauth2callback",
    )
