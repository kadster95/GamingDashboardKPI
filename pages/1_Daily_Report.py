"""Daily Report page — latest day metrics, DoD changes, anomaly highlights."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date

import streamlit as st

from src.database.db_manager import fetch_daily_data, initialize_database
from src.metrics.kpi_calculator import compute_kpis
from src.metrics.anomaly_detector import anomalies_to_df, detect_daily_anomalies
from src.metrics.trends import add_dod_changes, get_dod_summary
from src.reporting.daily_report import build_daily_report
from src.export.exporter import to_csv_bytes, to_excel_bytes
from ui.components.charts import line_chart, bar_chart
from ui.components.kpi_cards import render_kpi_row

st.set_page_config(page_title="Daily Report | Casino Analytics", page_icon="📅", layout="wide")
initialize_database()

# ---------------------------------------------------------------------------
# Sidebar controls
# ---------------------------------------------------------------------------

st.sidebar.title("📅 Daily Report")

all_data = fetch_daily_data()
if all_data.empty:
    st.warning("No data in database. Upload or enter data in **Data Management**.")
    st.stop()

available_dates = sorted(all_data["date"].dt.date.tolist(), reverse=True)
selected_date = st.sidebar.selectbox(
    "Select date",
    options=available_dates,
    format_func=lambda d: d.strftime("%Y-%m-%d (%A)"),
)

# ---------------------------------------------------------------------------
# Build report
# ---------------------------------------------------------------------------

report = build_daily_report(all_data, target_date=str(selected_date))

st.title(f"📅 Daily Report — {selected_date.strftime('%B %d, %Y')}")

# ---------------------------------------------------------------------------
# KPI cards
# ---------------------------------------------------------------------------

st.subheader("KPIs vs Previous Day")
render_kpi_row(report["kpis"], period_label="vs yesterday")

st.markdown("---")

# ---------------------------------------------------------------------------
# Anomaly alerts for this day
# ---------------------------------------------------------------------------

anom_df = report["anomalies"]
if anom_df.empty:
    st.success("✅ No anomalies detected for this day.")
else:
    for _, row in anom_df.iterrows():
        colour = "#2ECC71" if row["direction"] == "SPIKE" else "#E74C3C"
        icon = "📈" if row["direction"] == "SPIKE" else "📉"
        st.markdown(
            f"<div style='padding:8px;border-left:4px solid {colour};margin-bottom:6px;'>"
            f"{icon} <b>{row['metric']}</b>: {row['direction']} of "
            f"<b>{row['pct_change']:+.1f}%</b> on {row['date']}</div>",
            unsafe_allow_html=True,
        )

st.markdown("---")

# ---------------------------------------------------------------------------
# 30-day trend charts
# ---------------------------------------------------------------------------

trend_df = report["trend_df"]

if not trend_df.empty:
    st.subheader("30-Day Trend")

    col1, col2 = st.columns(2)
    with col1:
        if "ggr" in trend_df.columns:
            st.plotly_chart(
                line_chart(trend_df, "date", ["ggr"], title="GGR Trend"),
                use_container_width=True,
            )
    with col2:
        if "active_players" in trend_df.columns:
            st.plotly_chart(
                line_chart(trend_df, "date", ["active_players"], title="Active Players"),
                use_container_width=True,
            )

    col3, col4 = st.columns(2)
    with col3:
        if "deposits_amount" in trend_df.columns:
            st.plotly_chart(
                line_chart(trend_df, "date", ["deposits_amount", "withdrawals_amount"],
                           title="Deposits vs Withdrawals"),
                use_container_width=True,
            )
    with col4:
        if "hold_pct" in trend_df.columns:
            st.plotly_chart(
                line_chart(trend_df, "date", ["hold_pct"], title="Hold % Trend"),
                use_container_width=True,
            )

# ---------------------------------------------------------------------------
# Detailed metrics table for selected day
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📋 Full Metrics for Selected Day")

kpis = report["kpis"]
if kpis:
    rows = []
    label_map = {
        "ggr": "GGR", "ngr": "NGR", "bets": "Bets / Turnover",
        "wins": "Wins", "bonuses": "Bonuses",
        "hold_pct": "Hold %", "arpu": "ARPU",
        "active_players": "Active Players", "new_players": "New Players",
        "deposits_amount": "Deposits Amount", "deposits_count": "Deposits Count",
        "withdrawals_amount": "Withdrawals Amount", "withdrawals_count": "Withdrawals Count",
    }
    for key, info in kpis.items():
        label = label_map.get(key, key.replace("_", " ").title())
        pct = info.get("pct_change")
        rows.append({
            "Metric": label,
            "Today": info.get("current"),
            "Yesterday": info.get("previous"),
            "Change %": f"{pct:+.2f}%" if pct is not None else "—",
        })
    import pandas as pd
    st.dataframe(pd.DataFrame(rows), use_container_width=True)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📤 Export")

if not trend_df.empty:
    col_e1, col_e2 = st.columns(2)
    with col_e1:
        st.download_button(
            "⬇️ Export CSV",
            data=to_csv_bytes(trend_df),
            file_name=f"daily_report_{selected_date}.csv",
            mime="text/csv",
        )
    with col_e2:
        st.download_button(
            "⬇️ Export Excel",
            data=to_excel_bytes({"Daily Trend": trend_df}),
            file_name=f"daily_report_{selected_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )
