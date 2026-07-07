from services.youtube_upload import upload_video

video_id = upload_video(
    user_id=5749748972,
    video_path="services/test.mp4",
    title="اختبار من البوت",
    description="أول فيديو مرفوع بواسطة البوت",
    privacy="private",
)

print("Video ID:", video_id)
print("https://youtu.be/" + video_id)
