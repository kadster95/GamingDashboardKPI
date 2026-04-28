"""
Anomaly detection: flags metrics where the period-over-period change
exceeds a configurable threshold.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

import pandas as pd

from config import ANOMALY_THRESHOLDS


@dataclass
class Anomaly:
    date: str
    metric: str
    current_value: float
    previous_value: float
    pct_change: float
    direction: str          # "spike" | "drop"
    threshold_pct: float


def detect_daily_anomalies(
    df: pd.DataFrame,
    custom_thresholds: Optional[Dict[str, float]] = None,
) -> List[Anomaly]:
    """
    Scan a daily DataFrame (with *_dod_pct columns) and return anomalies.

    Anomaly = |pct_change| > threshold for that metric.
    """
    thresholds = {**ANOMALY_THRESHOLDS, **(custom_thresholds or {})}
    anomalies: List[Anomaly] = []

    pct_cols = [c for c in df.columns if c.endswith("_dod_pct")]

    for _, row in df.iterrows():
        for pct_col in pct_cols:
            metric = pct_col.replace("_dod_pct", "")
            pct = row.get(pct_col)
            if pct is None or pd.isna(pct):
                continue

            threshold = thresholds.get(metric, thresholds["default"]) * 100

            if abs(pct) >= threshold:
                current_col = metric
                current_val = row.get(current_col, float("nan"))
                prev_val = current_val / (1 + pct / 100) if (1 + pct / 100) != 0 else float("nan")

                anomalies.append(
                    Anomaly(
                        date=str(row["date"])[:10],
                        metric=metric,
                        current_value=current_val,
                        previous_value=prev_val,
                        pct_change=pct,
                        direction="spike" if pct > 0 else "drop",
                        threshold_pct=threshold,
                    )
                )

    return anomalies


def anomalies_to_df(anomalies: List[Anomaly]) -> pd.DataFrame:
    """Convert a list of Anomaly objects to a display-ready DataFrame."""
    if not anomalies:
        return pd.DataFrame(
            columns=["date", "metric", "direction", "pct_change", "current_value", "previous_value"]
        )

    records = [
        {
            "date": a.date,
            "metric": a.metric.replace("_", " ").title(),
            "direction": a.direction.upper(),
            "pct_change": round(a.pct_change, 2),
            "current_value": a.current_value,
            "previous_value": a.previous_value,
            "threshold_%": a.threshold_pct,
        }
        for a in anomalies
    ]
    return pd.DataFrame(records).sort_values(["date", "pct_change"])
