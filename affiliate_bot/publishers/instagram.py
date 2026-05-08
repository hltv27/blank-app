import logging
import requests

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

GRAPH_API = "https://graph.facebook.com/v19.0"


def _post(endpoint: str, **kwargs) -> dict | None:
    url = f"{GRAPH_API}/{endpoint}"
    try:
        resp = requests.post(url, timeout=60, **kwargs)
        data = resp.json()
        if "error" in data:
            logger.error("Instagram API error: %s", data["error"].get("message"))
            return None
        return data
    except Exception as e:
        logger.error("Instagram request error: %s", e)
        return None


def _get(endpoint: str, params: dict) -> dict | None:
    url = f"{GRAPH_API}/{endpoint}"
    try:
        resp = requests.get(url, params=params, timeout=30)
        data = resp.json()
        if "error" in data:
            logger.error("Instagram GET error: %s", data["error"].get("message"))
            return None
        return data
    except Exception as e:
        logger.error("Instagram GET request error: %s", e)
        return None


def publish(product: dict, caption: str, image_url: str) -> bool:
    """
    Instagram Graph API two-step publish:
    1. Create media container
    2. Publish container
    """
    account_id = Config.INSTAGRAM_BUSINESS_ACCOUNT_ID
    token = Config.INSTAGRAM_ACCESS_TOKEN

    full_caption = f"{caption}\n\n🔗 Link in bio → {product['affiliate_url'][:50]}..."

    # Step 1: Create container
    container = _post(
        f"{account_id}/media",
        data={
            "image_url": image_url,
            "caption": full_caption[:2200],
            "access_token": token,
        },
    )
    if not container or "id" not in container:
        logger.error("Instagram: failed to create media container")
        return False

    creation_id = container["id"]

    # Step 2: Publish container
    result = _post(
        f"{account_id}/media_publish",
        data={
            "creation_id": creation_id,
            "access_token": token,
        },
    )

    if result and "id" in result:
        logger.info("Instagram: published post %s for product %s", result["id"], product["product_id"])
        return True

    logger.error("Instagram: failed to publish container %s", creation_id)
    return False


def test_connection() -> bool:
    data = _get(
        Config.INSTAGRAM_BUSINESS_ACCOUNT_ID,
        {"fields": "username,name", "access_token": Config.INSTAGRAM_ACCESS_TOKEN},
    )
    if data:
        logger.info("Instagram connected: @%s", data.get("username"))
        return True
    return False
