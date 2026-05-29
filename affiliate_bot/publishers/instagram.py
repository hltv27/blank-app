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
    from instagrapi.exceptions import LoginRequired, BadPassword, TwoFactorRequired

    cl = Client()
    cl.delay_range = [2, 5]

    if _SESSION.exists():
        try:
            cl.load_settings(_SESSION)
            cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
            logger.info("Instagram: resumed cached session @%s", Config.INSTAGRAM_USERNAME)
            _client = cl
            return _client
        except (LoginRequired, BadPassword):
            logger.warning("Instagram: cached session expired, logging in fresh")
        except Exception as e:
            logger.warning("Instagram: session load error: %s", e)

    cl = Client()
    cl.delay_range = [2, 5]
    cl.login(Config.INSTAGRAM_USERNAME, Config.INSTAGRAM_PASSWORD)
    cl.dump_settings(_SESSION)
    logger.info("Instagram: fresh login @%s", Config.INSTAGRAM_USERNAME)
    _client = cl
    return _client


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
