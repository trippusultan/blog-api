# ── database layer ──────────────────────────────────────────────────
import os, aiosqlite, json, time
from pathlib import Path

DB_PATH = Path(__file__).parent / "data" / "blog.db"

async def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        await db.execute("""
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title   TEXT NOT NULL,
            content TEXT NOT NULL,
            category TEXT DEFAULT '',
            tags    TEXT DEFAULT '[]',
            created_at TEXT NOT NULL,
            updated_at TEXT NOT NULL
        )""")
        # Seed one sample post if table empty
        cur = await db.execute("SELECT COUNT(*) AS c FROM posts")
        row = await cur.fetchone()
        if row['c'] == 0:
            await db.execute(
                "INSERT INTO posts (title, content, category, tags, created_at, updated_at) VALUES (?,?,?,?,?,?)",
                ("My First Blog Post",
                 "This is the content of my first blog post.",
                 "Technology", '["Tech","Programming"]',
                 "2021-09-01T12:00:00Z",
                 "2021-09-01T12:00:00Z"))
            await db.commit()
        await db.close()

async def fetchall(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        cur = await db.execute(query, params)
        rows = await cur.fetchall()
        return [dict(r) for r in rows]

async def fetchone(query, params=()):
    rows = await fetchall(query, params)
    return rows[0] if rows else None

async def execute(query, params=()):
    async with aiosqlite.connect(DB_PATH) as db:
        cur = await db.execute(query, params)
        await db.commit()
        last_id = cur.lastrowid
        await db.close()
        return last_id

async def execute_many(query, params_list):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.executemany(query, params_list)
        await db.commit()
        await db.close()
