import logging
from pathlib import Path
import requests

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

TELEGRAM_API = "https://api.telegram.org/bot{token}/{method}"


def _api(method: str, **kwargs) -> dict | None:
    url = TELEGRAM_API.format(token=Config.TELEGRAM_BOT_TOKEN, method=method)
    try:
        resp = requests.post(url, timeout=30, **kwargs)
        data = resp.json()
        if not data.get("ok"):
            logger.error("Telegram API error [%s]: %s", method, data.get("description"))
            return None
        return data
    except Exception as e:
        logger.error("Telegram request error: %s", e)
        return None


def publish(product: dict, caption: str, image_path: Path) -> bool:
    full_caption = f"{caption}\n\n🔗 {product['affiliate_url']}"
    if len(full_caption) > 1024:
        full_caption = full_caption[:1020] + "..."

    with open(image_path, "rb") as photo:
        result = _api(
            "sendPhoto",
            data={
                "chat_id": Config.TELEGRAM_CHANNEL_ID,
                "caption": full_caption,
                "parse_mode": "HTML",
            },
            files={"photo": photo},
        )

    if result:
        logger.info("Telegram: posted product %s", product["product_id"])
        return True

    logger.warning("Telegram: retrying as message for product %s", product["product_id"])
    # Fallback: send without image
    result = _api(
        "sendMessage",
        json={
            "chat_id": Config.TELEGRAM_CHANNEL_ID,
            "text": full_caption,
            "parse_mode": "HTML",
            "disable_web_page_preview": False,
        },
    )
    return result is not None


def test_connection() -> bool:
    data = _api("getMe")
    if data:
        bot = data["result"]
        logger.info("Telegram connected: @%s", bot.get("username"))
        return True
    return False
