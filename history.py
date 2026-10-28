"""
Arjun's memory of everything you both said. Stored in a small database file
(history.db) using SQLite, which comes built into Python.
"""
import sqlite3
import datetime
from contextlib import closing

import config

DB_FILE = config.DATA_DIR / "history.db"


def _connect():
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS messages "
        "(id INTEGER PRIMARY KEY, ts TEXT, role TEXT, text TEXT)"
    )
    return conn


def log(role: str, text: str) -> None:
    """Save one message ('user' or 'assistant')."""
    if not text:
        return
    ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")
    with closing(_connect()) as conn:
        conn.execute("INSERT INTO messages (ts, role, text) VALUES (?, ?, ?)", (ts, role, text))
        conn.commit()


def search(query: str, limit: int = 8):
    """Find past messages containing ALL the words in the query (also matches dates like 2026-10-25)."""
    words = query.split()
    if not words:
        return recent(limit)
    clause = " AND ".join(["(text || ' ' || ts) LIKE ? ESCAPE '\\'"] * len(words))
    params = ["%" + w.replace("\\", "\\\\").replace("%", "\\%").replace("_", "\\_") + "%" for w in words]
    with closing(_connect()) as conn:
        rows = conn.execute(
            f"SELECT ts, role, text FROM messages WHERE {clause} ORDER BY id DESC LIMIT ?",
            params + [int(limit)],
        ).fetchall()
    return rows


def recent(limit: int = 10):
    with closing(_connect()) as conn:
        rows = conn.execute(
            "SELECT ts, role, text FROM messages ORDER BY id DESC LIMIT ?", (int(limit),)
        ).fetchall()
    return rows


def format_rows(rows) -> str:
    if not rows:
        return "Nothing found."
    lines = []
    for ts, role, text in rows:
        who = "You" if role == "user" else "Arjun"
        short = text if len(text) <= 300 else text[:300] + "..."
        lines.append(f"[{ts}] {who}: {short}")
    return "\n".join(lines)
