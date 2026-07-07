from google_auth_oauthlib.flow import Flow
from config import BASE_URL

SCOPES = [
    "https://www.googleapis.com/auth/youtube",
    "https://www.googleapis.com/auth/youtube.upload"
]


def build_flow():
    return Flow.from_client_secrets_file(
        "client_secret.json",
        scopes=SCOPES,
        redirect_uri=f"{BASE_URL}/oauth2callback",
    )
