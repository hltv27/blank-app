"""
One-shot: fetch product by ID and post to all active platforms immediately.
Usage: cd /root/affiliate-bot && python3 -m affiliate_bot.post_now 1005010063076436 tech_gadgets
"""
import sys
import logging
import requests

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("post_now")

from affiliate_bot.config import Config
from affiliate_bot.database import init_db, save_product, record_post, was_posted
from affiliate_bot.generators.content import generate_post_text
from affiliate_bot.generators.image import create_product_card
from affiliate_bot import publishers

RAPIDAPI_HOST = "aliexpress-datahub.p.rapidapi.com"


def fetch_item(item_id: str) -> dict | None:
    """Fetch product details from RapidAPI item_detail_2."""
    headers = {
        "X-RapidAPI-Key": Config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }
    resp = requests.get(
        f"https://{RAPIDAPI_HOST}/item_detail",
        headers=headers,
        params={"itemId": item_id},
        timeout=15,
    )
    if resp.status_code != 200:
        logger.error("API error %s: %s", resp.status_code, resp.text[:200])
        return None

    data = resp.json()
    result = data.get("result", {})

    # Try to extract from item detail response
    item = result.get("item", {})
    if not item:
        logger.error("No item in response: %s", str(data)[:300])
        return None

    # Price — sku.def.promotionPrice is the discounted price (number);
    # sku.def.price can be a single value OR a range "X - Y" (string)
    sku_def = item.get("sku", {}).get("def", {})
    promotion_raw = sku_def.get("promotionPrice")
    price_field = sku_def.get("price", "0")

    def _parse_price(val, fallback: float = 0.0) -> float:
        try:
            s = str(val)
            if " - " in s:
                s = s.split(" - ")[0]
            return float(s.replace(",", "."))
        except (ValueError, TypeError):
            return fallback

    original = _parse_price(price_field)
    price = _parse_price(promotion_raw, fallback=original) if promotion_raw is not None else original

    discount = round((1 - price / original) * 100) if original > price > 0 else 0

    # Image
    images = item.get("images", [])
    image_url = ("https:" + images[0]) if images and images[0].startswith("//") else (images[0] if images else "")

    title = item.get("title", f"AliExpress Product {item_id}")[:120]

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
        "niche": sys.argv[2] if len(sys.argv) > 2 else "tech_gadgets",
        "source": "aliexpress",
        "rating": float(item.get("averageStarRate", 4.5) or 4.5),
        "orders": 0,
    }


def post_to_all(product: dict):
    save_product(product)
    caption = generate_post_text(product, "telegram")
    image_path = create_product_card(product)

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
            logger.info("%s → %s", platform, "✅" if ok else "❌")
        except Exception as e:
            logger.error("%s error: %s", platform, e)
            record_post(product["product_id"], platform, status="error", error=str(e))


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 -m affiliate_bot.post_now <item_id> [niche]")
        print("Example: python3 -m affiliate_bot.post_now 1005010063076436 tech_gadgets")
        sys.exit(1)

    item_id = sys.argv[1]
    niche = sys.argv[2] if len(sys.argv) > 2 else "tech_gadgets"

    init_db()
    logger.info("Fetching product %s ...", item_id)
    product = fetch_item(item_id)

    if not product:
        logger.error("Could not fetch product. Check RAPIDAPI_KEY and item ID.")
        sys.exit(1)

    logger.info("Product: %s | €%.2f (-%d%%)", product["title"][:60], product["price"], product["discount_percent"])
    post_to_all(product)
    logger.info("Done.")
