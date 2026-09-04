"""
Test which AliExpress DataHub endpoint variant works for item detail lookup.
Usage: python3 -m affiliate_bot.test_endpoints 1005010063076436
"""
import sys
import requests

from affiliate_bot.config import Config

RAPIDAPI_HOST = "aliexpress-datahub.p.rapidapi.com"

CANDIDATES = [
    ("item_detail", "itemId"),
    ("item_detail_2", "itemId"),
    ("item_detail_3", "itemId"),
    ("item_detail_4", "itemId"),
    ("item_detail_5", "itemId"),
    ("item_detail_6", "itemId"),
    ("product_detail", "itemId"),
    ("item_detail", "productId"),
    ("item_detail_2", "productId"),
]

if __name__ == "__main__":
    item_id = sys.argv[1] if len(sys.argv) > 1 else "1005010063076436"
    headers = {
        "X-RapidAPI-Key": Config.RAPIDAPI_KEY,
        "X-RapidAPI-Host": RAPIDAPI_HOST,
    }

    for endpoint, param in CANDIDATES:
        try:
            resp = requests.get(
                f"https://{RAPIDAPI_HOST}/{endpoint}",
                headers=headers,
                params={param: item_id},
                timeout=15,
            )
            print(f"\n=== {endpoint} (param={param}) — HTTP {resp.status_code} ===")
            if resp.status_code == 200:
                data = resp.json()
                status = data.get("result", {}).get("status", {})
                code = status.get("code")
                item = data.get("result", {}).get("item", {})
                if item and item.get("title"):
                    print(f"  ✅ WORKS! Title: {item.get('title')[:60]}")
                else:
                    print(f"  ⚠️ status.code={code} — {str(data)[:200]}")
            else:
                print(f"  ✗ {resp.text[:150]}")
        except Exception as e:
            print(f"\n=== {endpoint} (param={param}) — EXCEPTION: {e}")

        import time
        time.sleep(3)
