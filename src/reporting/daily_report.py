"""
Daily report builder.

Produces a structured dict with the latest day's metrics, DoD deltas,
and a list of flagged anomalies — ready for the UI layer to consume.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import pandas as pd

from src.metrics.anomaly_detector import Anomaly, anomalies_to_df, detect_daily_anomalies
from src.metrics.kpi_calculator import compute_kpis
from src.metrics.trends import add_dod_changes, get_dod_summary


def build_daily_report(
    df: pd.DataFrame,
    target_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Build the daily report payload.

    Args:
        df:          Full daily DataFrame (any date range).
        target_date: Optional YYYY-MM-DD string; defaults to most recent date.

    Returns a dict with keys:
        date, kpis (DoD summary dict), anomalies (DataFrame), trend_df
    """
    if df.empty:
        return {"date": None, "kpis": {}, "anomalies": pd.DataFrame(), "trend_df": pd.DataFrame()}

    df = compute_kpis(df.sort_values("date").reset_index(drop=True))
    df = add_dod_changes(df)

    if target_date:
        target_dt = pd.to_datetime(target_date)
        # Include the day before target to compute DoD
        window = df[df["date"] <= target_dt].tail(2)
    else:
        window = df.tail(2)

    dod_summary = get_dod_summary(window)

    anomalies: List[Anomaly] = detect_daily_anomalies(df)
    if target_date:
        anomalies = [a for a in anomalies if a.date == str(target_dt)[:10]]

    # Trend df = last 30 days for charts
    trend_df = df.tail(30).copy()

    report_date = str(window["date"].iloc[-1])[:10] if not window.empty else None

    return {
        "date": report_date,
        "kpis": dod_summary,
        "anomalies": anomalies_to_df(anomalies),
        "trend_df": trend_df,
    }
