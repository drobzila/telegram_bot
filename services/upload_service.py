from database.users import get_user
from database.videos import (
    create_video,
    update_video,
)
from database.states import (
    set_state,
    set_state_data,
)

from states.state_names import WAITING_TITLE


class UploadService:

    @staticmethod
    def receive_video(telegram_user_id, telegram_video):

        user = get_user(telegram_user_id)

        video_id = create_video(user["id"])

        update_video(
            video_id,
            filename="telegram_video",
            telegram_file_id=telegram_video.file_id,
            status="waiting_title"
        )

        set_state_data(
            telegram_user_id,
            {
                "video_id": video_id,
                "telegram_file_id": telegram_video.file_id,
                "duration": telegram_video.duration,
                "width": telegram_video.width,
                "height": telegram_video.height,
                "file_size": telegram_video.file_size,
            }
        )

        set_state(
            telegram_user_id,
            WAITING_TITLE
        )

        return video_id
