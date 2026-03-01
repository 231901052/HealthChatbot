import os
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./dev.db")
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
TWILIO_NUMBER = os.getenv("TWILIO_NUMBER", "")
GEMINI_API = os.getenv("GEMINI_API", "")
TWILIO_WHATSAPP = os.getenv("TWILIO_WHATSAPP", "")
ASHA_ESC_URL = os.getenv("ASHA_ESC_URL", "")
ASHA_API_KEY = os.getenv("ASHA_API_KEY", "")
REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")
RASA_URL = os.getenv("RASA_URL", "http://rasa:5005")
