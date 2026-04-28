"""Month-over-Month analysis page — side-by-side KPI comparison."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import streamlit as st

from src.database.db_manager import fetch_daily_data, initialize_database
from src.reporting.mom_analysis import build_mom_analysis
from src.export.exporter import to_csv_bytes, to_excel_bytes
from ui.components.charts import mom_comparison_bar

st.set_page_config(page_title="MoM Analysis | Casino Analytics", page_icon="📈", layout="wide")
initialize_database()

st.title("📈 Month-over-Month Analysis")

df_raw = fetch_daily_data()
if df_raw.empty:
    st.warning("No data found. Upload daily reports in **Data Management**.")
    st.stop()

analysis = build_mom_analysis(df_raw)
comparison_df = analysis["comparison_df"]
monthly_df = analysis["monthly_df"]
current_month, previous_month = analysis["months"]

if comparison_df.empty:
    st.warning("Need at least two months of data for MoM analysis.")
    st.stop()

# ---------------------------------------------------------------------------
# Month labels
# ---------------------------------------------------------------------------

st.markdown(
    f"Comparing **{current_month}** (current) vs **{previous_month}** (previous)"
)

st.markdown("---")

# ---------------------------------------------------------------------------
# Comparison table with coloured % change
# ---------------------------------------------------------------------------

st.subheader("KPI Comparison Table")


def _style_row(row):
    styles = [""] * len(row)
    pct_idx = list(row.index).index("Change %") if "Change %" in row.index else -1
    if pct_idx >= 0:
        val = row["Change %"]
        try:
            v = float(val)
            colour = "#2ECC71" if v > 0 else "#E74C3C"
            styles[pct_idx] = f"color: {colour}; font-weight: bold"
        except (TypeError, ValueError):
            pass
    return styles


display_df = comparison_df.copy()

# Format currency columns nicely
for col in ("Current Month", "Previous Month"):
    display_df[col] = display_df[col].apply(
        lambda v: f"{v:,.2f}" if pd.notna(v) else "—"
    )

display_df["Change %"] = comparison_df["Change %"].apply(
    lambda v: f"{v:+.2f}%" if pd.notna(v) else "—"
)

st.dataframe(
    display_df.style.apply(_style_row, axis=1),
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------------------------
# Bar chart comparison
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📊 Visual Comparison")

# Filter to revenue metrics only for the chart (skip player counts etc.)
rev_kpis = ["GGR", "NGR", "Bets / Turnover", "Bonuses", "Deposits (Amount)", "Withdrawals (Amount)"]
chart_df = comparison_df[comparison_df["KPI"].isin(rev_kpis)].copy()

if not chart_df.empty:
    chart_df.columns = ["KPI", "Current Month", "Previous Month", "Change %", "Direction"]
    st.plotly_chart(
        mom_comparison_bar(
            chart_df,
            current_label=current_month,
            previous_label=previous_month,
        ),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# % Change waterfall summary
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("🔢 % Change Summary")

pct_df = comparison_df[["KPI", "Change %", "Direction"]].dropna(subset=["Change %"]).copy()

col_pos, col_neg = st.columns(2)
pos = pct_df[pct_df["Change %"] > 0].sort_values("Change %", ascending=False)
neg = pct_df[pct_df["Change %"] < 0].sort_values("Change %")

with col_pos:
    st.markdown("**Improved ↑**")
    for _, r in pos.iterrows():
        st.markdown(
            f"<span style='color:#2ECC71'>▲ {r['KPI']}: **{r['Change %']:+.1f}%**</span>",
            unsafe_allow_html=True,
        )

with col_neg:
    st.markdown("**Declined ↓**")
    for _, r in neg.iterrows():
        st.markdown(
            f"<span style='color:#E74C3C'>▼ {r['KPI']}: **{r['Change %']:+.1f}%**</span>",
            unsafe_allow_html=True,
        )

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.download_button(
        "⬇️ Export MoM Table CSV",
        data=to_csv_bytes(comparison_df),
        file_name=f"mom_analysis_{current_month}.csv",
        mime="text/csv",
    )
with col_e2:
    st.download_button(
        "⬇️ Export MoM Excel",
        data=to_excel_bytes({
            "MoM Comparison": comparison_df,
            "Monthly Data": monthly_df,
        }),
        file_name=f"mom_analysis_{current_month}.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
