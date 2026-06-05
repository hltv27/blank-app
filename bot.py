#!/usr/bin/env python3
"""
Affiliate Bot — entry point.

Usage:
    python bot.py              # start 24/7 scheduler
    python bot.py --test       # run one post per channel (smoke test)
    python bot.py --stats      # print database stats and exit
    python bot.py --check      # verify API connections and exit
"""
import argparse
import logging
import sys

from affiliate_bot.config import Config

logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL, logging.INFO),
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("affiliate_bot.log"),
    ],
)
logger = logging.getLogger(__name__)


def cmd_check():
    from affiliate_bot.publishers import telegram, instagram, tiktok
    results = {
        "Telegram":  telegram.test_connection(),
        "Instagram": instagram.test_connection(),
        "TikTok":    tiktok.test_connection(),
    }
    for platform, ok in results.items():
        status = "✅ OK" if ok else "❌ FAILED"
        print(f"  {platform:12s} {status}")


def cmd_stats():
    from affiliate_bot.database import init_db, get_stats
    init_db()
    stats = get_stats()
    print(f"Total posts:  {stats['total_posts']}")
    print(f"Today posts:  {stats['today_posts']}")
    for platform, count in stats["by_platform"].items():
        print(f"  {platform:12s} {count}")


def main():
    parser = argparse.ArgumentParser(description="Affiliate Bot")
    parser.add_argument("--test",  action="store_true", help="Post once per channel and exit")
    parser.add_argument("--stats", action="store_true", help="Show posting statistics")
    parser.add_argument("--check", action="store_true", help="Test API connections")
    args = parser.parse_args()

    missing = Config.validate()
    if missing and not args.check:
        logger.error("Missing required config: %s", missing)
        logger.error("Copy .env.example to .env and fill in your keys.")
        sys.exit(1)

    if args.stats:
        cmd_stats()
    elif args.check:
        cmd_check()
    elif args.test:
        from affiliate_bot.scheduler import start
        start(use_apscheduler=False)
    else:
        from affiliate_bot.scheduler import start
        start(use_apscheduler=True)


if __name__ == "__main__":
    main()
