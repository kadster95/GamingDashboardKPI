"""
Reusable KPI metric card components built on top of st.metric.
"""

from __future__ import annotations

from typing import Optional

import streamlit as st


def _fmt_currency(value: Optional[float]) -> str:
    if value is None or (hasattr(value, "__class__") and str(value) == "nan"):
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if abs(v) >= 1_000_000:
        return f"${v / 1_000_000:,.2f}M"
    if abs(v) >= 1_000:
        return f"${v / 1_000:,.1f}K"
    return f"${v:,.2f}"


def _fmt_number(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    try:
        v = float(value)
    except (TypeError, ValueError):
        return "N/A"
    if abs(v) >= 1_000_000:
        return f"{v / 1_000_000:,.2f}M"
    if abs(v) >= 1_000:
        return f"{v / 1_000:,.1f}K"
    return f"{v:,.0f}"


def _fmt_pct(value: Optional[float]) -> str:
    if value is None:
        return "N/A"
    try:
        return f"{float(value):.2f}%"
    except (TypeError, ValueError):
        return "N/A"


def _delta_str(pct: Optional[float]) -> Optional[str]:
    if pct is None:
        return None
    try:
        p = float(pct)
        arrow = "▲" if p >= 0 else "▼"
        return f"{arrow} {abs(p):.1f}%"
    except (TypeError, ValueError):
        return None


def render_kpi_card(
    label: str,
    value: Optional[float],
    pct_change: Optional[float] = None,
    fmt: str = "currency",
    help_text: Optional[str] = None,
    invert_delta: bool = False,
) -> None:
    """
    Render a single KPI card.

    Args:
        label:        Card title.
        value:        Current period value.
        pct_change:   % change vs. previous period (positive = up).
        fmt:          "currency" | "number" | "percentage"
        help_text:    Tooltip text.
        invert_delta: Set True when a lower value is better (e.g. withdrawals).
    """
    if fmt == "currency":
        display = _fmt_currency(value)
    elif fmt == "percentage":
        display = _fmt_pct(value)
    else:
        display = _fmt_number(value)

    delta = _delta_str(pct_change)

    # Streamlit st.metric uses delta_color="normal" (green=up, red=down)
    # We flip this for metrics where down is good.
    delta_color = "inverse" if invert_delta else "normal"

    st.metric(
        label=label,
        value=display,
        delta=delta,
        delta_color=delta_color,
        help=help_text,
    )


def render_kpi_row(kpis: dict, period_label: str = "vs prev period") -> None:
    """
    Render a full row of KPI cards.

    ``kpis`` is a dict: metric_key → {"current": v, "pct_change": v, ...}
    """
    _DISPLAY_ORDER = [
        ("ggr", "GGR", "currency", False),
        ("ngr", "NGR", "currency", False),
        ("bets", "Bets / Turnover", "currency", False),
        ("hold_pct", "Hold %", "percentage", False),
        ("arpu", "ARPU", "currency", False),
        ("active_players", "Active Players", "number", False),
        ("new_players", "New Players", "number", False),
        ("deposits_amount", "Deposits", "currency", False),
        ("withdrawals_amount", "Withdrawals", "currency", True),
    ]

    visible = [(k, lbl, fmt, inv) for k, lbl, fmt, inv in _DISPLAY_ORDER if k in kpis]
    if not visible:
        st.info("No KPI data available for this period.")
        return

    cols = st.columns(min(len(visible), 4))
    for idx, (key, label, fmt, inv) in enumerate(visible):
        info = kpis[key]
        with cols[idx % 4]:
            render_kpi_card(
                label=label,
                value=info.get("current"),
                pct_change=info.get("pct_change"),
                fmt=fmt,
                help_text=f"{period_label}",
                invert_delta=inv,
            )
            # Start a new row every 4 cards
            if (idx + 1) % 4 == 0 and idx + 1 < len(visible):
                cols = st.columns(min(len(visible) - idx - 1, 4))
