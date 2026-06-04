import sqlite3
import logging
from datetime import datetime, timedelta
from pathlib import Path
from contextlib import contextmanager

from affiliate_bot.config import Config

logger = logging.getLogger(__name__)


@contextmanager
def get_db():
    conn = sqlite3.connect(Config.DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT UNIQUE NOT NULL,
                title TEXT,
                price REAL,
                original_price REAL,
                discount_percent REAL,
                image_url TEXT,
                affiliate_url TEXT,
                niche TEXT,
                source TEXT DEFAULT 'aliexpress',
                rating REAL,
                orders INTEGER,
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                posted_at TEXT DEFAULT (datetime('now')),
                status TEXT DEFAULT 'success',
                error_message TEXT,
                FOREIGN KEY (product_id) REFERENCES products(product_id)
            );

            CREATE TABLE IF NOT EXISTS post_queue (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_id TEXT NOT NULL,
                platform TEXT NOT NULL,
                niche TEXT NOT NULL,
                scheduled_at TEXT NOT NULL,
                status TEXT DEFAULT 'pending',
                created_at TEXT DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS product_cache (
                niche TEXT PRIMARY KEY,
                fetched_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_posts_product_platform
                ON posts(product_id, platform);
            CREATE INDEX IF NOT EXISTS idx_posts_posted_at
                ON posts(posted_at);
        """)
    logger.info("Database initialized at %s", Config.DB_PATH)


def was_posted(product_id: str, platform: str, days: int = 30) -> bool:
    since = (datetime.utcnow() - timedelta(days=days)).isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT 1 FROM posts WHERE product_id=? AND platform=? AND posted_at>? AND status='success'",
            (product_id, platform, since)
        ).fetchone()
    return row is not None


def save_product(product: dict) -> bool:
    try:
        with get_db() as conn:
            conn.execute("""
                INSERT OR REPLACE INTO products
                    (product_id, title, price, original_price, discount_percent,
                     image_url, affiliate_url, niche, source, rating, orders)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product["product_id"], product["title"], product["price"],
                product.get("original_price"), product.get("discount_percent"),
                product["image_url"], product["affiliate_url"], product["niche"],
                product.get("source", "aliexpress"), product.get("rating"),
                product.get("orders")
            ))
        return True
    except Exception as e:
        logger.error("save_product error: %s", e)
        return False


def record_post(product_id: str, platform: str, status: str = "success", error: str = None):
    with get_db() as conn:
        conn.execute(
            "INSERT INTO posts (product_id, platform, status, error_message) VALUES (?, ?, ?, ?)",
            (product_id, platform, status, error)
        )


def get_cached_products(niche: str, max_age_hours: int = 12) -> list[dict]:
    since = (datetime.utcnow() - timedelta(hours=max_age_hours)).isoformat()
    with get_db() as conn:
        row = conn.execute(
            "SELECT fetched_at FROM product_cache WHERE niche=?", (niche,)
        ).fetchone()
        if not row or row["fetched_at"] < since:
            return []
        rows = conn.execute(
            "SELECT * FROM products WHERE niche=? ORDER BY discount_percent DESC, orders DESC LIMIT 20",
            (niche,)
        ).fetchall()
    return [dict(r) for r in rows]


def mark_cache_refreshed(niche: str):
    with get_db() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO product_cache (niche, fetched_at) VALUES (?, datetime('now'))",
            (niche,)
        )


def get_stats() -> dict:
    with get_db() as conn:
        total_posts = conn.execute("SELECT COUNT(*) FROM posts WHERE status='success'").fetchone()[0]
        today = datetime.utcnow().strftime("%Y-%m-%d")
        today_posts = conn.execute(
            "SELECT COUNT(*) FROM posts WHERE status='success' AND posted_at LIKE ?",
            (f"{today}%",)
        ).fetchone()[0]
        by_platform = conn.execute(
            "SELECT platform, COUNT(*) as cnt FROM posts WHERE status='success' GROUP BY platform"
        ).fetchall()
    return {
        "total_posts": total_posts,
        "today_posts": today_posts,
        "by_platform": {row["platform"]: row["cnt"] for row in by_platform}
    }
