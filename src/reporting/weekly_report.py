"""
Weekly report builder.

Aggregates daily data to ISO weeks and computes WoW deltas.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.metrics.kpi_calculator import compute_kpis
from src.metrics.trends import get_weekly_trends


def build_weekly_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build the weekly report payload.

    Returns:
        weekly_df  – aggregated + WoW-enriched DataFrame
        summary    – dict with the most recent week's KPI changes
    """
    if df.empty:
        return {"weekly_df": pd.DataFrame(), "summary": {}}

    df = compute_kpis(df.sort_values("date").reset_index(drop=True))
    weekly_df = get_weekly_trends(df)

    # Summary: last week vs previous week
    summary: Dict[str, Any] = {}
    if len(weekly_df) >= 1:
        last = weekly_df.iloc[-1]
        prev = weekly_df.iloc[-2] if len(weekly_df) >= 2 else None

        for col in ("ggr", "ngr", "bets", "active_players", "new_players",
                    "deposits_amount", "withdrawals_amount"):
            if col not in weekly_df.columns:
                continue
            pct_col = f"{col}_wow_pct"
            summary[col] = {
                "current": last.get(col),
                "previous": prev.get(col) if prev is not None else None,
                "pct_change": last.get(pct_col),
                "week": str(last.get("week", ""))[:10],
            }

    return {"weekly_df": weekly_df, "summary": summary}
