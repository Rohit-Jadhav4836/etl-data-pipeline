import streamlit as st
import pandas as pd
import sqlite3
import os
from src.pipeline import run_pipeline
from src.config import DB_PATH, LOG_PATH

st.set_page_config(page_title="ETL Pipeline Control Center", layout="wide")

def load_css(path: str = "assets/style.css"):
    with open(path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)

load_css()

def get_conn():
    return sqlite3.connect(DB_PATH)

def table_exists(conn, name: str) -> bool:
    q = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone()
    return q is not None

st.title("ETL PIPELINE CONTROL CENTER")
st.caption("Extract (CSV + live exchange rate API) → Transform (validation, dedup, currency enrichment) → Load (SQLite warehouse) — fully decoupled from this dashboard")

st.markdown('''
<div class="dag-container">
    <div class="dag-node extract"><div class="dag-icon">📥</div><div class="dag-label">EXTRACT</div></div>
    <div class="dag-arrow">→</div>
    <div class="dag-node transform"><div class="dag-icon">⚙️</div><div class="dag-label">TRANSFORM</div></div>
    <div class="dag-arrow">→</div>
    <div class="dag-node load"><div class="dag-icon">📦</div><div class="dag-label">LOAD</div></div>
</div>
''', unsafe_allow_html=True)

col_run, col_status = st.columns([1, 3])
with col_run:
    run_clicked = st.button("▶ Run Pipeline Now", use_container_width=True)

if run_clicked:
    with st.spinner("Running pipeline..."):
        try:
            result = run_pipeline()
            st.success(f"Pipeline completed: {result['rows_loaded']} rows loaded, {result['rows_rejected']} rejected, in {result['duration_seconds']}s")
        except Exception as e:
            st.error(f"Pipeline failed: {e}")

if not os.path.exists(DB_PATH):
    st.info("No pipeline run yet. Click 'Run Pipeline Now' to initialize the warehouse.")
    st.stop()

conn = get_conn()

if not table_exists(conn, "pipeline_run_log") or pd.read_sql("SELECT COUNT(*) as c FROM pipeline_run_log", conn)["c"][0] == 0:
    st.info("No pipeline runs logged yet. Click 'Run Pipeline Now' above.")
    st.stop()

runs = pd.read_sql("SELECT * FROM pipeline_run_log ORDER BY run_id DESC", conn)
latest = runs.iloc[0]

st.divider()

status_class = "success" if latest["status"] == "SUCCESS" else "failed"
st.markdown(f'<span class="status-pill {status_class}">{latest["status"]}</span> &nbsp; Last run: {latest["finished_at"]}', unsafe_allow_html=True)

c1, c2, c3, c4 = st.columns(4)
c1.metric("Rows Extracted", int(latest["rows_extracted"]) if pd.notna(latest["rows_extracted"]) else "—")
c2.metric("Duplicates Removed", int(latest["duplicates_removed"]) if pd.notna(latest["duplicates_removed"]) else "—")
c3.metric("Rows Rejected", int(latest["rows_rejected"]) if pd.notna(latest["rows_rejected"]) else "—")
c4.metric("Rows Loaded", int(latest["rows_loaded"]) if pd.notna(latest["rows_loaded"]) else "—")

st.divider()

tab1, tab2, tab3, tab4 = st.tabs(["Warehouse Data", "Rejected Records", "Run History", "Pipeline Logs"])

with tab1:
    st.markdown("**Run a SQL query against the warehouse:**")
    default_query = "SELECT * FROM fact_orders ORDER BY total_value_usd DESC LIMIT 100"
    query = st.text_area("SQL Query", value=default_query, height=80)
    if st.button("Run Query"):
        try:
            result_df = pd.read_sql(query, conn)
            st.dataframe(result_df, use_container_width=True)
            st.caption(f"{len(result_df)} rows returned")
        except Exception as e:
            st.error(f"Query error: {e}")

with tab2:
    rejected = pd.read_sql("SELECT * FROM rejected_records ORDER BY id DESC", conn)
    if rejected.empty:
        st.success("No rejected records in the last run.")
    else:
        reason_counts = rejected["rejection_reason"].str.get_dummies(sep=";").sum().sort_values(ascending=False)
        st.bar_chart(reason_counts)
        st.dataframe(rejected, use_container_width=True)

with tab3:
    st.dataframe(runs, use_container_width=True)
    if len(runs) > 1:
        st.line_chart(runs.set_index("run_id")[["rows_loaded", "rows_rejected"]].iloc[::-1])

with tab4:
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH) as f:
            log_content = f.read()
        recent_logs = "\n".join(log_content.splitlines()[-60:])
        st.markdown(f'<div class="log-console">{recent_logs}</div>', unsafe_allow_html=True)
    else:
        st.info("No log file yet.")

conn.close()