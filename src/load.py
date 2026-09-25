import sqlite3
import json
from datetime import datetime
import pandas as pd
from src.config import DB_PATH


def load_orders(clean_df: pd.DataFrame, rejected_df: pd.DataFrame):
    conn = sqlite3.connect(DB_PATH)
    now = datetime.now().isoformat()

    # Load clean records — REPLACE handles reruns idempotently
    to_load = clean_df.copy()
    to_load["order_date"] = to_load["order_date"].dt.strftime("%Y-%m-%d")
    to_load["loaded_at"] = now
    to_load[[
        "order_id", "customer_id", "product_name", "quantity", "unit_price",
        "currency", "unit_price_usd", "total_value_usd", "order_date", "loaded_at"
    ]].to_sql("fact_orders", conn, if_exists="replace", index=False)

    conn.execute("DELETE FROM rejected_records")  # fresh snapshot each run
    for _, row in rejected_df.iterrows():
        row_dict = row.drop("rejection_reason", errors="ignore").astype(str).to_dict()
        conn.execute(
            "INSERT INTO rejected_records (order_id, customer_id, rejection_reason, raw_row_json, logged_at) VALUES (?, ?, ?, ?, ?)",
            (
                row_dict.get("order_id", ""),
                row_dict.get("customer_id", ""),
                row.get("rejection_reason", ""),
                json.dumps(row_dict),
                now,
            ),
        )

    conn.commit()
    conn.close()


def log_pipeline_run(started_at: str, finished_at: str, duration: float, metrics: dict, status: str, error_message: str = None):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(
        """INSERT INTO pipeline_run_log
           (started_at, finished_at, duration_seconds, rows_extracted, duplicates_removed, rows_rejected, rows_loaded, status, error_message)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            started_at, finished_at, duration,
            metrics.get("rows_extracted"), metrics.get("duplicates_removed"),
            metrics.get("rows_rejected"), metrics.get("rows_loaded"),
            status, error_message,
        ),
    )
    conn.commit()
    conn.close()