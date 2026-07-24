"""
config.py
Central configuration for the watchlist system.
Edit values here instead of touching enroll.py / main.py / evaluate.py.
"""

# --- Matching ---
SIMILARITY_THRESHOLD = 0.5
ALERT_COOLDOWN = 30

# --- Camera ---
CAMERA_INDEX = 0
DET_SIZE = (640, 640)

# --- Paths ---
WANTED_PHOTOS_DIR = "wanted_photos"
VILLAGE_PHOTOS_DIR = "village_photos"
DB_PATH = "watchlist.pkl"
ALERTS_DIR = "alerts"

# --- Telegram alerts (optional) ---
# 1. Message @BotFather on Telegram -> /newbot -> copy the token below
# 2. Message @userinfobot -> it replies with your chat id -> paste below
# 3. Set ENABLE_TELEGRAM = True
ENABLE_TELEGRAM = True
TELEGRAM_BOT_TOKEN = "8723686755:AAEP8f-bDrlmKUIVRnUPOEVm_UUvglkku7o"   # paste your real token
TELEGRAM_CHAT_ID = "1829902955"

# --- Email alerts (optional) ---
# Use an app password (not your real password) if using Gmail:
# https://myaccount.google.com/apppasswords
ENABLE_EMAIL = False
EMAIL_FROM = ""
EMAIL_TO = ""
EMAIL_APP_PASSWORD = ""
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587