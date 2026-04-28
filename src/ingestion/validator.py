"""
Data validation and cleaning for casino daily and game-level DataFrames.

Returns a cleaned DataFrame plus a list of human-readable warning strings
so callers can surface issues in the UI.
"""

from __future__ import annotations

from typing import List, Tuple

import pandas as pd


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def validate_daily(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """
    Validate and clean a daily-summary DataFrame.

    Returns (cleaned_df, warnings).  Rows that cannot be salvaged are
    dropped; warnings describe every problem found.
    """
    warnings: List[str] = []
    df = df.copy()

    # -- Date column -------------------------------------------------------
    if "date" not in df.columns:
        warnings.append("CRITICAL: 'date' column is missing — cannot process file.")
        return pd.DataFrame(), warnings

    original_len = len(df)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates:
        warnings.append(f"{bad_dates} row(s) had unparseable dates and were removed.")
    df = df.dropna(subset=["date"])

    # Deduplicate within the uploaded batch (keep last occurrence)
    dupes = df.duplicated(subset=["date"], keep="last").sum()
    if dupes:
        warnings.append(
            f"{dupes} duplicate date(s) in upload — kept most recent row per date."
        )
    df = df.drop_duplicates(subset=["date"], keep="last")

    # -- Numeric columns ---------------------------------------------------
    numeric_cols = [
        "bets", "wins", "ggr", "bonuses",
        "deposits_amount", "deposits_count",
        "withdrawals_amount", "withdrawals_count",
        "active_players", "new_players",
    ]

    for col in numeric_cols:
        if col not in df.columns:
            continue
        before = df[col].notna().sum()
        df[col] = pd.to_numeric(df[col], errors="coerce")
        after = df[col].notna().sum()
        if before != after:
            warnings.append(
                f"Column '{col}': {before - after} non-numeric value(s) set to NaN."
            )

        # Negative-value guard for amounts/counts that must be non-negative
        if col in {"bets", "wins", "deposits_amount", "deposits_count",
                   "withdrawals_amount", "withdrawals_count",
                   "active_players", "new_players"}:
            neg = (df[col] < 0).sum()
            if neg:
                df.loc[df[col] < 0, col] = None
                warnings.append(
                    f"Column '{col}': {neg} negative value(s) replaced with NaN."
                )

    # -- Cross-field sanity ------------------------------------------------
    if {"bets", "wins"}.issubset(df.columns):
        bad = (df["wins"] > df["bets"]).sum()
        if bad:
            warnings.append(
                f"{bad} row(s) where wins > bets — check source data."
            )

    if len(df) < original_len - bad_dates:
        warnings.append(
            f"{original_len - len(df)} row(s) were removed during validation."
        )

    return df.reset_index(drop=True), warnings


def validate_game(df: pd.DataFrame) -> Tuple[pd.DataFrame, List[str]]:
    """Validate and clean a game-level DataFrame."""
    warnings: List[str] = []
    df = df.copy()

    required = {"date", "game_name"}
    missing = required - set(df.columns)
    if missing:
        warnings.append(f"CRITICAL: Missing required columns: {missing}.")
        return pd.DataFrame(), warnings

    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    bad_dates = df["date"].isna().sum()
    if bad_dates:
        warnings.append(f"{bad_dates} game row(s) with invalid dates removed.")
    df = df.dropna(subset=["date"])

    df["game_name"] = df["game_name"].astype(str).str.strip()
    df = df[df["game_name"] != ""]

    for col in ("bets", "wins", "ggr", "active_players"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    dupes = df.duplicated(subset=["date", "game_name"], keep="last").sum()
    if dupes:
        warnings.append(
            f"{dupes} duplicate (date, game_name) pair(s) — kept last occurrence."
        )
    df = df.drop_duplicates(subset=["date", "game_name"], keep="last")

    return df.reset_index(drop=True), warnings
