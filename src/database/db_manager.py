"""
Database manager: initialisation, upsert, fetch, and delete operations
for daily summary and game-level data.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import pandas as pd

from src.database.models import ALL_SCHEMAS

# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

_DAILY_MUTABLE_COLS: List[str] = [
    "bets", "wins", "ggr", "ngr", "bonuses",
    "deposits_amount", "deposits_count",
    "withdrawals_amount", "withdrawals_count",
    "active_players", "new_players",
    "hold_pct", "arpu", "updated_at",
]

_DAILY_ALL_COLS: List[str] = ["date"] + _DAILY_MUTABLE_COLS

_GAME_MUTABLE_COLS: List[str] = [
    "provider", "bets", "wins", "ggr", "active_players",
]

_GAME_ALL_COLS: List[str] = ["date", "game_name"] + _GAME_MUTABLE_COLS


def _get_db_path() -> str:
    from config import DATABASE_PATH  # deferred import avoids circular deps at module level
    return DATABASE_PATH


def _connect() -> sqlite3.Connection:
    """Return a connection, creating the DB file and parent dirs if needed."""
    db_path = Path(_get_db_path())
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def initialize_database() -> None:
    """Create all tables when they do not yet exist."""
    with _connect() as conn:
        for schema in ALL_SCHEMAS:
            conn.execute(schema)
        conn.commit()


# --- Daily data -----------------------------------------------------------


def upsert_daily_data(df: pd.DataFrame) -> Dict[str, int]:
    """
    Insert or update rows in *daily_data*.

    Returns a dict with counts: inserted / updated / errors.
    """
    stats: Dict[str, int] = {"inserted": 0, "updated": 0, "errors": 0}

    with _connect() as conn:
        for _, row in df.iterrows():
            try:
                data: Dict[str, Any] = {
                    k: (None if pd.isna(v) else v)
                    for k, v in row.items()
                }
                data["updated_at"] = datetime.now().isoformat()

                date_val = data.get("date")
                if date_val is None:
                    stats["errors"] += 1
                    continue

                # Normalise datetime → plain date string
                if hasattr(date_val, "strftime"):
                    date_val = date_val.strftime("%Y-%m-%d")
                else:
                    date_val = str(date_val)[:10]
                data["date"] = date_val

                existing = conn.execute(
                    "SELECT id FROM daily_data WHERE date = ?", (date_val,)
                ).fetchone()

                if existing:
                    cols = [c for c in _DAILY_MUTABLE_COLS if c in data]
                    set_clause = ", ".join(f"{c} = ?" for c in cols)
                    values = [data[c] for c in cols] + [date_val]
                    conn.execute(
                        f"UPDATE daily_data SET {set_clause} WHERE date = ?",
                        values,
                    )
                    stats["updated"] += 1
                else:
                    cols = [c for c in _DAILY_ALL_COLS if c in data]
                    placeholders = ", ".join("?" for _ in cols)
                    conn.execute(
                        f"INSERT INTO daily_data ({', '.join(cols)}) VALUES ({placeholders})",
                        [data[c] for c in cols],
                    )
                    stats["inserted"] += 1

            except Exception:
                stats["errors"] += 1

        conn.commit()

    return stats


def fetch_daily_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Return daily_data rows as a DataFrame, sorted ascending by date."""
    query = "SELECT * FROM daily_data"
    params: List[str] = []
    conditions: List[str] = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date ASC"

    with _connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])

    return df


def delete_daily_record(date: str) -> bool:
    """Delete a single daily record by date string (YYYY-MM-DD)."""
    with _connect() as conn:
        cursor = conn.execute("DELETE FROM daily_data WHERE date = ?", (date,))
        conn.commit()
        return cursor.rowcount > 0


# --- Game data ------------------------------------------------------------


def upsert_game_data(df: pd.DataFrame) -> Dict[str, int]:
    """Insert or update rows in *game_data*."""
    stats: Dict[str, int] = {"inserted": 0, "updated": 0, "errors": 0}

    with _connect() as conn:
        for _, row in df.iterrows():
            try:
                data: Dict[str, Any] = {
                    k: (None if pd.isna(v) else v)
                    for k, v in row.items()
                }

                date_val = data.get("date")
                if date_val is None or not data.get("game_name"):
                    stats["errors"] += 1
                    continue

                if hasattr(date_val, "strftime"):
                    date_val = date_val.strftime("%Y-%m-%d")
                else:
                    date_val = str(date_val)[:10]
                data["date"] = date_val

                existing = conn.execute(
                    "SELECT id FROM game_data WHERE date = ? AND game_name = ?",
                    (date_val, data["game_name"]),
                ).fetchone()

                if existing:
                    cols = [c for c in _GAME_MUTABLE_COLS if c in data]
                    set_clause = ", ".join(f"{c} = ?" for c in cols)
                    values = [data[c] for c in cols] + [date_val, data["game_name"]]
                    conn.execute(
                        f"UPDATE game_data SET {set_clause} WHERE date = ? AND game_name = ?",
                        values,
                    )
                    stats["updated"] += 1
                else:
                    cols = [c for c in _GAME_ALL_COLS if c in data]
                    placeholders = ", ".join("?" for _ in cols)
                    conn.execute(
                        f"INSERT INTO game_data ({', '.join(cols)}) VALUES ({placeholders})",
                        [data[c] for c in cols],
                    )
                    stats["inserted"] += 1

            except Exception:
                stats["errors"] += 1

        conn.commit()

    return stats


def fetch_game_data(
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> pd.DataFrame:
    """Return game_data rows as a DataFrame."""
    query = "SELECT * FROM game_data"
    params: List[str] = []
    conditions: List[str] = []

    if start_date:
        conditions.append("date >= ?")
        params.append(start_date)
    if end_date:
        conditions.append("date <= ?")
        params.append(end_date)

    if conditions:
        query += " WHERE " + " AND ".join(conditions)
    query += " ORDER BY date ASC, ggr DESC"

    with _connect() as conn:
        df = pd.read_sql_query(query, conn, params=params)

    if not df.empty:
        df["date"] = pd.to_datetime(df["date"])

    return df


# --- Summary --------------------------------------------------------------


def get_data_summary() -> Dict[str, Any]:
    """Return high-level counts and date range for stored data."""
    with _connect() as conn:
        daily_count: int = conn.execute(
            "SELECT COUNT(*) FROM daily_data"
        ).fetchone()[0]
        game_count: int = conn.execute(
            "SELECT COUNT(*) FROM game_data"
        ).fetchone()[0]
        date_range = conn.execute(
            "SELECT MIN(date), MAX(date) FROM daily_data"
        ).fetchone()

    return {
        "daily_records": daily_count,
        "game_records": game_count,
        "min_date": date_range[0],
        "max_date": date_range[1],
    }
