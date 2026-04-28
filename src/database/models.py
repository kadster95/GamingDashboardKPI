"""SQLite DDL for all tables used by the casino analytics system."""

DAILY_DATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS daily_data (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    date                TEXT    UNIQUE NOT NULL,
    bets                REAL,
    wins                REAL,
    ggr                 REAL,
    ngr                 REAL,
    bonuses             REAL,
    deposits_amount     REAL,
    deposits_count      INTEGER,
    withdrawals_amount  REAL,
    withdrawals_count   INTEGER,
    active_players      INTEGER,
    new_players         INTEGER,
    hold_pct            REAL,
    arpu                REAL,
    created_at          TEXT DEFAULT (datetime('now')),
    updated_at          TEXT DEFAULT (datetime('now'))
)
"""

GAME_DATA_SCHEMA = """
CREATE TABLE IF NOT EXISTS game_data (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    date            TEXT    NOT NULL,
    game_name       TEXT    NOT NULL,
    provider        TEXT,
    bets            REAL,
    wins            REAL,
    ggr             REAL,
    active_players  INTEGER,
    created_at      TEXT DEFAULT (datetime('now')),
    UNIQUE (date, game_name)
)
"""

ALL_SCHEMAS = [DAILY_DATA_SCHEMA, GAME_DATA_SCHEMA]
