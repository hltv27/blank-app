"""
Updates docs/products.json in GitHub via API so GitHub Pages reflects new deals.
Requires GITHUB_TOKEN in .env (personal access token with repo write access).
"""
import base64
import json
import logging
from datetime import datetime

import requests

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

REPO       = "hltv27/blank-app"
FILE_PATH  = "docs/products.json"
BRANCH     = "claude/affiliate-bot-automation-5rsFF"
API_BASE   = "https://api.github.com"
MAX_PRODUCTS = 50


def _headers() -> dict:
    return {
        "Authorization": f"token {Config.GITHUB_TOKEN}",
        "Accept": "application/vnd.github.v3+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def publish(product: dict, caption: str, image_path: str, platform: str = "web") -> bool:
    """Add product to docs/products.json and push to GitHub."""
    if not Config.GITHUB_TOKEN:
        logger.debug("GITHUB_TOKEN not set — skipping website update")
        return False

    url = f"{API_BASE}/repos/{REPO}/contents/{FILE_PATH}"

    try:
        # Fetch current file
        resp = requests.get(url, headers=_headers(), params={"ref": BRANCH}, timeout=10)

        if resp.status_code == 200:
            data = resp.json()
            sha = data["sha"]
            content = json.loads(base64.b64decode(data["content"]).decode())
        elif resp.status_code == 404:
            sha = None
            content = {"products": [], "updated_at": None, "channel": "@TopDealsGadgetss"}
        else:
            logger.error("GitHub fetch error: %s %s", resp.status_code, resp.text[:200])
            return False

        # Build new entry
        new_entry = {
            "product_id":      product["product_id"],
            "title":           product["title"],
            "price":           product["price"],
            "original_price":  product.get("original_price", product["price"]),
            "discount_percent": product.get("discount_percent", 0),
            "image_url":       product["image_url"],
            "affiliate_url":   product["affiliate_url"],
            "niche":           product.get("niche", ""),
            "posted_at":       datetime.utcnow().isoformat(),
            "platform":        platform,
        }

        # Remove duplicate then prepend
        products = [p for p in content.get("products", []) if p["product_id"] != product["product_id"]]
        products.insert(0, new_entry)
        products = products[:MAX_PRODUCTS]

        content["products"]   = products
        content["updated_at"] = datetime.utcnow().isoformat()

        # Encode and push
        encoded = base64.b64encode(
            json.dumps(content, ensure_ascii=False, indent=2).encode()
        ).decode()

        payload = {
            "message": f"bot: add deal {product['product_id'][:12]}",
            "content": encoded,
            "branch":  BRANCH,
            "committer": {"name": "TopDeals Bot", "email": "bot@hugo.deals"},
        }
        if sha:
            payload["sha"] = sha

        put = requests.put(url, headers=_headers(), json=payload, timeout=15)

        if put.status_code in (200, 201):
            logger.info("Website updated: %s (%d products)", product["product_id"], len(products))
            return True
        else:
            logger.error("GitHub push error: %s %s", put.status_code, put.text[:200])
            return False

    except Exception as e:
        logger.error("website.publish error: %s", e)
        return False


def test_connection() -> bool:
    if not Config.GITHUB_TOKEN:
        return False
    try:
        resp = requests.get(
            f"{API_BASE}/repos/{REPO}",
            headers=_headers(),
            timeout=8,
        )
        return resp.status_code == 200
    except Exception as e:
        logger.error("website.test_connection: %s", e)
        return False
