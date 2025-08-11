import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import List, Optional, Tuple, Dict, Any

DATABASE_PATH = Path("/workspace/data/blog.db")

SCHEMA_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'admin',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    title TEXT NOT NULL,
    slug TEXT UNIQUE NOT NULL,
    content_md TEXT NOT NULL,
    cover_image TEXT,
    published INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_posts_published_created ON posts(published, created_at DESC);
"""


@contextmanager
def get_conn():
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DATABASE_PATH))
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()


def init_db() -> None:
    with get_conn() as conn:
        conn.executescript(SCHEMA_SQL)
        conn.commit()


# User ops

def get_user_by_username(username: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM users WHERE username = ?", (username,))
        return cur.fetchone()


def create_user(username: str, password_hash: str, role: str = "admin") -> int:
    with get_conn() as conn:
        cur = conn.execute(
            "INSERT INTO users (username, password_hash, role) VALUES (?, ?, ?)",
            (username, password_hash, role),
        )
        conn.commit()
        return cur.lastrowid


# Post ops

def list_posts(published_only: bool = True) -> List[sqlite3.Row]:
    with get_conn() as conn:
        if published_only:
            cur = conn.execute(
                "SELECT * FROM posts WHERE published = 1 ORDER BY created_at DESC"
            )
        else:
            cur = conn.execute("SELECT * FROM posts ORDER BY created_at DESC")
        return cur.fetchall()


def get_post_by_slug(slug: str) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM posts WHERE slug = ?", (slug,))
        return cur.fetchone()


def get_post_by_id(post_id: int) -> Optional[sqlite3.Row]:
    with get_conn() as conn:
        cur = conn.execute("SELECT * FROM posts WHERE id = ?", (post_id,))
        return cur.fetchone()


def create_post(title: str, slug: str, content_md: str, cover_image: Optional[str], published: bool) -> int:
    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO posts (title, slug, content_md, cover_image, published)
            VALUES (?, ?, ?, ?, ?)
            """,
            (title, slug, content_md, cover_image, 1 if published else 0),
        )
        conn.commit()
        return cur.lastrowid


def update_post(
    post_id: int,
    title: str,
    slug: str,
    content_md: str,
    cover_image: Optional[str],
    published: bool,
) -> None:
    with get_conn() as conn:
        conn.execute(
            """
            UPDATE posts
            SET title = ?, slug = ?, content_md = ?, cover_image = ?, published = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
            """,
            (title, slug, content_md, cover_image, 1 if published else 0, post_id),
        )
        conn.commit()


def delete_post(post_id: int) -> None:
    with get_conn() as conn:
        conn.execute("DELETE FROM posts WHERE id = ?", (post_id,))
        conn.commit()