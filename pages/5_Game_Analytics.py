"""Game Analytics page — top games by GGR/bets, provider comparison."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date, timedelta
from typing import List

import pandas as pd
import streamlit as st

from src.database.db_manager import fetch_game_data, get_data_summary, initialize_database
from src.metrics.kpi_calculator import compute_game_kpis
from src.export.exporter import to_csv_bytes, to_excel_bytes
from ui.components.charts import bar_chart, donut_chart, grouped_bar_chart, line_chart

st.set_page_config(page_title="Game Analytics | Casino Analytics", page_icon="🎮", layout="wide")
initialize_database()

st.title("🎮 Game Analytics")

# ---------------------------------------------------------------------------
# Date filter
# ---------------------------------------------------------------------------

summary = get_data_summary()
data_max = date.fromisoformat(summary["max_date"]) if summary["max_date"] else date.today()
data_min = date.fromisoformat(summary["min_date"]) if summary["min_date"] else data_max - timedelta(days=90)

with st.sidebar:
    st.subheader("Date Range")
    start_date = st.date_input("From", value=data_max - timedelta(days=29), min_value=data_min, max_value=data_max)
    end_date   = st.date_input("To",   value=data_max, min_value=data_min, max_value=data_max)
    top_n      = st.slider("Top N games", min_value=5, max_value=30, value=10)

game_df = fetch_game_data(start_date=str(start_date), end_date=str(end_date))

if game_df.empty:
    st.info(
        "No game-level data found for this period. "
        "Upload a file with game columns (Game Name, Provider, Bets, GGR, …) "
        "via **Data Management**."
    )
    st.stop()

game_df = compute_game_kpis(game_df)

# ---------------------------------------------------------------------------
# Aggregate across date range
# ---------------------------------------------------------------------------

agg_cols = [c for c in ("bets", "wins", "ggr", "active_players") if c in game_df.columns]
game_agg = game_df.groupby("game_name", as_index=False)[agg_cols].sum()

if "provider" in game_df.columns:
    game_agg = game_agg.merge(
        game_df.groupby("game_name")["provider"].first().reset_index(),
        on="game_name",
        how="left",
    )

if "bets" in game_agg.columns and "ggr" in game_agg.columns:
    game_agg["hold_pct"] = game_agg.apply(
        lambda r: r["ggr"] / r["bets"] * 100 if r["bets"] > 0 else None, axis=1
    )

game_agg = game_agg.sort_values("ggr", ascending=False)

# ---------------------------------------------------------------------------
# Top games
# ---------------------------------------------------------------------------

st.subheader(f"🏆 Top {top_n} Games by GGR")

top_games = game_agg.head(top_n)

col1, col2 = st.columns(2)
with col1:
    if "ggr" in top_games.columns:
        fig = bar_chart(
            top_games.sort_values("ggr"),
            x="ggr", y="game_name",
            title=f"Top {top_n} Games by GGR",
            orientation="h",
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    if "bets" in top_games.columns:
        fig = bar_chart(
            top_games.sort_values("bets"),
            x="bets", y="game_name",
            title=f"Top {top_n} Games by Bets",
            orientation="h",
            color="info",
        )
        st.plotly_chart(fig, use_container_width=True)

# ---------------------------------------------------------------------------
# Provider comparison
# ---------------------------------------------------------------------------

if "provider" in game_df.columns:
    st.markdown("---")
    st.subheader("🏢 Provider Comparison")

    prov_agg = game_df.groupby("provider", as_index=False)[agg_cols].sum()
    prov_agg = prov_agg.sort_values("ggr", ascending=False)

    col3, col4 = st.columns(2)
    with col3:
        if "ggr" in prov_agg.columns:
            st.plotly_chart(
                donut_chart(
                    labels=prov_agg["provider"].tolist(),
                    values=prov_agg["ggr"].tolist(),
                    title="GGR Share by Provider",
                ),
                use_container_width=True,
            )
    with col4:
        if "bets" in prov_agg.columns:
            st.plotly_chart(
                bar_chart(prov_agg.sort_values("bets"), "bets", "provider",
                          title="Bets by Provider", orientation="h", color="purple"),
                use_container_width=True,
            )

    st.dataframe(prov_agg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Game trends over time (multi-select)
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📈 Game Trend Over Time")

all_games = sorted(game_df["game_name"].unique().tolist())
selected_games: List[str] = st.multiselect(
    "Select games to compare",
    options=all_games,
    default=all_games[:min(3, len(all_games))],
)

if selected_games and "ggr" in game_df.columns:
    pivot = (
        game_df[game_df["game_name"].isin(selected_games)]
        .pivot_table(index="date", columns="game_name", values="ggr", aggfunc="sum")
        .reset_index()
    )
    st.plotly_chart(
        line_chart(pivot, "date", selected_games, title="GGR by Game Over Time"),
        use_container_width=True,
    )

# ---------------------------------------------------------------------------
# Full game table
# ---------------------------------------------------------------------------

st.markdown("---")
st.subheader("📋 Full Game Summary")
st.dataframe(game_agg, use_container_width=True, hide_index=True)

# ---------------------------------------------------------------------------
# Export
# ---------------------------------------------------------------------------

st.markdown("---")
col_e1, col_e2 = st.columns(2)
with col_e1:
    st.download_button(
        "⬇️ Export Game Summary CSV",
        data=to_csv_bytes(game_agg),
        file_name="game_analytics.csv",
        mime="text/csv",
    )
with col_e2:
    st.download_button(
        "⬇️ Export Excel",
        data=to_excel_bytes({"Game Summary": game_agg, "Raw Game Data": game_df}),
        file_name="game_analytics.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
