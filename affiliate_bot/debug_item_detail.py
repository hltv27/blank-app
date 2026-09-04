"""
Dump full item_detail response for inspection.
Usage: python3 -m affiliate_bot.debug_item_detail 1005011779826745
"""
import sys
import json
import requests

from affiliate_bot.config import Config

RAPIDAPI_HOST = "aliexpress-datahub.p.rapidapi.com"

if __name__ == "__main__":
    item_id = sys.argv[1] if len(sys.argv) > 1 else "1005011779826745"
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
    print(f"HTTP {resp.status_code}")
    data = resp.json()
    item = data.get("result", {}).get("item", {})
    # Print only the keys and a preview of each value (avoid dumping huge nested blobs)
    print("\n=== TOP-LEVEL ITEM KEYS ===")
    for k, v in item.items():
        preview = json.dumps(v, ensure_ascii=False)[:200]
        print(f"{k}: {preview}")
