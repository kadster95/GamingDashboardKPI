"""Weekly Report page — WoW aggregations, trend charts, top/bottom weeks."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import pandas as pd

from src.database.db_manager import fetch_daily_data, initialize_database
from src.reporting.weekly_report import build_weekly_report
from src.export.exporter import to_csv_bytes, to_excel_bytes
from ui.components.charts import grouped_bar_chart, line_chart
from ui.components.kpi_cards import render_kpi_row

st.set_page_config(page_title="Weekly Report | Casino Analytics", page_icon="📆", layout="wide")
initialize_database()

# ---------------------------------------------------------------------------
# Header & data load
# ---------------------------------------------------------------------------

st.title("📆 Weekly Report")

df_raw = fetch_daily_data()
if df_raw.empty:
    st.warning("No data found. Upload daily reports in **Data Management**.")
    st.stop()

report = build_weekly_report(df_raw)
weekly_df = report["weekly_df"]
summary = report["summary"]

if weekly_df.empty:
    st.warning("Not enough data to compute weekly aggregations.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI cards — latest week vs previous week
# ---------------------------------------------------------------------------

st.subheader("Latest Week KPIs (WoW)")
render_kpi_row(summary, period_label="vs previous week")

st.markdown("---")

# ---------------------------------------------------------------------------
# Charts
# ---------------------------------------------------------------------------

col1, col2 = st.columns(2)

with col1:
    if "ggr" in weekly_df.columns:
        st.plotly_chart(
            line_chart(weekly_df, "week", ["ggr", "ngr"],
                       labels={"ggr": "GGR", "ngr": "NGR"},
                       title="GGR & NGR by Week"),
            use_container_width=True,
        )

with col2:
    if "active_players" in weekly_df.columns:
        st.plotly_chart(
            line_chart(weekly_df, "week", ["active_players", "new_players"],
                       labels={"active_players": "Active", "new_players": "New"},
                       title="Players by Week"),
            use_container_width=True,
        )

col3, col4 = st.columns(2)

with col3:
    if "deposits_amount" in weekly_df.columns:
        st.plotly_chart(
            grouped_bar_chart(
                weekly_df, "week",
                ["deposits_amount", "withdrawals_amount"],
                labels={"deposits_amount": "Deposits", "withdrawals_amount": "Withdrawals"},
                title="Deposits vs Withdrawals by Week",
            ),
            use_container_width=True,
        )

with col4:
    if "hold_pct" in weekly_df.columns:
        st.plotly_chart(
            line_chart(weekly_df, "week", ["hold_pct"],
                       title="Hold % by Week",
                       yaxis_format=".2f"),
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# WoW change table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📋 Week-over-Week Changes")

display_cols = {
    "week": "Week Start",
    "ggr": "GGR",
    "ggr_wow_pct": "GGR WoW %",
    "ngr": "NGR",
    "ngr_wow_pct": "NGR WoW %",
    "bets": "Bets",
    "bets_wow_pct": "Bets WoW %",
    "active_players": "Active Players",
    "active_players_wow_pct": "Players WoW %",
    "deposits_amount": "Deposits",
    "deposits_amount_wow_pct": "Deposits WoW %",
}

table_cols = [c for c in display_cols if c in weekly_df.columns]
table_df = weekly_df[table_cols].copy()
table_df = table_df.rename(columns=display_cols)
if "Week Start" in table_df.columns:
    table_df["Week Start"] = pd.to_datetime(table_df["Week Start"]).dt.strftime("%Y-%m-%d")

# Colour WoW % columns
pct_cols = [v for k, v in display_cols.items() if "WoW" in v and v in table_df.columns]

def _colour_pct(val):
    try:
        v = float(val)
        if v > 0:
            return "color: #2ECC71"
        if v < 0:
            return "color: #E74C3C"
    except (TypeError, ValueError):
        pass
    return ""

st.dataframe(
    table_df.sort_values("Week Start", ascending=False)
            .style.applymap(_colour_pct, subset=pct_cols),
    use_container_width=True,
)

# Top / bottom 3 weeks by GGR
if "ggr" in weekly_df.columns and len(weekly_df) >= 3:
    st.markdown("---")
    col_top, col_bot = st.columns(2)
    with col_top:
        st.subheader("🏆 Top 3 Weeks by GGR")
        top3 = weekly_df.nlargest(3, "ggr")[["week", "ggr"]].copy()
        top3["week"] = pd.to_datetime(top3["week"]).dt.strftime("%Y-%m-%d")
        st.dataframe(top3, use_container_width=True, hide_index=True)
    with col_bot:
        st.subheader("⚠️ Bottom 3 Weeks by GGR")
        bot3 = weekly_df.nsmallest(3, "ggr")[["week", "ggr"]].copy()
        bot3["week"] = pd.to_datetime(bot3["week"]).dt.strftime("%Y-%m-%d")
        st.dataframe(bot3, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📤 Export")
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.download_button(
        "⬇️ Export CSV",
        data=to_csv_bytes(weekly_df),
        file_name="weekly_report.csv",
        mime="text/csv",
    )
with col_e2:
    st.download_button(
        "⬇️ Export Excel",
        data=to_excel_bytes({"Weekly Report": weekly_df}),
        file_name="weekly_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
