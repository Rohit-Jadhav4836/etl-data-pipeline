# ETL Data Pipeline with Monitoring Dashboard

A complete Extract-Transform-Load pipeline that ingests order data from a messy CSV export and a live public API, applies real data-quality validation, and loads it into a SQLite warehouse — with a monitoring dashboard for running and observing pipeline health.

🔗 **Live Demo:** https://etl-data-pipeline-nknqzkjtmtstwnqbjycbbs.streamlit.app/

** Dashboard Preview ** : 

<img width="1917" height="902" alt="Screenshot 2026-09-26 033453" src="https://github.com/user-attachments/assets/8b5a06fc-528e-475f-bd37-b47739896c36" />
<img width="1911" height="896" alt="Screenshot 2026-09-26 033510" src="https://github.com/user-attachments/assets/be1a1fef-7286-451b-9067-9746c9d8290a" />
<img width="1897" height="901" alt="Screenshot 2026-09-26 033524" src="https://github.com/user-attachments/assets/736daadc-4140-4e5f-bc77-74a6fd449844" />
<img width="1917" height="910" alt="Screenshot 2026-09-26 033536" src="https://github.com/user-attachments/assets/835a32b7-c4e2-49e6-b64d-c5c35aa23fe1" />
<img width="1912" height="901" alt="Screenshot 2026-09-26 033548" src="https://github.com/user-attachments/assets/a9502868-db42-4e27-990a-6d5e302b8928" />

## Overview

This project demonstrates a genuine data engineering workflow rather than a toy script: the pipeline (`src/pipeline.py`) is a fully standalone, runnable module with zero dependency on the Streamlit UI. It can be triggered from the command line, scheduled via cron/Airflow in a real deployment, or run from the dashboard — the UI is purely a monitoring/control layer on top of it.

Part of a Data Analytics / Data Science / Data Engineering portfolio built during certification with IT Vedant.

## Architecture

EXTRACT TRANSFORM LOAD
├─ CSV (legacy export) → ├─ Deduplicate → ├─ fact_orders (SQLite)
└─ Live exchange rate API ├─ Standardize mixed date fmts ├─ rejected_records (audit)
├─ Validate business rules └─ pipeline_run_log (audit)
├─ Reject bad rows (not drop!)
└─ Enrich: currency → USD


## Features

- **Multi-source extraction**: a messy legacy-style CSV + a live public currency exchange rate API (with automatic fallback if the API is unreachable)
- **Real data-quality rules**: rejects (never silently drops) rows with missing customer IDs, invalid quantities/prices, unrecognized currencies, or unparseable dates — every rejection is logged with its reason
- **Mixed date format handling**: source data intentionally includes 4 different date formats, standardized during transform
- **Currency enrichment**: every order's value is converted to USD using real-time exchange rates
- **Idempotent loading**: reruns replace the warehouse table cleanly rather than duplicating data
- **Full audit trail**: every pipeline run is logged (duration, rows extracted/rejected/loaded, status, errors) in its own table
- **Live SQL query interface**: run ad-hoc SQL directly against the warehouse from the dashboard
- **Pipeline Control Center UI**: DAG-style visual, status pills, live log console

## Tech Stack

| Category | Tools |
|---|---|
| Language | Python 3.11 |
| Data | pandas |
| Database | SQLite |
| API | requests (live exchange rate data) |
| Web App | Streamlit |
| Logging | Python `logging` module |

## Project Structure

etl-data-pipeline/
├── data/
│ ├── raw/
│ │ └── orders_export.csv
│ └── warehouse.db # generated at runtime, not committed
├── src/
│ ├── config.py
│ ├── extract.py
│ ├── transform.py
│ ├── load.py
│ ├── pipeline.py # standalone orchestrator
│ └── db_schema.py
├── logs/
│ └── pipeline_runs.log
├── assets/
│ └── style.css
├── app.py # monitoring dashboard
├── requirements.txt
└── README.md


## Data Quality Rules

| Rule | Rejection Reason |
|---|---|
| Missing customer ID | `missing_customer_id` |
| Quantity ≤ 0 or null | `invalid_quantity` |
| Unit price ≤ 0 or null | `invalid_unit_price` |
| Currency not in {USD, EUR, GBP, INR, AUD} | `unrecognized_currency` |
| Unparseable date (any of 4 known formats fails) | `unparseable_date` |

Rejected rows are stored with their full original data and reason — never discarded — matching how real data quality monitoring works.

## Run Locally

```bash
git clone https://github.com/<your-username>/etl-data-pipeline.git
cd etl-data-pipeline
python -m venv venv
venv\Scripts\activate        # Windows
pip install -r requirements.txt
```

Run the pipeline standalone (no UI needed):
```bash
python -m src.pipeline
```

Or launch the monitoring dashboard:
```bash
streamlit run app.py
```

## What I Learned

- Structuring an ETL pipeline as fully decoupled from its UI — the same pattern used in production data engineering (a pipeline that could be scheduled by Airflow/cron, with a dashboard as a separate monitoring layer)
- Handling multi-format date parsing and mixed-quality real-world-style data without silently dropping records
- Designing idempotent loads (safe to rerun) and a proper audit trail schema (`pipeline_run_log`) — standard practice for debugging pipeline failures in production
- Building resilient API extraction with a fallback path, since real pipelines can't fail just because one external API call times out
