import sqlite3
import json
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "blogy.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS blogs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                keyword TEXT NOT NULL,
                blog_html TEXT NOT NULL,
                outline TEXT,
                seo_score INTEGER,
                word_count INTEGER,
                platform_variants TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        conn.commit()

def save_blog(keyword, blog_html, outline, seo, platform_variants):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO blogs (keyword, blog_html, outline, seo_score, word_count, platform_variants)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (
            keyword, blog_html, outline,
            seo.get("seo_score"), seo.get("word_count"),
            json.dumps(platform_variants)
        ))
        conn.commit()

def get_all_blogs():
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, keyword, seo_score, word_count, created_at FROM blogs ORDER BY created_at DESC LIMIT 50"
        ).fetchall()
        return [dict(r) for r in rows]

def get_blog_by_id(blog_id):
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM blogs WHERE id = ?", (blog_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        d["platform_variants"] = json.loads(d["platform_variants"] or "{}")
        return d