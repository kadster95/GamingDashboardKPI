"""
Period-over-period trend calculations: DoD, WoW, MoM.

Each function adds *_pct_change columns alongside the original metric
columns so callers can display both value and delta.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from src.metrics.kpi_calculator import aggregate_monthly, aggregate_weekly

# Columns for which we calculate period changes
_TREND_COLS: List[str] = [
    "ggr", "ngr", "bets", "wins", "bonuses",
    "deposits_amount", "deposits_count",
    "withdrawals_amount", "withdrawals_count",
    "active_players", "new_players",
    "hold_pct", "arpu",
]


def _pct_change(current: float, previous: float) -> Optional[float]:
    """Safe percentage-change helper; returns None when previous is 0/NaN."""
    if previous is None or previous == 0 or pd.isna(previous):
        return None
    return (current - previous) / abs(previous) * 100


# ---------------------------------------------------------------------------
# Daily (Day-over-Day)
# ---------------------------------------------------------------------------


def add_dod_changes(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add *_dod_pct columns: percentage change vs. the immediately preceding row.

    The DataFrame must be sorted ascending by date.
    """
    df = df.sort_values("date").reset_index(drop=True).copy()

    for col in _TREND_COLS:
        if col not in df.columns:
            continue
        shifted = df[col].shift(1)
        df[f"{col}_dod_pct"] = (
            (df[col] - shifted) / shifted.abs().replace(0, float("nan")) * 100
        )

    return df


def get_dod_summary(df: pd.DataFrame) -> dict:
    """
    Return a dict summarising the latest day vs. the previous day.

    Keys: metric → {"current": value, "previous": value, "pct_change": value}
    """
    df = df.sort_values("date").reset_index(drop=True)

    if len(df) < 1:
        return {}

    latest = df.iloc[-1]
    previous = df.iloc[-2] if len(df) >= 2 else None

    summary = {}
    for col in _TREND_COLS:
        if col not in df.columns:
            continue
        curr_val = latest.get(col)
        prev_val = previous.get(col) if previous is not None else None
        summary[col] = {
            "current": curr_val,
            "previous": prev_val,
            "pct_change": _pct_change(curr_val, prev_val),
            "date": str(latest["date"])[:10],
        }

    return summary


# ---------------------------------------------------------------------------
# Weekly (Week-over-Week)
# ---------------------------------------------------------------------------


def add_wow_changes(weekly_df: pd.DataFrame) -> pd.DataFrame:
    """Add *_wow_pct columns to a weekly-aggregated DataFrame."""
    df = weekly_df.sort_values("week").reset_index(drop=True).copy()

    for col in _TREND_COLS:
        if col not in df.columns:
            continue
        shifted = df[col].shift(1)
        df[f"{col}_wow_pct"] = (
            (df[col] - shifted) / shifted.abs().replace(0, float("nan")) * 100
        )

    return df


def get_weekly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to weekly level and attach WoW change columns."""
    weekly = aggregate_weekly(daily_df)
    return add_wow_changes(weekly)


# ---------------------------------------------------------------------------
# Monthly (Month-over-Month)
# ---------------------------------------------------------------------------


def add_mom_changes(monthly_df: pd.DataFrame) -> pd.DataFrame:
    """Add *_mom_pct columns to a monthly-aggregated DataFrame."""
    df = monthly_df.sort_values("month").reset_index(drop=True).copy()

    for col in _TREND_COLS:
        if col not in df.columns:
            continue
        shifted = df[col].shift(1)
        df[f"{col}_mom_pct"] = (
            (df[col] - shifted) / shifted.abs().replace(0, float("nan")) * 100
        )

    return df


def get_monthly_trends(daily_df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate to monthly level and attach MoM change columns."""
    monthly = aggregate_monthly(daily_df)
    return add_mom_changes(monthly)


def get_mom_comparison(daily_df: pd.DataFrame) -> dict:
    """
    Return a comparison of the most recent complete month vs. the one before.

    Result dict: metric → {current, previous, pct_change, current_month, previous_month}
    """
    monthly = get_monthly_trends(daily_df)

    if len(monthly) < 1:
        return {}

    last = monthly.iloc[-1]
    prev = monthly.iloc[-2] if len(monthly) >= 2 else None

    comparison = {}
    for col in _TREND_COLS:
        if col not in monthly.columns:
            continue
        curr_val = last.get(col)
        prev_val = prev.get(col) if prev is not None else None
        comparison[col] = {
            "current": curr_val,
            "previous": prev_val,
            "pct_change": _pct_change(curr_val, prev_val),
            "current_month": str(last["month"])[:7],
            "previous_month": str(prev["month"])[:7] if prev is not None else "—",
        }

    return comparison
