"""
Simple rolling-average forecasting.

Computes a centred/trailing rolling mean and projects forward
FORECAST_HORIZON days using the average of the last FORECAST_WINDOW days.
"""

from __future__ import annotations

from typing import List

import numpy as np
import pandas as pd

from config import FORECAST_HORIZON, FORECAST_WINDOW

_FORECASTABLE: List[str] = ["ggr", "ngr", "bets", "active_players", "deposits_amount"]


def add_rolling_averages(df: pd.DataFrame) -> pd.DataFrame:
    """
    Add a *_rolling_{window}d column for each forecastable metric.
    """
    df = df.sort_values("date").reset_index(drop=True).copy()

    for col in _FORECASTABLE:
        if col not in df.columns:
            continue
        df[f"{col}_rolling"] = (
            df[col].rolling(window=FORECAST_WINDOW, min_periods=1).mean()
        )

    return df


def forecast_forward(df: pd.DataFrame) -> pd.DataFrame:
    """
    Project each forecastable metric FORECAST_HORIZON days beyond the last
    observed date using a rolling-average baseline.

    Returns a DataFrame of future rows with columns:
        date, <metric>_forecast, ... for each forecastable metric present.
    """
    df = df.sort_values("date").reset_index(drop=True)

    if df.empty:
        return pd.DataFrame()

    last_date = df["date"].max()
    future_dates = pd.date_range(
        start=last_date + pd.Timedelta(days=1),
        periods=FORECAST_HORIZON,
        freq="D",
    )

    forecast_rows = {"date": future_dates}

    for col in _FORECASTABLE:
        if col not in df.columns:
            continue
        tail = df[col].dropna().tail(FORECAST_WINDOW)
        if tail.empty:
            continue
        baseline = tail.mean()
        # Simple flat projection; can be extended with linear trend
        forecast_rows[f"{col}_forecast"] = np.full(FORECAST_HORIZON, baseline)

    return pd.DataFrame(forecast_rows)
