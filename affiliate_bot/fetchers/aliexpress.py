import logging
import requests

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

RAPIDAPI_HOST = "aliexpress-datahub.p.rapidapi.com"
RAPIDAPI_BASE = f"https://{RAPIDAPI_HOST}"


def _headers() -> dict:
    return {
        "X-RapidAPI-Key": Config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }


def _fix_url(url: str) -> str:
    if url.startswith("//"):
        return "https:" + url
    return url


def _affiliate_url(product_id: str) -> str:
    base = f"https://www.aliexpress.com/item/{product_id}.html"
    tracking = Config.ALIEXPRESS_TRACKING_ID
    if tracking:
        return f"{base}?aff_fcid={tracking}&aff_platform=portals-tool"
    return base


def search_products(keyword: str, niche: str, min_rating: float = 4.0, page_size: int = 20) -> list[dict]:
    try:
        resp = requests.get(
            f"{RAPIDAPI_BASE}/item_search_2",
            headers=_headers(),
            params={"q": keyword, "page": "1"},
            timeout=15,
        )
        resp.raise_for_status()
        data = resp.json()
    except Exception as e:
        logger.error("RapidAPI search error: %s", e)
        return []

    status_code = data.get("result", {}).get("status", {}).get("code")
    if status_code != 200:
        logger.warning("RapidAPI returned status %s for keyword '%s'", status_code, keyword)
        return []

    products = []
    items = data.get("result", {}).get("resultList", [])

    for entry in items:
        try:
            item = entry.get("item", {})

            price_raw = item.get("sku", {}).get("def", {}).get("promotionPrice")
            if not price_raw:
                continue
            price = float(price_raw)
            if price <= 0:
                continue

            # original price not available — use same as price
            original_raw = item.get("sku", {}).get("def", {}).get("price")
            original = float(original_raw) if original_raw else price
            discount = round((1 - price / original) * 100) if original > price else 0

            rating = float(item.get("averageStarRate", 0) or 0)
            if rating < min_rating:
                continue

            orders_raw = item.get("sales", "0") or "0"
            orders = int(str(orders_raw).replace(",", "").replace("+", ""))

            product_id = str(item.get("itemId", ""))
            image = _fix_url(item.get("image", ""))
            title = item.get("title", "")[:120]

            if not product_id or not title:
                continue

            products.append({
                "product_id": product_id,
                "title": title,
                "price": price,
                "original_price": original,
                "discount_percent": discount,
                "image_url": image,
                "affiliate_url": _affiliate_url(product_id),
                "niche": niche,
                "source": "aliexpress",
                "rating": rating,
                "orders": orders,
            })
        except (KeyError, ValueError, ZeroDivisionError, TypeError) as e:
            logger.debug("Skipping product: %s", e)
            continue

    return products[:page_size]


def get_products_for_niche(niche_key: str, niche_config: dict, limit: int = 5) -> list[dict]:
    all_products = []
    keywords = niche_config.get("keywords", [])[:3]

    for keyword in keywords:
        found = search_products(
            keyword=keyword,
            niche=niche_key,
            min_rating=niche_config.get("min_rating", 4.0),
            page_size=10,
        )
        all_products.extend(found)
        if len(all_products) >= limit * 2:
            break

    all_products.sort(
        key=lambda p: (p.get("discount_percent", 0) * 0.4 + min(p.get("orders", 0) / 1000, 50) * 0.6),
        reverse=True,
    )
    return all_products[:limit]
