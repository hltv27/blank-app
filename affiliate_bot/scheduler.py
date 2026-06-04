import logging
import random
from pathlib import Path

from affiliate_bot.config import Config
from affiliate_bot.database import (
    init_db, was_posted, save_product, record_post, get_stats,
    get_cached_products, mark_cache_refreshed,
)
from affiliate_bot.fetchers.aliexpress import get_products_for_niche
from affiliate_bot.generators.content import generate_post_text
from affiliate_bot.generators.image import create_product_card
from affiliate_bot import publishers

logger = logging.getLogger(__name__)



def refresh_product_cache(niches: dict):
    """Fetch fresh products from API for all niches and store in DB. Runs once daily."""
    logger.info("Refreshing product cache for %d niches", len(niches))
    for niche_key, niche_cfg in niches.items():
        try:
            products = get_products_for_niche(niche_key, niche_cfg, limit=20)
            for p in products:
                save_product(p)
            mark_cache_refreshed(niche_key)
            logger.info("Cache refreshed: %s — %d products", niche_key, len(products))
        except Exception as e:
            logger.error("Cache refresh error for %s: %s", niche_key, e)


def run_post_cycle(platform: str, niche_key: str, niche_config: dict) -> bool:
    logger.info("Starting post cycle: platform=%s niche=%s", platform, niche_key)

    # Use cached products from DB — only call API if cache is stale
    products = get_cached_products(niche_key, max_age_hours=12)
    if not products:
        logger.info("Cache empty/stale for %s — fetching from API", niche_key)
        products = get_products_for_niche(niche_key, niche_config, limit=20)
        for p in products:
            save_product(p)
        mark_cache_refreshed(niche_key)

    if not products:
        logger.warning("No products found for niche %s", niche_key)
        return False

    # Find a product not yet posted on this platform
    product = None
    for p in products:
        if not was_posted(p["product_id"], platform):
            product = p
            break

    if not product:
        logger.info("All products already posted for %s/%s — picking oldest", platform, niche_key)
        product = products[0]

    save_product(product)

    caption = generate_post_text(product, platform)
    image_path = create_product_card(product)

    success = False
    try:
        if platform == "telegram":
            success = publishers.telegram.publish(product, caption, image_path)

        elif platform == "instagram":
            success = publishers.instagram.publish(product, caption, str(image_path))

        elif platform == "tiktok":
            success = publishers.tiktok.publish(product, caption, str(image_path))

    except Exception as e:
        logger.error("Publish error [%s/%s]: %s", platform, niche_key, e)
        record_post(product["product_id"], platform, status="error", error=str(e))
        return False

    record_post(product["product_id"], platform, status="success" if success else "error")

    if success:
        logger.info("Posted %s to %s — %s", product["product_id"], platform, product["title"][:50])
    return success


def build_daily_schedule(niches: dict, schedule_config: dict) -> list[dict]:
    """
    Returns a list of {platform, niche, hour, minute} jobs for the day.
    Spreads posts evenly with random jitter to look organic.
    """
    jobs = []
    niche_keys = list(niches.keys())
    platforms = [
        ("telegram",  schedule_config["posts_per_day_telegram"]),
        ("instagram", schedule_config["posts_per_day_instagram"]),
        ("tiktok",    schedule_config["posts_per_day_tiktok"]),
    ]

    for platform, daily_count in platforms:
        # Spread across waking hours: 7:00 – 23:00 = 960 minutes
        interval = 960 // daily_count
        for i in range(daily_count):
            base_minute = 7 * 60 + i * interval
            jitter = random.randint(-10, 10)
            total_minute = max(7 * 60, min(23 * 60, base_minute + jitter))
            hour, minute = divmod(total_minute, 60)
            niche = niche_keys[i % len(niche_keys)]
            jobs.append({"platform": platform, "niche": niche, "hour": hour, "minute": minute})

    return sorted(jobs, key=lambda j: (j["hour"], j["minute"]))


def start(use_apscheduler: bool = True):
    init_db()

    missing = Config.validate()
    if missing:
        logger.warning("Missing config keys: %s — some platforms may fail", missing)

    niche_data = Config.load_niches()
    niches = niche_data["niches"]
    schedule_cfg = niche_data["schedule"]

    if use_apscheduler:
        _start_with_apscheduler(niches, schedule_cfg)
    else:
        _run_once(niches)


def _active_platforms() -> list[str]:
    platforms = ["telegram"]
    if Config.INSTAGRAM_USERNAME and Config.INSTAGRAM_PASSWORD:
        platforms.append("instagram")
    if Config.TIKTOK_ACCESS_TOKEN:
        platforms.append("tiktok")
    return platforms


def _start_with_apscheduler(niches: dict, schedule_cfg: dict):
    from apscheduler.schedulers.blocking import BlockingScheduler
    from apscheduler.triggers.cron import CronTrigger

    active = _active_platforms()
    logger.info("Active platforms: %s", active)

    scheduler = BlockingScheduler(timezone="UTC")
    jobs = [j for j in build_daily_schedule(niches, schedule_cfg) if j["platform"] in active]

    for job in jobs:
        niche_cfg = niches[job["niche"]]
        scheduler.add_job(
            run_post_cycle,
            CronTrigger(hour=job["hour"], minute=job["minute"]),
            args=[job["platform"], job["niche"], niche_cfg],
            id=f"{job['platform']}_{job['niche']}_{job['hour']:02d}{job['minute']:02d}",
            replace_existing=True,
            max_instances=1,
        )
        logger.debug("Scheduled: %s/%s at %02d:%02d UTC", job["platform"], job["niche"], job["hour"], job["minute"])

    # Daily product cache refresh at 06:00 UTC (before posts start at 07:00)
    scheduler.add_job(
        refresh_product_cache,
        CronTrigger(hour=6, minute=0),
        args=[niches],
        id="cache_refresh",
    )

    # Daily stats log at midnight
    scheduler.add_job(
        lambda: logger.info("Daily stats: %s", get_stats()),
        CronTrigger(hour=0, minute=5),
        id="daily_stats",
    )

    logger.info("Scheduler started with %d jobs. Press Ctrl+C to stop.", len(jobs))
    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


def _run_once(niches: dict):
    """Run one post per active platform — useful for testing."""
    for platform in _active_platforms():
        niche_key = list(niches.keys())[0]
        run_post_cycle(platform, niche_key, niches[niche_key])
