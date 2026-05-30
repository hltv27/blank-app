import anthropic
import base64
import re
from typing import Dict, List, Tuple


def _media_type(data: bytes) -> str:
    if data[:8] == b'\x89PNG\r\n\x1a\n':
        return 'image/png'
    if data[:4] == b'RIFF' and data[8:12] == b'WEBP':
        return 'image/webp'
    return 'image/jpeg'


def _extract_one(client: anthropic.Anthropic, image_data: bytes) -> List[str]:
    b64 = base64.standard_b64encode(image_data).decode()
    resp = client.messages.create(
        model="claude-haiku-4-5-20251001",
        max_tokens=512,
        messages=[{
            "role": "user",
            "content": [
                {
                    "type": "image",
                    "source": {"type": "base64", "media_type": _media_type(image_data), "data": b64}
                },
                {
                    "type": "text",
                    "text": (
                        "Extract all stock ticker symbols visible in this image. "
                        "Return ONLY the ticker symbols (e.g. AAPL, NVDA, TSLA), one per line. "
                        "Convert company names to their official US/international stock tickers. "
                        "Only include valid tickers (1-7 uppercase letters). "
                        "No explanations, no extra text — tickers only."
                    )
                }
            ]
        }]
    )
    tickers = []
    for line in resp.content[0].text.strip().splitlines():
        t = re.sub(r'[^A-Z0-9\.]', '', line.strip().upper())
        if 1 <= len(t) <= 7:
            tickers.append(t)
    return list(set(tickers))


def extract_stocks_from_images(
    images: List[Tuple[str, bytes]],
    api_key: str
) -> Dict[str, List[str]]:
    """Returns {filename: [tickers]}."""
    client = anthropic.Anthropic(api_key=api_key)
    results = {}
    for filename, data in images:
        try:
            results[filename] = _extract_one(client, data)
        except Exception as e:
            results[filename] = []
    return results
