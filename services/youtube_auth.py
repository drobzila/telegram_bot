from google_auth_oauthlib.flow import Flow

from config import BASE_URL, GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload",
]


def build_flow(state=None):
    if not BASE_URL:
        raise RuntimeError("BASE_URL غير مضبوط.")
    if not GOOGLE_CLIENT_ID or not GOOGLE_CLIENT_SECRET:
        raise RuntimeError(
            "يجب ضبط GOOGLE_CLIENT_ID و GOOGLE_CLIENT_SECRET في متغيرات البيئة."
        )

    redirect_uri = f"{BASE_URL.rstrip('/')}/oauth2callback"
    client_config = {
        "web": {
            "client_id": GOOGLE_CLIENT_ID,
            "client_secret": GOOGLE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [redirect_uri],
        }
    }
    return Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        state=state,
        redirect_uri=redirect_uri,
    )
