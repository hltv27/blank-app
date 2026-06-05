import logging
from pathlib import Path

from affiliate_bot.config import Config, BASE_DIR

logger = logging.getLogger(__name__)

_client = None
_SESSION = BASE_DIR / "instagram_session.json"


def _get_client():
    global _client
    if _client is not None:
        return _client

    from instagrapi import Client

    cl = Client()
    cl.delay_range = [2, 5]

    if _SESSION.exists():
        cl.load_settings(_SESSION)
        logger.info("Instagram: loaded session from file")
        _client = cl
        return _client

    raise RuntimeError(
        f"Instagram session file not found: {_SESSION}. "
        "Run the login script on a PC to generate it."
    )


def publish(product: dict, caption: str, image_path: str) -> bool:
    full_caption = f"{caption}\n\n🔗 {product['affiliate_url']}"[:2200]

    try:
        cl = _get_client()
        media = cl.photo_upload(path=image_path, caption=full_caption)
        logger.info("Instagram: posted %s for product %s", media.pk, product["product_id"])
        return True
    except Exception as e:
        global _client
        _client = None
        logger.error("Instagram publish error: %s", e)
        return False


def test_connection() -> bool:
    try:
        cl = _get_client()
        info = cl.account_info()
        logger.info("Instagram connected: @%s", info.username)
        return True
    except Exception as e:
        logger.error("Instagram connection test failed: %s", e)
        return False
