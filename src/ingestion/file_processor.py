"""
File ingestion: reads CSV or Excel uploads, normalises column names to the
internal schema, and returns separate daily and game DataFrames.
"""

from __future__ import annotations

import io
from typing import Dict, List, Optional, Tuple

import pandas as pd

from config import COLUMN_ALIASES, GAME_COLUMN_ALIASES
from src.ingestion.validator import validate_daily, validate_game


# ---------------------------------------------------------------------------
# Column normalisation
# ---------------------------------------------------------------------------


def _normalise_columns(
    df: pd.DataFrame, alias_map: Dict[str, List[str]]
) -> pd.DataFrame:
    """
    Rename DataFrame columns to internal names using the alias map.
    Columns not in the alias map are kept as-is (for game data passthrough).
    """
    rename: Dict[str, str] = {}
    df_cols_lower = {c.lower().strip(): c for c in df.columns}

    for standard_name, aliases in alias_map.items():
        for alias in aliases:
            key = alias.lower().strip()
            if key in df_cols_lower:
                original = df_cols_lower[key]
                if original != standard_name:
                    rename[original] = standard_name
                break

    return df.rename(columns=rename)


# ---------------------------------------------------------------------------
# Sheet detection
# ---------------------------------------------------------------------------


def _looks_like_game_sheet(df: pd.DataFrame) -> bool:
    """Return True when a DataFrame appears to contain game-level data."""
    game_signals = {"game_name", "game", "game name", "provider"}
    cols_lower = {c.lower().strip() for c in df.columns}
    return bool(game_signals & cols_lower)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def process_upload(
    file_bytes: bytes,
    filename: str,
) -> Tuple[Optional[pd.DataFrame], Optional[pd.DataFrame], List[str]]:
    """
    Parse an uploaded file (CSV or Excel).

    Returns:
        daily_df   – cleaned daily-summary DataFrame (or None)
        game_df    – cleaned game-level DataFrame (or None)
        warnings   – list of human-readable warning strings
    """
    all_warnings: List[str] = []
    daily_df: Optional[pd.DataFrame] = None
    game_df: Optional[pd.DataFrame] = None

    ext = filename.rsplit(".", 1)[-1].lower()

    if ext == "csv":
        raw_sheets = {"Sheet1": _read_csv(file_bytes, all_warnings)}
    elif ext in {"xls", "xlsx"}:
        raw_sheets = _read_excel(file_bytes, all_warnings)
    else:
        all_warnings.append(f"Unsupported file type '.{ext}'. Use CSV or Excel.")
        return None, None, all_warnings

    # Classify and process each sheet
    daily_frames: List[pd.DataFrame] = []
    game_frames: List[pd.DataFrame] = []

    for sheet_name, raw_df in raw_sheets.items():
        if raw_df is None or raw_df.empty:
            continue

        if _looks_like_game_sheet(raw_df):
            norm = _normalise_columns(raw_df, GAME_COLUMN_ALIASES)
            cleaned, warns = validate_game(norm)
            for w in warns:
                all_warnings.append(f"[Game/{sheet_name}] {w}")
            if not cleaned.empty:
                game_frames.append(cleaned)
        else:
            norm = _normalise_columns(raw_df, COLUMN_ALIASES)
            cleaned, warns = validate_daily(norm)
            for w in warns:
                all_warnings.append(f"[Daily/{sheet_name}] {w}")
            if not cleaned.empty:
                daily_frames.append(cleaned)

    if daily_frames:
        daily_df = pd.concat(daily_frames, ignore_index=True)
        daily_df = daily_df.drop_duplicates(subset=["date"], keep="last")

    if game_frames:
        game_df = pd.concat(game_frames, ignore_index=True)
        game_df = game_df.drop_duplicates(subset=["date", "game_name"], keep="last")

    return daily_df, game_df, all_warnings


def process_manual_entry(data: Dict) -> Tuple[Optional[pd.DataFrame], List[str]]:
    """
    Convert a manual-entry dict (from the UI form) into a validated daily DataFrame.
    """
    df = pd.DataFrame([data])
    norm = _normalise_columns(df, COLUMN_ALIASES)
    cleaned, warnings = validate_daily(norm)
    return (cleaned if not cleaned.empty else None), warnings


# ---------------------------------------------------------------------------
# Internal readers
# ---------------------------------------------------------------------------


def _read_csv(
    file_bytes: bytes, warnings: List[str]
) -> Optional[pd.DataFrame]:
    try:
        return pd.read_csv(io.BytesIO(file_bytes))
    except Exception as exc:
        warnings.append(f"Failed to read CSV: {exc}")
        return None


def _read_excel(
    file_bytes: bytes, warnings: List[str]
) -> Dict[str, Optional[pd.DataFrame]]:
    sheets: Dict[str, Optional[pd.DataFrame]] = {}
    try:
        xl = pd.ExcelFile(io.BytesIO(file_bytes))
        for sheet in xl.sheet_names:
            try:
                sheets[sheet] = xl.parse(sheet)
            except Exception as exc:
                warnings.append(f"Could not parse sheet '{sheet}': {exc}")
                sheets[sheet] = None
    except Exception as exc:
        warnings.append(f"Failed to read Excel file: {exc}")
    return sheets
