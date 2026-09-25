import pandas as pd
from src.config import VALID_CURRENCIES


def transform_orders(raw_df: pd.DataFrame, exchange_rates: dict) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """
    Clean, validate, deduplicate, and enrich the raw orders data.
    Returns (clean_df, rejected_df, metrics_dict) — rejected rows are
    kept and logged, never silently dropped, as a real data pipeline should.
    """
    df = raw_df.copy()
    metrics = {"rows_extracted": len(df)}

    # 1. Deduplicate exact duplicate rows
    before = len(df)
    df = df.drop_duplicates()
    metrics["duplicates_removed"] = before - len(df)

    # 2. Standardize inconsistent date formats into a single ISO format
    def parse_flexible_date(val):
        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m-%d-%Y", "%Y/%m/%d"):
            try:
                return pd.to_datetime(val, format=fmt)
            except (ValueError, TypeError):
                continue
        return pd.NaT

    df["order_date"] = df["order_date"].apply(parse_flexible_date)

    # 3. Build a rejection mask — rows failing ANY business rule get flagged
    rejection_reasons = pd.Series([""] * len(df), index=df.index)

    blank_customer = df["customer_id"].isna() | (df["customer_id"].str.strip() == "")
    rejection_reasons = rejection_reasons.where(~blank_customer, rejection_reasons + "missing_customer_id;")

    bad_quantity = df["quantity"].isna() | (df["quantity"] <= 0)
    rejection_reasons = rejection_reasons.where(~bad_quantity, rejection_reasons + "invalid_quantity;")

    bad_price = df["unit_price"].isna() | (df["unit_price"] <= 0)
    rejection_reasons = rejection_reasons.where(~bad_price, rejection_reasons + "invalid_unit_price;")

    bad_currency = ~df["currency"].isin(VALID_CURRENCIES)
    rejection_reasons = rejection_reasons.where(~bad_currency, rejection_reasons + "unrecognized_currency;")

    bad_date = df["order_date"].isna()
    rejection_reasons = rejection_reasons.where(~bad_date, rejection_reasons + "unparseable_date;")

    is_rejected = rejection_reasons != ""

    rejected_df = df[is_rejected].copy()
    rejected_df["rejection_reason"] = rejection_reasons[is_rejected]

    clean_df = df[~is_rejected].copy()

    # 4. Enrich: convert every order's value into USD using live exchange rates
    clean_df["unit_price_usd"] = clean_df.apply(
        lambda row: round(row["unit_price"] / exchange_rates.get(row["currency"], 1.0), 2), axis=1
    )
    clean_df["total_value_usd"] = round(clean_df["quantity"] * clean_df["unit_price_usd"], 2)

    metrics["rows_rejected"] = len(rejected_df)
    metrics["rows_loaded"] = len(clean_df)

    return clean_df, rejected_df, metrics