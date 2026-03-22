import os
import sqlite3
from pathlib import Path

from app.config import settings

SEED_DEFENDERS = [
    ("nasir",    "U46cOr50ZgYm",  87385),
    ("yogi",     "B6ljBvTXwjba",  91780),
    ("vamboge",  "x3gZjX6cU",     90868),
    ("nghich",   "geKKZH7Z00MY",  94033),
    ("yingyang", "DOiW3XREBkDI",  87450),
    ("lick",     "s8cjblcSGByG",  95224),
    ("tear",     "UBpeDNvDNZ61",  96415),
    ("butter",   "qLpVJEsmZDqN",  91941),
]

SCHEMA = """
CREATE TABLE IF NOT EXISTS defenders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,
    code TEXT,
    comp TEXT DEFAULT '',
    trophies INTEGER,
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS officers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL COLLATE NOCASE,
    provider TEXT NOT NULL DEFAULT 'local',
    external_id TEXT,
    comp TEXT DEFAULT '',
    ricky_replaces TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    UNIQUE(provider, external_id)
);

CREATE TABLE IF NOT EXISTS matchups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    officer_id INTEGER NOT NULL REFERENCES officers(id),
    defender_id INTEGER NOT NULL REFERENCES defenders(id) ON DELETE CASCADE,
    wins_control INTEGER NOT NULL DEFAULT 0,
    wins_ricky INTEGER NOT NULL DEFAULT 0,
    losses_control INTEGER NOT NULL DEFAULT 0,
    losses_ricky INTEGER NOT NULL DEFAULT 0,
    order_first TEXT NOT NULL DEFAULT 'control',
    notes TEXT DEFAULT '',
    updated_at TEXT DEFAULT (datetime('now')),
    UNIQUE(officer_id, defender_id)
);
"""


def get_db_path() -> str:
    if settings.DATABASE_PATH:
        return settings.DATABASE_PATH
    if os.path.isdir("/var/data"):
        return "/var/data/data.db"
    Path("data").mkdir(exist_ok=True)
    return "data/data.db"


def get_connection() -> sqlite3.Connection:
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def migrate_db(conn):
    cols = {r[1] for r in conn.execute("PRAGMA table_info(defenders)")}
    if "trophies" not in cols:
        conn.execute("ALTER TABLE defenders ADD COLUMN trophies INTEGER")
    cols = {r[1] for r in conn.execute("PRAGMA table_info(matchups)")}
    if "losses_control" not in cols:
        conn.execute("ALTER TABLE matchups ADD COLUMN losses_control INTEGER NOT NULL DEFAULT 0")
    if "losses_ricky" not in cols:
        conn.execute("ALTER TABLE matchups ADD COLUMN losses_ricky INTEGER NOT NULL DEFAULT 0")
    conn.commit()


def init_db():
    conn = get_connection()
    conn.executescript(SCHEMA)
    conn.commit()
    migrate_db(conn)
    seed_defenders(conn)
    conn.close()


def seed_defenders(conn: sqlite3.Connection):
    conn.executemany(
        "INSERT OR IGNORE INTO defenders (name, code, trophies) VALUES (?, ?, ?)",
        SEED_DEFENDERS,
    )
    for name, _, trophies in SEED_DEFENDERS:
        conn.execute(
            "UPDATE defenders SET trophies = ? WHERE name = ? AND trophies IS NULL",
            (trophies, name),
        )
    conn.commit()
