import pandas as pd
import requests
from src.config import RAW_CSV_PATH, EXCHANGE_RATE_API_URL


def extract_orders_csv() -> pd.DataFrame:
    """Extract raw order records from the legacy CSV export."""
    df = pd.read_csv(RAW_CSV_PATH, dtype={"customer_id": str})
    return df


def extract_exchange_rates() -> dict:
    """Extract live currency exchange rates from a public REST API.
    Falls back to fixed rates if the API is unreachable, so the pipeline
    never fails hard on a network hiccup — a real production consideration."""
    fallback_rates = {"USD": 1.0, "EUR": 0.92, "GBP": 0.79, "INR": 83.1, "AUD": 1.52}
    try:
        response = requests.get(EXCHANGE_RATE_API_URL, timeout=8)
        response.raise_for_status()
        data = response.json()
        rates = data.get("rates", {})
        return {cur: rates.get(cur, fallback_rates[cur]) for cur in fallback_rates}
    except (requests.RequestException, ValueError, KeyError):
        return fallback_rates