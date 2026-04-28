"""
Month-over-Month (MoM) analysis builder.

Produces a structured comparison table for the last two calendar months,
including percentage changes for every available KPI.
"""

from __future__ import annotations

from typing import Any, Dict, List

import pandas as pd

from src.metrics.kpi_calculator import compute_kpis
from src.metrics.trends import get_mom_comparison, get_monthly_trends

_METRIC_LABELS: Dict[str, str] = {
    "ggr": "GGR",
    "ngr": "NGR",
    "bets": "Bets / Turnover",
    "wins": "Wins",
    "bonuses": "Bonuses",
    "deposits_amount": "Deposits (Amount)",
    "deposits_count": "Deposits (Count)",
    "withdrawals_amount": "Withdrawals (Amount)",
    "withdrawals_count": "Withdrawals (Count)",
    "active_players": "Active Players",
    "new_players": "New Players",
    "hold_pct": "Hold %",
    "arpu": "ARPU",
}


def build_mom_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Build a full MoM analysis payload.

    Returns:
        comparison_df  – tidy DataFrame with one row per KPI
        monthly_df     – full monthly aggregation with mom_pct columns
        months         – (current_month_label, previous_month_label)
    """
    if df.empty:
        return {
            "comparison_df": pd.DataFrame(),
            "monthly_df": pd.DataFrame(),
            "months": ("—", "—"),
        }

    df = compute_kpis(df.sort_values("date").reset_index(drop=True))
    comparison = get_mom_comparison(df)
    monthly_df = get_monthly_trends(df)

    rows: List[Dict[str, Any]] = []
    current_month = "—"
    previous_month = "—"

    for metric, info in comparison.items():
        label = _METRIC_LABELS.get(metric, metric.replace("_", " ").title())
        pct = info["pct_change"]
        rows.append(
            {
                "KPI": label,
                "Current Month": info["current"],
                "Previous Month": info["previous"],
                "Change %": round(pct, 2) if pct is not None else None,
                "Direction": (
                    "↑" if (pct or 0) > 0 else ("↓" if (pct or 0) < 0 else "—")
                ),
            }
        )
        current_month = info.get("current_month", "—")
        previous_month = info.get("previous_month", "—")

    comparison_df = pd.DataFrame(rows)

    return {
        "comparison_df": comparison_df,
        "monthly_df": monthly_df,
        "months": (current_month, previous_month),
    }
