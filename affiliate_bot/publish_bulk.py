"""
Bulk publish multiple AliExpress products to all platforms.
Usage: python3 -m affiliate_bot.publish_bulk "item_id:niche" "item_id:niche" ...
Example: python3 -m affiliate_bot.publish_bulk "1005010063076436:tech_gadgets" "1005009999999999:fitness_health"
"""
import sys
import time
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("publish_bulk")

from affiliate_bot.config import Config
from affiliate_bot.database import init_db, save_product, record_post
from affiliate_bot.generators.content import generate_post_text
from affiliate_bot.generators.image import create_product_card
from affiliate_bot import publishers

RAPIDAPI_HOST = "aliexpress-datahub.p.rapidapi.com"
DELAY_BETWEEN_REQUESTS = 6  # seconds — respect RapidAPI Basic rate limit


def fetch_item(item_id: str, niche: str, retry: bool = True) -> dict | None:
    """Fetch product details from RapidAPI. Retries once on 429 with backoff."""
    headers = {
        "X-RapidAPI-Key": Config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    try:
        resp = requests.get(
            f"https://{RAPIDAPI_HOST}/item_detail_2",
            headers=headers,
            params={"itemId": item_id},
            timeout=15,
        )
        if resp.status_code == 429:
            if retry:
                logger.warning("[%s] 429 — waiting 20s and retrying once...", item_id)
                time.sleep(20)
                return fetch_item(item_id, niche, retry=False)
            logger.error("[%s] API error 429 (after retry)", item_id)
            return None
        if resp.status_code != 200:
            logger.error("[%s] API error %s: %s", item_id, resp.status_code, resp.text[:200])
            return None

        data = resp.json()
        item = data.get("result", {}).get("item", {})
        if not item:
            logger.error("[%s] No item in response. Raw: %s", item_id, str(data)[:500])
            return None

        # Price
        price_info = item.get("sku", {}).get("base", [{}])[0] if item.get("sku", {}).get("base") else {}
        price_raw = price_info.get("promotionPrice") or price_info.get("price", "0")
        original_raw = price_info.get("price", price_raw)
        try:
            price = float(str(price_raw).replace(",", "."))
            original = float(str(original_raw).replace(",", "."))
        except (ValueError, TypeError):
            price = 0.0
            original = 0.0

        discount = round((1 - price / original) * 100) if original > price > 0 else 0

        # Image
        images = item.get("images", [])
        image_url = ("https:" + images[0]) if images and images[0].startswith("//") else (images[0] if images else "")

        title = item.get("title", f"Product {item_id}")[:120]

        tracking = Config.ALIEXPRESS_TRACKING_ID
        affiliate_url = f"https://www.aliexpress.com/item/{item_id}.html"
        if tracking:
            affiliate_url += f"?aff_fcid={tracking}&aff_platform=portals-tool"

        return {
            "product_id": item_id,
            "title": title,
            "price": price,
            "original_price": original,
            "discount_percent": discount,
            "image_url": image_url,
            "affiliate_url": affiliate_url,
            "niche": niche,
            "source": "aliexpress",
            "rating": float(item.get("averageStarRate", 4.5) or 4.5),
            "orders": 0,
        }
    except Exception as e:
        logger.error("[%s] Fetch error: %s", item_id, e)
        return None


def post_product(product: dict):
    """Post single product to all active platforms."""
    item_id = product["product_id"]
    save_product(product)

    try:
        image_path = create_product_card(product)
    except Exception as e:
        logger.error("[%s] Image generation failed: %s", item_id, e)
        image_path = None

    active = []
    if Config.TELEGRAM_BOT_TOKEN:
        active.append("telegram")
    if Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
        active.append("instagram")
    if Config.FACEBOOK_PAGE_ID and Config.FACEBOOK_PAGE_TOKEN:
        active.append("facebook")

    for platform in active:
        try:
            cap = generate_post_text(product, platform)
            if platform == "telegram":
                ok = publishers.telegram.publish(product, cap, str(image_path))
            elif platform == "instagram":
                ok = publishers.instagram.publish(product, cap, str(image_path))
            elif platform == "facebook":
                ok = publishers.facebook.publish(product, cap, str(image_path))
            else:
                ok = False

            status = "success" if ok else "error"
            record_post(product["product_id"], platform, status=status)
            logger.info("[%s] %s → %s", item_id, platform, "✅" if ok else "❌")
        except Exception as e:
            logger.error("[%s] %s error: %s", item_id, platform, str(e)[:100])
            record_post(product["product_id"], platform, status="error", error=str(e)[:200])


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m affiliate_bot.publish_bulk <item:niche> [<item:niche> ...]")
        print("Example: python3 -m affiliate_bot.publish_bulk '1005010063076436:tech' '1005009999999:fitness'")
        sys.exit(1)

    init_db()

    items = []
    for arg in sys.argv[1:]:
        parts = arg.split(":")
        item_id = parts[0].strip()
        niche = parts[1].strip() if len(parts) > 1 else "tech_gadgets"
        items.append((item_id, niche))

    logger.info("Fetching %d products (sequential, %ds delay to respect rate limit)...", len(items), DELAY_BETWEEN_REQUESTS)

    # Fetch sequentially with delay to avoid 429
    products = []
    for i, (iid, niche) in enumerate(items):
        if i > 0:
            time.sleep(DELAY_BETWEEN_REQUESTS)
        product = fetch_item(iid, niche)
        if product:
            products.append(product)
            logger.info("[%s] ✓ Fetched: %s (€%.2f)", iid, product["title"][:50], product["price"])
        else:
            logger.warning("[%s] ✗ Could not fetch", iid)

    logger.info("\nPublishing %d/%d products to all platforms...", len(products), len(items))
    for product in products:
        post_product(product)

    logger.info("\nDone. %d/%d products published.", len(products), len(items))
