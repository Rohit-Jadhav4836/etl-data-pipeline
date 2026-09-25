import logging
import time
from datetime import datetime

from src.config import LOG_PATH
from src.db_schema import init_db
from src.extract import extract_orders_csv, extract_exchange_rates
from src.transform import transform_orders
from src.load import load_orders, log_pipeline_run

logging.basicConfig(
    filename=LOG_PATH,
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)


def run_pipeline() -> dict:
    """Run the full Extract -> Transform -> Load pipeline once.
    Returns the run's metrics dict. Safe to call repeatedly (idempotent load)."""
    init_db()
    started_at = datetime.now()
    t0 = time.time()

    try:
        logging.info("Pipeline run started.")

        raw_df = extract_orders_csv()
        logging.info(f"Extracted {len(raw_df)} rows from CSV.")

        rates = extract_exchange_rates()
        logging.info(f"Fetched exchange rates: {rates}")

        clean_df, rejected_df, metrics = transform_orders(raw_df, rates)
        logging.info(f"Transform complete: {metrics}")

        load_orders(clean_df, rejected_df)
        logging.info(f"Loaded {metrics['rows_loaded']} rows into warehouse.")

        duration = round(time.time() - t0, 2)
        finished_at = datetime.now()
        log_pipeline_run(started_at.isoformat(), finished_at.isoformat(), duration, metrics, status="SUCCESS")

        logging.info(f"Pipeline run finished successfully in {duration}s.")
        metrics["duration_seconds"] = duration
        metrics["status"] = "SUCCESS"
        return metrics

    except Exception as e:
        duration = round(time.time() - t0, 2)
        finished_at = datetime.now()
        logging.error(f"Pipeline run FAILED: {e}")
        log_pipeline_run(started_at.isoformat(), finished_at.isoformat(), duration, {}, status="FAILED", error_message=str(e))
        raise


if __name__ == "__main__":
    result = run_pipeline()
    print(result)