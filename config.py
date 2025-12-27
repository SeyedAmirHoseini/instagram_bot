from pathlib import Path
from dotenv import load_dotenv
import os

load_dotenv()

USERNAME = os.getenv("INSTA_USERNAME")
PASSWORD = os.getenv("INSTA_PASSWORD")

ADMIN_ID = int(os.getenv("ADMIN_ID", "0"))

TELEGRAM_BOT_USERNAME = "MoviesssBot_bot"

SESSION_FILE = Path("session.json")
DB_NAME = "bot_data.db"

# تأخیرها - محتاطانه‌تر
DELAY_RANGE_REQUESTS = [3, 8]
DELAY_RANGE_DM = [10, 25]
DELAY_RANGE_COMMENTS = [40, 90]

CHECK_INTERVAL_COMMENTS = 420  # ۷ دقیقه
POSTS_TO_CHECK = 5

DM_TEMPLATES = [
    "این هم لینک دانلود {category} {name} که خواستی: {link} 🎬",
    "سلام عزیزم، لینک {name} برات اومد: {link} 🫶",
    "بفرما، لینک {category} {name}: {link}",
]

REPLY_TEMPLATES = [
    "لینک دایرکت شد جانم، چک کن 🥰",
    "ارسال شد، برو دایرکت ببین 🌸",
    "چک کن دایرکت، فرستادم ✅",
]