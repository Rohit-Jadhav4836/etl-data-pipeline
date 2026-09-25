import sqlite3
from src.config import DB_PATH

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS fact_orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    product_name TEXT NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    currency TEXT NOT NULL,
    unit_price_usd REAL NOT NULL,
    total_value_usd REAL NOT NULL,
    order_date TEXT NOT NULL,
    loaded_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS rejected_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id TEXT,
    customer_id TEXT,
    rejection_reason TEXT NOT NULL,
    raw_row_json TEXT,
    logged_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS pipeline_run_log (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT NOT NULL,
    duration_seconds REAL NOT NULL,
    rows_extracted INTEGER,
    duplicates_removed INTEGER,
    rows_rejected INTEGER,
    rows_loaded INTEGER,
    status TEXT NOT NULL,
    error_message TEXT
);
"""


def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA_SQL)
    conn.commit()
    conn.close()