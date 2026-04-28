"""
Central configuration: KPI definitions, anomaly thresholds, column aliases,
chart colours, and forecasting parameters.
"""

# --- Persistence ----------------------------------------------------------

DATABASE_PATH = "data/casino.db"

# --- KPI catalogue --------------------------------------------------------

KPI_DEFINITIONS = {
    "GGR": {
        "name": "Gross Gaming Revenue",
        "description": "Total bets minus total wins",
        "formula": "GGR = Bets - Wins",
        "format": "currency",
        "higher_is_better": True,
    },
    "NGR": {
        "name": "Net Gaming Revenue",
        "description": "GGR minus bonuses paid to players",
        "formula": "NGR = GGR - Bonuses",
        "format": "currency",
        "higher_is_better": True,
    },
    "ARPU": {
        "name": "Average Revenue Per User",
        "description": "GGR divided by number of active players",
        "formula": "ARPU = GGR / Active Players",
        "format": "currency",
        "higher_is_better": True,
    },
    "Hold%": {
        "name": "Hold Percentage",
        "description": "Proportion of bets retained as GGR",
        "formula": "Hold% = GGR / Bets × 100",
        "format": "percentage",
        "higher_is_better": True,
    },
    "Bets": {
        "name": "Total Bets / Turnover",
        "description": "Sum of all wagers placed",
        "formula": "—",
        "format": "currency",
        "higher_is_better": True,
    },
    "Active Players": {
        "name": "Active Players",
        "description": "Players who placed at least one bet",
        "formula": "—",
        "format": "number",
        "higher_is_better": True,
    },
}

# --- Anomaly detection ----------------------------------------------------
# Percentage change thresholds that trigger an anomaly flag.

ANOMALY_THRESHOLDS = {
    "default": 0.30,
    "ggr": 0.30,
    "ngr": 0.30,
    "bets": 0.35,
    "active_players": 0.25,
    "new_players": 0.40,
    "deposits_amount": 0.35,
    "withdrawals_amount": 0.35,
    "hold_pct": 0.20,
}

# --- Column name normalisation --------------------------------------------
# Maps standard internal column name → list of accepted CSV/Excel headers.

COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["date", "day", "report_date", "Date", "Day", "Report Date", "Report_Date"],
    "bets": ["bets", "turnover", "bet_amount", "total_bets", "Bets", "Turnover", "Total Bets"],
    "wins": ["wins", "win_amount", "total_wins", "Wins", "Win Amount", "Total Wins"],
    "ggr": ["ggr", "gross_gaming_revenue", "GGR", "Gross Gaming Revenue", "Gross_Gaming_Revenue"],
    "bonuses": ["bonuses", "bonus", "bonus_amount", "Bonuses", "Bonus", "Bonus Amount"],
    "deposits_amount": [
        "deposits_amount", "deposit_amount", "deposits", "Deposits Amount",
        "Deposit Amount", "Deposits", "Total Deposits",
    ],
    "deposits_count": [
        "deposits_count", "deposit_count", "num_deposits", "Deposits Count",
        "Deposit Count", "# Deposits",
    ],
    "withdrawals_amount": [
        "withdrawals_amount", "withdrawal_amount", "withdrawals", "Withdrawals Amount",
        "Withdrawal Amount", "Withdrawals", "Total Withdrawals",
    ],
    "withdrawals_count": [
        "withdrawals_count", "withdrawal_count", "num_withdrawals", "Withdrawals Count",
        "Withdrawal Count", "# Withdrawals",
    ],
    "active_players": [
        "active_players", "active_users", "dau", "Active Players",
        "Active Users", "DAU",
    ],
    "new_players": [
        "new_players", "new_users", "registrations", "New Players",
        "New Users", "Registrations", "New Registrations",
    ],
}

GAME_COLUMN_ALIASES: dict[str, list[str]] = {
    "date": ["date", "Date"],
    "game_name": ["game_name", "game", "Game Name", "Game", "game_title", "Game Title"],
    "provider": ["provider", "Provider", "game_provider", "Game Provider", "vendor", "Vendor"],
    "bets": ["bets", "turnover", "Bets", "Turnover"],
    "wins": ["wins", "Wins"],
    "ggr": ["ggr", "GGR"],
    "active_players": ["active_players", "players", "Active Players", "Players"],
}

# --- Chart styling --------------------------------------------------------

CHART_COLORS = {
    "primary": "#4C9BE8",
    "success": "#2ECC71",
    "danger": "#E74C3C",
    "warning": "#F39C12",
    "info": "#1ABC9C",
    "purple": "#9B59B6",
    "secondary": "#95A5A6",
}

CHART_TEMPLATE = "plotly_dark"

# --- Forecasting ----------------------------------------------------------

FORECAST_WINDOW = 7        # rolling average window (days)
FORECAST_HORIZON = 14      # days to project forward

# --- Reporting defaults ---------------------------------------------------

DEFAULT_DATE_RANGE_DAYS = 30
