import os
import json
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

BASE_DIR = Path(__file__).parent.parent

class Config:
    # AliExpress (via RapidAPI DataHub)
    RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY", "")
    ALIEXPRESS_TRACKING_ID = os.getenv("ALIEXPRESS_TRACKING_ID", "")

    # Amazon
    AMAZON_ACCESS_KEY = os.getenv("AMAZON_ACCESS_KEY", "")
    AMAZON_SECRET_KEY = os.getenv("AMAZON_SECRET_KEY", "")
    AMAZON_PARTNER_TAG = os.getenv("AMAZON_PARTNER_TAG", "")
    AMAZON_REGION = os.getenv("AMAZON_REGION", "ES")

    # Telegram
    TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
    TELEGRAM_CHANNEL_ID = os.getenv("TELEGRAM_CHANNEL_ID", "")

    # Instagram (instagrapi — login direto com user+password)
    INSTAGRAM_USERNAME = os.getenv("INSTAGRAM_USERNAME", "")
    INSTAGRAM_PASSWORD = os.getenv("INSTAGRAM_PASSWORD", "")

    # TikTok
    TIKTOK_CLIENT_KEY = os.getenv("TIKTOK_CLIENT_KEY", "")
    TIKTOK_CLIENT_SECRET = os.getenv("TIKTOK_CLIENT_SECRET", "")
    TIKTOK_ACCESS_TOKEN = os.getenv("TIKTOK_ACCESS_TOKEN", "")

    # Anthropic
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

    # General
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    DB_PATH = BASE_DIR / os.getenv("DB_PATH", "affiliate_bot.db")
    IMAGES_DIR = BASE_DIR / os.getenv("IMAGES_DIR", "generated_images")

    @classmethod
    def load_niches(cls) -> dict:
        niche_file = BASE_DIR / "affiliate_bot" / "niches" / "config.json"
        with open(niche_file) as f:
            return json.load(f)

    @classmethod
    def validate(cls) -> list[str]:
        # Only these two are required to start — everything else is optional
        missing = []
        required = {
            "RAPIDAPI_KEY": cls.RAPIDAPI_KEY,
            "TELEGRAM_BOT_TOKEN": cls.TELEGRAM_BOT_TOKEN,
            "TELEGRAM_CHANNEL_ID": cls.TELEGRAM_CHANNEL_ID,
        }
        for name, value in required.items():
            if not value:
                missing.append(name)
        return missing
