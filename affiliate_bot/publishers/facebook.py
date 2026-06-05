import logging
import requests

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.facebook.com/v19.0"


def publish(product: dict, caption: str, image_path: str) -> bool:
    page_id = Config.FACEBOOK_PAGE_ID
    token = Config.FACEBOOK_PAGE_TOKEN

    if not page_id or not token:
        logger.warning("Facebook: PAGE_ID or PAGE_TOKEN not set")
        return False

    full_caption = f"{caption}\n\n🔗 {product['affiliate_url']}"[:63206]

    try:
        with open(image_path, "rb") as f:
            resp = requests.post(
                f"{GRAPH_BASE}/{page_id}/photos",
                params={"access_token": token},
                data={"caption": full_caption},
                files={"source": f},
                timeout=30,
            )
        resp.raise_for_status()
        data = resp.json()
        logger.info("Facebook: posted photo id=%s", data.get("id"))
        return True
    except Exception as e:
        logger.error("Facebook publish error: %s", e)
        return False


def test_connection() -> bool:
    try:
        resp = requests.get(
            f"{GRAPH_BASE}/{Config.FACEBOOK_PAGE_ID}",
            params={"access_token": Config.FACEBOOK_PAGE_TOKEN, "fields": "name,id"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        logger.info("Facebook connected: %s (%s)", data.get("name"), data.get("id"))
        return True
    except Exception as e:
        logger.error("Facebook connection test failed: %s", e)
        return False
