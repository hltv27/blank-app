import logging
import anthropic

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

CHANNEL = "@TopDealsGadgetss"

_client = None


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=Config.ANTHROPIC_API_KEY)
    return _client


PLATFORM_PROMPTS = {
    "telegram": {
        "max_chars": 900,
        "style": (
            "High-energy deal post. Hook in first line (use CAPS for key words like FREE SHIPPING, "
            "FLASH DEAL, PRICE DROP). Show original price crossed out then new price. "
            "Add urgency (limited stock, today only). Include rating and orders as social proof. "
            "End with '👇 Link below' — do NOT include the channel name, it will be added automatically."
        ),
    },
    "instagram": {
        "max_chars": 2000,
        "style": (
            "Aspirational and visually descriptive. Start with a powerful hook. "
            "Include price, discount, and social proof. Use line breaks for readability. "
            "Add 12-15 relevant hashtags at the end. Do NOT include channel name."
        ),
    },
    "tiktok": {
        "max_chars": 280,
        "style": (
            "Viral hook in first 5 words. Punchy, conversational, Gen-Z energy. "
            "Price drop angle. 3-5 hashtags max. Do NOT include channel name."
        ),
    },
}

NICHE_EMOJI = {
    "tech_gadgets": "📱⚡",
    "home_smart": "🏠✨",
    "fitness_health": "💪🔥",
    "fashion_accessories": "👗💎",
}

CHANNEL_CTA = {
    "telegram": f"\n\n📲 More deals daily → {CHANNEL}",
    "instagram": f"\n\n👉 Follow us for daily deals!",
    "tiktok": f" | More deals 👇",
}


def generate_post_text(product: dict, platform: str) -> str:
    if not Config.ANTHROPIC_API_KEY:
        return _fallback_text(product, platform)

    style = PLATFORM_PROMPTS.get(platform, PLATFORM_PROMPTS["telegram"])
    niche_emoji = NICHE_EMOJI.get(product.get("niche", ""), "🛒")
    discount = product.get("discount_percent", 0)
    price = product["price"]
    original = product.get("original_price", price)
    orders = product.get("orders", 0)
    rating = product.get("rating", 4.5)
    savings = original - price

    flash = discount >= 50
    discount_note = f"{'⚡ FLASH DEAL — ' if flash else ''}{discount:.0f}% OFF (save €{savings:.2f})" if discount >= 10 else ""

    prompt = f"""You are an expert affiliate marketing copywriter for a deals channel.

Product: {product['title']}
Price: €{price:.2f} (was €{original:.2f})
{discount_note}
Niche: {niche_emoji}
Rating: {rating:.1f}/5 ⭐ · {orders:,}+ orders

Write a {platform} post in English.
Style: {style['style']}
Max {style['max_chars']} characters.
Do NOT include any URL or channel name — those are added automatically.
Output ONLY the post text."""

    try:
        message = _get_client().messages.create(
            model="claude-haiku-4-5-20251001",
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        body = message.content[0].text.strip()
    except Exception as e:
        logger.error("Content generation error: %s", e)
        body = _fallback_text(product, platform, add_cta=False)

    return body + CHANNEL_CTA.get(platform, "")


def _fallback_text(product: dict, platform: str, add_cta: bool = True) -> str:
    title = product["title"][:70]
    price = product["price"]
    original = product.get("original_price", price)
    discount = product.get("discount_percent", 0)
    orders = product.get("orders", 0)
    rating = product.get("rating", 0)
    savings = original - price
    niche_emoji = NICHE_EMOJI.get(product.get("niche", ""), "🛒")

    if discount >= 50:
        header = f"⚡ FLASH DEAL ⚡\n\n"
    elif discount >= 25:
        header = f"🔥 HOT DEAL 🔥\n\n"
    else:
        header = f"🛒 Deal of the Day\n\n"

    price_line = f"💰 ~~€{original:.2f}~~ → **€{price:.2f}**" if discount >= 10 else f"💰 €{price:.2f}"
    discount_line = f"\n🏷️ {discount:.0f}% OFF — Save €{savings:.2f}" if discount >= 10 else ""
    social_proof = ""
    if rating >= 4.0:
        social_proof += f"\n⭐ {rating:.1f}/5"
    if orders >= 100:
        social_proof += f" · {orders:,}+ sold"

    body = f"{header}{niche_emoji} {title}\n\n{price_line}{discount_line}{social_proof}\n\n👇 Link below"

    if add_cta:
        body += CHANNEL_CTA.get(platform, "")

    return body
