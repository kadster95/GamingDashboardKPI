"""Monthly Report page — revenue, player, and deposit trend by calendar month."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from src.database.db_manager import fetch_daily_data, initialize_database
from src.reporting.monthly_report import build_monthly_report
from src.export.exporter import to_csv_bytes, to_excel_bytes
from ui.components.charts import bar_chart, grouped_bar_chart, line_chart
from ui.components.kpi_cards import render_kpi_row

st.set_page_config(page_title="Monthly Report | Casino Analytics", page_icon="🗓️", layout="wide")
initialize_database()

st.title("🗓️ Monthly Report")

df_raw = fetch_daily_data()
if df_raw.empty:
    st.warning("No data found. Upload daily reports in **Data Management**.")
    st.stop()

report = build_monthly_report(df_raw)
monthly_df = report["monthly_df"]
summary = report["summary"]

if monthly_df.empty:
    st.warning("Not enough data to build monthly aggregations.")
    st.stop()

# ---------------------------------------------------------------------------
# KPI cards — latest month
# ---------------------------------------------------------------------------

st.subheader("Latest Month KPIs (MoM)")
render_kpi_row(summary, period_label="vs previous month")

st.markdown("---")

# ---------------------------------------------------------------------------
# Revenue trends
# ---------------------------------------------------------------------------

st.subheader("📊 Revenue Trends")
col1, col2 = st.columns(2)

with col1:
    rev_cols = [c for c in ("ggr", "ngr") if c in monthly_df.columns]
    if rev_cols:
        st.plotly_chart(
            line_chart(monthly_df, "month", rev_cols,
                       labels={"ggr": "GGR", "ngr": "NGR"},
                       title="GGR & NGR by Month"),
            use_container_width=True,
        )

with col2:
    if "bets" in monthly_df.columns:
        st.plotly_chart(
            bar_chart(monthly_df, "month", "bets", title="Total Bets by Month"),
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# Player trends
# ---------------------------------------------------------------------------

st.subheader("👥 Player Trends")
col3, col4 = st.columns(2)

with col3:
    player_cols = [c for c in ("active_players", "new_players") if c in monthly_df.columns]
    if player_cols:
        st.plotly_chart(
            grouped_bar_chart(monthly_df, "month", player_cols,
                              labels={"active_players": "Active", "new_players": "New"},
                              title="Active vs New Players by Month"),
            use_container_width=True,
        )

with col4:
    if "arpu" in monthly_df.columns:
        st.plotly_chart(
            line_chart(monthly_df, "month", ["arpu"],
                       title="ARPU by Month"),
            use_container_width=True,
        )

# ---------------------------------------------------------------------------
# Deposit trends
# ---------------------------------------------------------------------------

st.subheader("💰 Deposit & Withdrawal Trends")
dep_cols = [c for c in ("deposits_amount", "withdrawals_amount") if c in monthly_df.columns]
if dep_cols:
    st.plotly_chart(
        grouped_bar_chart(monthly_df, "month", dep_cols,
                          labels={"deposits_amount": "Deposits", "withdrawals_amount": "Withdrawals"},
                          title="Deposits vs Withdrawals by Month"),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Monthly summary table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📋 Monthly Summary Table")

key_cols = {
    "month": "Month",
    "ggr": "GGR",
    "ggr_mom_pct": "GGR MoM%",
    "ngr": "NGR",
    "ngr_mom_pct": "NGR MoM%",
    "bets": "Bets",
    "active_players": "Active Players",
    "active_players_mom_pct": "Players MoM%",
    "new_players": "New Players",
    "deposits_amount": "Deposits",
    "withdrawals_amount": "Withdrawals",
    "hold_pct": "Hold %",
    "arpu": "ARPU",
}

table_cols = [c for c in key_cols if c in monthly_df.columns]
table_df = monthly_df[table_cols].copy().rename(columns=key_cols)
if "Month" in table_df.columns:
    table_df["Month"] = pd.to_datetime(table_df["Month"]).dt.strftime("%Y-%m")

pct_display_cols = [v for k, v in key_cols.items() if "MoM%" in v and v in table_df.columns]

def _colour_pct(val):
    try:
        v = float(val)
        return "color: #2ECC71" if v > 0 else ("color: #E74C3C" if v < 0 else "")
    except (TypeError, ValueError):
        return ""

st.dataframe(
    table_df.sort_values("Month", ascending=False)
            .style.applymap(_colour_pct, subset=pct_display_cols),
    use_container_width=True,
)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.download_button(
        "⬇️ Export CSV",
        data=to_csv_bytes(monthly_df),
        file_name="monthly_report.csv",
        mime="text/csv",
    )
with col_e2:
    st.download_button(
        "⬇️ Export Excel",
        data=to_excel_bytes({"Monthly Report": monthly_df}),
        file_name="monthly_report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
