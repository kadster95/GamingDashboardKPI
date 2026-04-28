"""
Casino Analytics Dashboard — main entry point / Overview page.

Run with:  streamlit run app.py
"""

import sys
from pathlib import Path

# Make sure src/ and ui/ are importable regardless of cwd
ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from config import DEFAULT_DATE_RANGE_DAYS
from src.database.db_manager import (
    fetch_daily_data,
    get_data_summary,
    initialize_database,
)
from src.metrics.anomaly_detector import anomalies_to_df, detect_daily_anomalies
from src.metrics.kpi_calculator import compute_kpis
from src.metrics.trends import add_dod_changes
from src.forecasting.rolling_forecast import add_rolling_averages, forecast_forward
from ui.components.charts import area_chart, forecast_chart, line_chart
from ui.components.kpi_cards import render_kpi_card, render_kpi_row

# ---------------------------------------------------------------------------
# Page config
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Casino Analytics",
    page_icon="🎰",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Bootstrap DB
# ---------------------------------------------------------------------------

initialize_database()

# ---------------------------------------------------------------------------
# Sidebar — date filter
# ---------------------------------------------------------------------------

st.sidebar.title("🎰 Casino Analytics")
st.sidebar.markdown("---")

summary = get_data_summary()
if summary["min_date"] and summary["max_date"]:
    data_min = date.fromisoformat(summary["min_date"])
    data_max = date.fromisoformat(summary["max_date"])
else:
    data_min = date.today() - timedelta(days=DEFAULT_DATE_RANGE_DAYS)
    data_max = date.today()

with st.sidebar:
    st.subheader("Date Range")
    start_date = st.date_input("From", value=data_max - timedelta(days=DEFAULT_DATE_RANGE_DAYS - 1), min_value=data_min, max_value=data_max)
    end_date   = st.date_input("To",   value=data_max, min_value=data_min, max_value=data_max)

    st.markdown("---")
    st.caption(
        f"📦 {summary['daily_records']} daily records | "
        f"🎮 {summary['game_records']} game records"
    )
    if summary["min_date"]:
        st.caption(f"Range: {summary['min_date']} → {summary['max_date']}")

# ---------------------------------------------------------------------------
# Load data
# ---------------------------------------------------------------------------

df_raw = fetch_daily_data(
    start_date=str(start_date),
    end_date=str(end_date),
)

# ---------------------------------------------------------------------------
# Header
# ---------------------------------------------------------------------------

st.title("🎰 Casino Analytics — Overview")
st.markdown(f"**Period:** {start_date} → {end_date}")

if df_raw.empty:
    st.warning(
        "No data found for the selected period. "
        "Go to **Data Management** to upload daily reports or enter data manually."
    )
    st.stop()

# ---------------------------------------------------------------------------
# KPI computation
# ---------------------------------------------------------------------------

df = compute_kpis(df_raw.copy())
df = add_dod_changes(df)
df = add_rolling_averages(df)

# Build DoD summary from last two rows for the KPI cards
from src.metrics.trends import get_dod_summary
dod = get_dod_summary(df)

# ---------------------------------------------------------------------------
# KPI Cards (top row)
# ---------------------------------------------------------------------------

st.subheader("Key Performance Indicators")
render_kpi_row(dod, period_label="vs previous day")

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts — two columns
# ---------------------------------------------------------------------------

col_left, col_right = st.columns(2)

with col_left:
    if "ggr" in df.columns:
        st.plotly_chart(
            area_chart(df, x="date", y="ggr", title="GGR Trend", color="primary"),
            use_container_width=True,
        )

with col_right:
    if "active_players" in df.columns:
        st.plotly_chart(
            area_chart(df, x="date", y="active_players", title="Active Players", color="info"),
            use_container_width=True,
        )

# Revenue decomposition line chart
rev_cols = [c for c in ("ggr", "ngr", "bets") if c in df.columns]
if rev_cols:
    st.plotly_chart(
        line_chart(
            df,
            x="date",
            y_cols=rev_cols,
            labels={"ggr": "GGR", "ngr": "NGR", "bets": "Bets"},
            title="Revenue Decomposition",
        ),
        use_container_width=True,
    )

# Player trend
player_cols = [c for c in ("active_players", "new_players") if c in df.columns]
if player_cols:
    st.plotly_chart(
        line_chart(
            df,
            x="date",
            y_cols=player_cols,
            labels={"active_players": "Active", "new_players": "New"},
            title="Player Trends",
        ),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Forecast section
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📈 GGR Forecast (Rolling Average Projection)")
forecast_df = forecast_forward(df)
if not forecast_df.empty and "ggr" in df.columns:
    st.plotly_chart(
        forecast_chart(df, forecast_df, "ggr", title="GGR — Actuals + Forecast"),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Anomaly panel
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("⚠️ Anomaly Alerts")

anomalies = detect_daily_anomalies(df)
anom_df = anomalies_to_df(anomalies)

if anom_df.empty:
    st.success("No anomalies detected in the selected period.")
else:
    st.warning(f"{len(anom_df)} anomaly / anomalies detected (≥30% DoD change).")

    def _colour_direction(val: str) -> str:
        if val == "SPIKE":
            return "color: #2ECC71"
        if val == "DROP":
            return "color: #E74C3C"
        return ""

    st.dataframe(
        anom_df.style.applymap(_colour_direction, subset=["direction"]),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Raw data table (expandable)
# ---------------------------------------------------------------------------

with st.expander("📋 Raw Daily Data"):
    display_df = df_raw.copy()
    if "date" in display_df.columns:
        display_df["date"] = display_df["date"].dt.strftime("%Y-%m-%d")
    st.dataframe(display_df, use_container_width=True)
