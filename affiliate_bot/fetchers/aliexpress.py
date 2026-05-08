import hashlib
import hmac
import time
import logging
import requests
from urllib.parse import urlencode

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

ALIEXPRESS_API_URL = "https://api-sg.aliexpress.com/sync"


def _sign(params: dict, secret: str) -> str:
    sorted_params = sorted(params.items())
    sign_str = secret + "".join(f"{k}{v}" for k, v in sorted_params) + secret
    return hashlib.md5(sign_str.encode("utf-8")).hexdigest().upper()


def _build_params(method: str, extra: dict) -> dict:
    params = {
        "app_key": Config.ALIEXPRESS_APP_KEY,
        "method": method,
        "timestamp": str(int(time.time() * 1000)),
        "format": "json",
        "v": "2.0",
        "sign_method": "md5",
        **extra,
    }
    params["sign"] = _sign(params, Config.ALIEXPRESS_APP_SECRET)
    return params


def _call_api(method: str, extra: dict) -> dict | None:
    params = _build_params(method, extra)
    try:
        resp = requests.post(ALIEXPRESS_API_URL, data=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        # AliExpress wraps responses with method-specific keys
        for key in data:
            if isinstance(data[key], dict):
                return data[key]
        return data
    except Exception as e:
        logger.error("AliExpress API error [%s]: %s", method, e)
        return None


def search_products(keyword: str, niche: str, min_rating: float = 4.0, page_size: int = 20) -> list[dict]:
    data = _call_api("aliexpress.affiliate.product.query", {
        "keywords": keyword,
        "page_size": str(page_size),
        "page_no": "1",
        "tracking_id": Config.ALIEXPRESS_TRACKING_ID,
        "sort": "SALE_PRICE_ASC",
        "target_currency": "EUR",
        "target_language": "EN",
    })

    if not data:
        return []

    products = []
    try:
        items = data.get("resp_result", {}).get("result", {}).get("products", {}).get("product", [])
        if isinstance(items, dict):
            items = [items]

        for item in items:
            try:
                price = float(item.get("target_sale_price", "0").split("-")[0])
                original = float(item.get("target_original_price", str(price)).split("-")[0])
                discount = round((1 - price / original) * 100) if original > price else 0
                rating = float(item.get("evaluate_rate", "0%").replace("%", "")) / 20
                orders = int(str(item.get("lastest_volume", "0")).replace(",", "").replace("+", ""))

                if rating < min_rating:
                    continue

                products.append({
                    "product_id": str(item["product_id"]),
                    "title": item.get("product_title", "")[:120],
                    "price": price,
                    "original_price": original,
                    "discount_percent": discount,
                    "image_url": item.get("product_main_image_url", ""),
                    "affiliate_url": item.get("promotion_link", item.get("product_detail_url", "")),
                    "niche": niche,
                    "source": "aliexpress",
                    "rating": rating,
                    "orders": orders,
                })
            except (KeyError, ValueError, ZeroDivisionError) as e:
                logger.debug("Skipping product: %s", e)
                continue

    except Exception as e:
        logger.error("Parsing AliExpress response: %s", e)

    return products


def get_products_for_niche(niche_key: str, niche_config: dict, limit: int = 5) -> list[dict]:
    all_products = []
    keywords = niche_config.get("keywords", [])[:3]  # max 3 keyword calls per niche

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

    # Sort by discount + orders score
    all_products.sort(
        key=lambda p: (p.get("discount_percent", 0) * 0.4 + min(p.get("orders", 0) / 1000, 50) * 0.6),
        reverse=True,
    )
    return all_products[:limit]
