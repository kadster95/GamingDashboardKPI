"""
Core KPI computation applied to daily-level DataFrames.

All functions accept a DataFrame with the standard internal column names
and return the same DataFrame enriched with computed columns.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute / fill-in all derived KPIs for a daily DataFrame.

    Input columns used (all optional except where noted):
        bets, wins, ggr, bonuses, active_players,
        deposits_amount, deposits_count,
        withdrawals_amount, withdrawals_count

    Added / overwritten columns:
        ggr, ngr, hold_pct, arpu, deposit_avg, withdrawal_avg
    """
    df = df.copy()

    # GGR -------------------------------------------------------------------
    if "ggr" not in df.columns or df["ggr"].isna().all():
        if {"bets", "wins"}.issubset(df.columns):
            df["ggr"] = df["bets"] - df["wins"]
        else:
            df["ggr"] = np.nan

    # NGR -------------------------------------------------------------------
    if "bonuses" in df.columns:
        df["ngr"] = df["ggr"] - df["bonuses"].fillna(0)
    else:
        df["ngr"] = df["ggr"]

    # Hold % ----------------------------------------------------------------
    if "bets" in df.columns:
        df["hold_pct"] = np.where(
            df["bets"] > 0, df["ggr"] / df["bets"] * 100, np.nan
        )
    else:
        df["hold_pct"] = np.nan

    # ARPU ------------------------------------------------------------------
    if "active_players" in df.columns:
        df["arpu"] = np.where(
            df["active_players"] > 0, df["ggr"] / df["active_players"], np.nan
        )
    else:
        df["arpu"] = np.nan

    # Deposit average -------------------------------------------------------
    if {"deposits_amount", "deposits_count"}.issubset(df.columns):
        df["deposit_avg"] = np.where(
            df["deposits_count"] > 0,
            df["deposits_amount"] / df["deposits_count"],
            np.nan,
        )
    else:
        df["deposit_avg"] = np.nan

    # Withdrawal average ----------------------------------------------------
    if {"withdrawals_amount", "withdrawals_count"}.issubset(df.columns):
        df["withdrawal_avg"] = np.where(
            df["withdrawals_count"] > 0,
            df["withdrawals_amount"] / df["withdrawals_count"],
            np.nan,
        )
    else:
        df["withdrawal_avg"] = np.nan

    return df


def compute_game_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Compute GGR and hold_pct for game-level data."""
    df = df.copy()

    if "ggr" not in df.columns or df["ggr"].isna().all():
        if {"bets", "wins"}.issubset(df.columns):
            df["ggr"] = df["bets"] - df["wins"]

    if "bets" in df.columns:
        df["hold_pct"] = np.where(
            df["bets"] > 0, df["ggr"] / df["bets"] * 100, np.nan
        )

    return df


def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily data to ISO week level.

    Returns one row per (year, week) with summed amounts and averaged rates.
    """
    df = df.copy()
    df["week"] = df["date"].dt.to_period("W").dt.start_time
    df["week_label"] = df["date"].dt.strftime("W%V %Y")

    sum_cols = [
        "bets", "wins", "ggr", "ngr", "bonuses",
        "deposits_amount", "deposits_count",
        "withdrawals_amount", "withdrawals_count",
        "active_players", "new_players",
    ]
    sum_cols = [c for c in sum_cols if c in df.columns]

    agg = df.groupby("week", as_index=False)[sum_cols].sum(min_count=1)

    # Recompute rates from aggregated totals
    agg = compute_kpis(agg)
    agg = agg.sort_values("week")
    return agg


def aggregate_monthly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily data to calendar month level."""
    df = df.copy()
    df["month"] = df["date"].dt.to_period("M").dt.start_time

    sum_cols = [
        "bets", "wins", "ggr", "ngr", "bonuses",
        "deposits_amount", "deposits_count",
        "withdrawals_amount", "withdrawals_count",
        "active_players", "new_players",
    ]
    sum_cols = [c for c in sum_cols if c in df.columns]

    agg = df.groupby("month", as_index=False)[sum_cols].sum(min_count=1)
    agg = compute_kpis(agg)
    agg = agg.sort_values("month")
    return agg
