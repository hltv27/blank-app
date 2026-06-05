import logging
import time
import requests

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

TIKTOK_API = "https://open.tiktokapis.com/v2"


def _post(endpoint: str, payload: dict) -> dict | None:
    url = f"{TIKTOK_API}/{endpoint}"
    headers = {
        "Authorization": f"Bearer {Config.TIKTOK_ACCESS_TOKEN}",
        "Content-Type": "application/json; charset=UTF-8",
    }
    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=60)
        data = resp.json()
        if data.get("error", {}).get("code", "ok") != "ok":
            logger.error("TikTok API error: %s", data.get("error"))
            return None
        return data
    except Exception as e:
        logger.error("TikTok request error: %s", e)
        return None


def _init_photo_upload(image_paths: list[str], caption: str) -> str | None:
    """Initialise a photo post (carousel) upload."""
    payload = {
        "post_info": {
            "title": caption[:150],
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "auto_add_music": True,
        },
        "source_info": {
            "source": "FILE_UPLOAD",
            "photo_cover_index": 0,
            "photo_images": [],
        },
        "media_type": "PHOTO",
        "post_mode": "DIRECT_POST",
    }
    data = _post("post/publish/content/init/", payload)
    if not data:
        return None
    return data.get("data", {}).get("publish_id")


def publish(product: dict, caption: str, image_path: str) -> bool:
    """
    TikTok Content Posting API — photo post.
    Requires the scope: video.publish (or photo.publish where available).
    """
    full_caption = caption[:150]

    # TikTok photo post via direct URL is not supported in v2 API without video.
    # We use the file upload flow: init → upload → (auto publish).
    # For simplicity we use the URL-based approach via content posting init.
    payload = {
        "post_info": {
            "title": full_caption,
            "privacy_level": "PUBLIC_TO_EVERYONE",
            "disable_duet": False,
            "disable_comment": False,
            "disable_stitch": False,
            "auto_add_music": True,
        },
        "source_info": {
            "source": "PULL_FROM_URL",
            "photo_images": [product.get("image_url", "")],
            "photo_cover_index": 0,
        },
        "media_type": "PHOTO",
        "post_mode": "DIRECT_POST",
    }

    data = _post("post/publish/content/init/", payload)
    if not data:
        return False

    publish_id = data.get("data", {}).get("publish_id")
    if not publish_id:
        logger.error("TikTok: no publish_id in response")
        return False

    # Poll status (max 30s)
    for _ in range(6):
        time.sleep(5)
        status_resp = requests.get(
            f"{TIKTOK_API}/post/publish/status/fetch/",
            headers={"Authorization": f"Bearer {Config.TIKTOK_ACCESS_TOKEN}"},
            params={"publish_id": publish_id},
            timeout=15,
        )
        status = status_resp.json().get("data", {}).get("status")
        if status == "PUBLISH_COMPLETE":
            logger.info("TikTok: published product %s (publish_id=%s)", product["product_id"], publish_id)
            return True
        if status in ("FAILED", "SPAM_RISK_CREATOR_BLOCKED"):
            logger.error("TikTok publish failed: status=%s", status)
            return False

    logger.warning("TikTok: publish_id=%s did not complete in time", publish_id)
    return False


def test_connection() -> bool:
    resp = requests.get(
        f"{TIKTOK_API}/user/info/",
        headers={"Authorization": f"Bearer {Config.TIKTOK_ACCESS_TOKEN}"},
        params={"fields": "display_name,username"},
        timeout=15,
    )
    data = resp.json()
    if data.get("error", {}).get("code", "ok") == "ok":
        user = data.get("data", {}).get("user", {})
        logger.info("TikTok connected: @%s", user.get("username", "unknown"))
        return True
    return False
