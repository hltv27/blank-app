import logging
import anthropic

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    return _client


PLATFORM_PROMPTS = {
    "telegram": {
        "max_chars": 1024,
        "style": "engaging and direct, with emoji, short sentences. Include price and discount prominently. End with a clear call-to-action.",
    },
    "instagram": {
        "max_chars": 2200,
        "style": "visually descriptive, aspirational tone, use line breaks for readability, include 10-15 relevant hashtags at the end.",
    },
    "tiktok": {
        "max_chars": 300,
        "style": "viral, punchy, hook in first 5 words, use trending slang, 3-5 hashtags only, feels authentic not salesy.",
    },
}


def generate_post_text(product: dict, platform: str) -> str:
    # Use AI only if Anthropic key is configured, otherwise use fallback
    if not Config.ANTHROPIC_API_KEY:
        return _fallback_text(product, platform)

    style = PLATFORM_PROMPTS.get(platform, PLATFORM_PROMPTS["telegram"])
    niche_emoji = {
        "tech_gadgets": "📱⚡",
        "home_smart": "🏠✨",
        "fitness_health": "💪🔥",
        "fashion_accessories": "👗💎",
    }.get(product.get("niche", ""), "🛒")

    discount_note = ""
    if product.get("discount_percent", 0) >= 20:
        discount_note = f"Discount: {product['discount_percent']:.0f}% OFF — "

    prompt = f"""You are an affiliate marketing copywriter creating a {platform} post.

Product: {product['title']}
Price: €{product['price']:.2f}
{discount_note}Original price: €{product.get('original_price', product['price']):.2f}
Niche emojis: {niche_emoji}
Rating: {product.get('rating', 4.5):.1f}/5 ⭐
Orders: {product.get('orders', 0):,}+

Write a {platform} post in English. Style: {style['style']}
Maximum {style['max_chars']} characters. Do NOT include the actual URL — it will be appended separately.
Output ONLY the post text, nothing else."""

    try:
        message = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        return message.content[0].text.strip()
    except Exception as e:
        logger.error("Content generation error: %s", e)
        return _fallback_text(product, platform)


def _fallback_text(product: dict, platform: str) -> str:
    title = product["title"][:60]
    price = product["price"]
    discount = product.get("discount_percent", 0)
    discount_str = f" 🔥 {discount:.0f}% OFF!" if discount >= 10 else ""
    return f"🛒 {title}{discount_str}\n💰 Only €{price:.2f}\n⭐ Highly rated product"
