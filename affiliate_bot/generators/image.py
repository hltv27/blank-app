import io
import logging
import requests
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)

NICHE_COLORS = {
    "tech_gadgets":       {"bg": (15, 15, 35),    "accent": (0, 200, 255),   "text": (255, 255, 255)},
    "home_smart":         {"bg": (20, 35, 20),    "accent": (80, 200, 120),  "text": (255, 255, 255)},
    "fitness_health":     {"bg": (35, 10, 10),    "accent": (255, 80, 60),   "text": (255, 255, 255)},
    "fashion_accessories":{"bg": (30, 20, 40),    "accent": (220, 150, 255), "text": (255, 255, 255)},
}
DEFAULT_COLORS = {"bg": (20, 20, 30), "accent": (255, 200, 0), "text": (255, 255, 255)}

CARD_W, CARD_H = 1080, 1080
PRODUCT_AREA = (80, 120, 1000, 720)


def _download_image(url: str) -> Image.Image | None:
    try:
        resp = requests.get(url, timeout=10)
        resp.raise_for_status()
        return Image.open(io.BytesIO(resp.content)).convert("RGBA")
    except Exception as e:
        logger.warning("Could not download product image: %s", e)
        return None


def _get_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSansBold.ttf" if bold else "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
    ]
    for path in font_paths:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def _wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
    words = text.split()
    lines, current = [], ""
    for word in words:
        test = f"{current} {word}".strip()
        bbox = font.getbbox(test)
        if bbox[2] - bbox[0] <= max_width:
            current = test
        else:
            if current:
                lines.append(current)
            current = word
    if current:
        lines.append(current)
    return lines


def create_product_card(product: dict) -> Path:
    Config.IMAGES_DIR.mkdir(parents=True, exist_ok=True)
    out_path = Config.IMAGES_DIR / f"{product['product_id']}.jpg"

    colors = NICHE_COLORS.get(product.get("niche", ""), DEFAULT_COLORS)

    # Base card
    card = Image.new("RGB", (CARD_W, CARD_H), colors["bg"])
    draw = ImageDraw.Draw(card)

    # Gradient overlay at bottom
    overlay = Image.new("RGBA", (CARD_W, 400), (0, 0, 0, 0))
    for i in range(400):
        alpha = int((i / 400) * 200)
        ImageDraw.Draw(overlay).line([(0, i), (CARD_W, i)], fill=(*colors["bg"], alpha))
    card.paste(Image.alpha_composite(Image.new("RGBA", (CARD_W, 400), (0, 0, 0, 0)), overlay).convert("RGB"),
               (0, CARD_H - 400))

    # Product image
    product_img = _download_image(product.get("image_url", ""))
    if product_img:
        pw = PRODUCT_AREA[2] - PRODUCT_AREA[0]
        ph = PRODUCT_AREA[3] - PRODUCT_AREA[1]
        product_img.thumbnail((pw, ph), Image.LANCZOS)
        px = PRODUCT_AREA[0] + (pw - product_img.width) // 2
        py = PRODUCT_AREA[1] + (ph - product_img.height) // 2
        if product_img.mode == "RGBA":
            card.paste(product_img, (px, py), product_img)
        else:
            card.paste(product_img, (px, py))

    # Accent bar top
    draw.rectangle([(0, 0), (CARD_W, 8)], fill=colors["accent"])

    # Discount badge
    discount = product.get("discount_percent", 0)
    if discount >= 10:
        badge_r = 70
        bx, by = CARD_W - badge_r - 30, badge_r + 30
        draw.ellipse([(bx - badge_r, by - badge_r), (bx + badge_r, by + badge_r)], fill=colors["accent"])
        font_badge = _get_font(22, bold=True)
        draw.text((bx, by), f"-{discount:.0f}%", font=font_badge, fill=colors["bg"], anchor="mm")

    # Title
    title = product["title"][:80]
    font_title = _get_font(36, bold=True)
    lines = _wrap_text(title, font_title, CARD_W - 80)[:3]
    y = CARD_H - 320
    for line in lines:
        draw.text((40, y), line, font=font_title, fill=colors["text"])
        y += 46

    # Price
    font_price = _get_font(58, bold=True)
    font_original = _get_font(30)
    y += 10
    draw.text((40, y), f"€{product['price']:.2f}", font=font_price, fill=colors["accent"])
    if product.get("original_price") and product["original_price"] > product["price"]:
        orig_text = f"€{product['original_price']:.2f}"
        draw.text((40 + 180, y + 20), orig_text, font=font_original, fill=(160, 160, 160))
        # strikethrough
        bbox = font_original.getbbox(orig_text)
        mid_y = y + 20 + (bbox[3] - bbox[1]) // 2
        draw.line([(40 + 180, mid_y), (40 + 180 + bbox[2], mid_y)], fill=(160, 160, 160), width=2)

    # Rating + orders
    font_small = _get_font(28)
    rating = product.get("rating", 0)
    orders = product.get("orders", 0)
    stars = "⭐" * int(round(rating))
    info = f"{stars}  {rating:.1f}   •   {orders:,}+ sold"
    draw.text((40, CARD_H - 60), info, font=font_small, fill=(180, 180, 180))

    # Accent bar bottom
    draw.rectangle([(0, CARD_H - 8), (CARD_W, CARD_H)], fill=colors["accent"])

    card.save(str(out_path), "JPEG", quality=92)
    logger.debug("Card saved: %s", out_path)
    return out_path
