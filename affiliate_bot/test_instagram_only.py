"""
Test Instagram publishing using a product already saved in the local DB —
bypasses RapidAPI entirely (useful when the monthly quota is exhausted).
Usage: python3 -m affiliate_bot.test_instagram_only [niche]
"""
import sys
import logging

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
logger = logging.getLogger("test_instagram_only")

from affiliate_bot.database import init_db, get_any_products
from affiliate_bot.generators.content import generate_post_text
from affiliate_bot.generators.image import create_product_card
from affiliate_bot import publishers

NICHES = ["tech_gadgets", "home_smart", "fitness_health", "fashion_beauty"]

if __name__ == "__main__":
    init_db()

    niche = sys.argv[1] if len(sys.argv) > 1 else None
    niches_to_try = [niche] if niche else NICHES

    product = None
    for n in niches_to_try:
        products = get_any_products(n, limit=1)
        if products:
            product = products[0]
            break

    if not product:
        logger.error("No products found in DB for niches: %s", niches_to_try)
        sys.exit(1)

    logger.info("Using product: %s | %s (€%.2f)", product["product_id"], product["title"][:60], product["price"])

    try:
        image_path = create_product_card(product)
    except Exception as e:
        logger.error("Image generation failed: %s", e)
        sys.exit(1)

    caption = generate_post_text(product, "instagram")

    try:
        ok = publishers.instagram.publish(product, caption, str(image_path))
        if ok:
            logger.info("✅ Instagram publish SUCCESS")
        else:
            logger.error("❌ Instagram publish FAILED (returned False)")
    except Exception as e:
        logger.error("❌ Instagram publish EXCEPTION: %s", e)
        sys.exit(1)
