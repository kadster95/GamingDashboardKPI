"""
Monthly report builder.

Aggregates daily data to calendar months and computes MoM deltas.
"""

from __future__ import annotations

from typing import Any, Dict

import pandas as pd

from src.metrics.kpi_calculator import compute_kpis
from src.metrics.trends import get_monthly_trends


def build_monthly_report(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build the monthly report payload.

    Returns:
        monthly_df  – aggregated + MoM-enriched DataFrame
        summary     – dict with the most recent month's KPI changes
    """
    if df.empty:
        return {"monthly_df": pd.DataFrame(), "summary": {}}

    df = compute_kpis(df.sort_values("date").reset_index(drop=True))
    monthly_df = get_monthly_trends(df)

    summary: Dict[str, Any] = {}
    if len(monthly_df) >= 1:
        last = monthly_df.iloc[-1]
        prev = monthly_df.iloc[-2] if len(monthly_df) >= 2 else None

        for col in ("ggr", "ngr", "bets", "active_players", "new_players",
                    "deposits_amount", "withdrawals_amount", "hold_pct", "arpu"):
            if col not in monthly_df.columns:
                continue
            pct_col = f"{col}_mom_pct"
            summary[col] = {
                "current": last.get(col),
                "previous": prev.get(col) if prev is not None else None,
                "pct_change": last.get(pct_col),
                "month": str(last.get("month", ""))[:7],
            }

    return {"monthly_df": monthly_df, "summary": summary}
