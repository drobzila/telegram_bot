import os
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
DRIVE_FOLDER_ID = os.getenv("DRIVE_FOLDER_ID")

# بيانات تطبيق OAuth (من Google Cloud Console > Credentials > OAuth client ID > Desktop app)
GOOGLE_CLIENT_ID = os.getenv("GOOGLE_CLIENT_ID")
GOOGLE_CLIENT_SECRET = os.getenv("GOOGLE_CLIENT_SECRET")
# يُنتَج مرة واحدة محلياً عبر get_token.py، ثم يوضع كمتغير بيئة دائم
GOOGLE_REFRESH_TOKEN = os.getenv("GOOGLE_REFRESH_TOKEN")

# Render يوفر هذا المتغير تلقائياً؛ محلياً سيأخذ القيمة الافتراضية 10000
PORT = int(os.getenv("PORT", 10000))

if not BOT_TOKEN:
    raise ValueError("❌ لم يتم تعيين BOT_TOKEN في ملف .env")

if not DRIVE_FOLDER_ID:
    raise ValueError("❌ لم يتم تعيين DRIVE_FOLDER_ID في ملف .env")
