from googleapiclient.http import MediaFileUpload

from services.youtube_service import get_youtube_service


def upload_video(
    user_id,
    video_path,
    title,
    description="",
    privacy="private",
):
    youtube = get_youtube_service(user_id)

    if youtube is None:
        raise Exception("YouTube غير مربوط.")

    body = {
        "snippet": {
            "title": title,
            "description": description,
        },
        "status": {
            "privacyStatus": privacy,
        },
    }

    media = MediaFileUpload(
        video_path,
        chunksize=-1,
        resumable=True,
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media,
    )

    response = None

    while response is None:
        _, response = request.next_chunk()

    return response["id"]
