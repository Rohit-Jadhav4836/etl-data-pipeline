import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_CSV_PATH = os.path.join(BASE_DIR, "data", "raw", "orders_export.csv")
DB_PATH = os.path.join(BASE_DIR, "data", "warehouse.db")

LOG_DIR = os.path.join(BASE_DIR, "logs")
os.makedirs(LOG_DIR, exist_ok=True)

LOG_PATH = os.path.join(LOG_DIR, "pipeline_runs.log")

# Public, no-API-key-required exchange rate API
EXCHANGE_RATE_API_URL = "https://open.er-api.com/v6/latest/USD"

VALID_CURRENCIES = {"USD", "EUR", "GBP", "INR", "AUD"}