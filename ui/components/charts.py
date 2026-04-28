"""
Reusable Plotly chart components for the casino analytics dashboard.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from config import CHART_COLORS, CHART_TEMPLATE, FORECAST_WINDOW

_C = CHART_COLORS


def _base_layout(fig: go.Figure, title: str) -> go.Figure:
    fig.update_layout(
        title=title,
        template=CHART_TEMPLATE,
        margin=dict(l=40, r=20, t=50, b=40),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
    )
    return fig


# ---------------------------------------------------------------------------
# Line charts
# ---------------------------------------------------------------------------


def line_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    labels: Optional[dict] = None,
    title: str = "",
    yaxis_format: str = "",
) -> go.Figure:
    """Multi-line chart with hover formatting."""
    labels = labels or {}
    fig = go.Figure()

    colour_list = list(_C.values())
    for i, col in enumerate(y_cols):
        if col not in df.columns:
            continue
        colour = colour_list[i % len(colour_list)]
        fig.add_trace(
            go.Scatter(
                x=df[x],
                y=df[col],
                name=labels.get(col, col.replace("_", " ").title()),
                mode="lines+markers",
                line=dict(color=colour, width=2),
                marker=dict(size=4),
            )
        )

    fig = _base_layout(fig, title)
    if yaxis_format:
        fig.update_yaxes(tickformat=yaxis_format)
    return fig


def area_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str = "primary",
) -> go.Figure:
    """Single-series filled area chart."""
    fig = go.Figure(
        go.Scatter(
            x=df[x],
            y=df[y],
            fill="tozeroy",
            mode="lines",
            line=dict(color=_C.get(color, _C["primary"]), width=2),
            fillcolor=_C.get(color, _C["primary"]) + "33",
        )
    )
    return _base_layout(fig, title)


# ---------------------------------------------------------------------------
# Bar charts
# ---------------------------------------------------------------------------


def bar_chart(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: str = "",
    color: str = "primary",
    orientation: str = "v",
) -> go.Figure:
    fig = px.bar(
        df,
        x=x if orientation == "v" else y,
        y=y if orientation == "v" else x,
        orientation=orientation,
        template=CHART_TEMPLATE,
        title=title,
        color_discrete_sequence=[_C.get(color, _C["primary"])],
    )
    fig.update_layout(margin=dict(l=40, r=20, t=50, b=40))
    return fig


def grouped_bar_chart(
    df: pd.DataFrame,
    x: str,
    y_cols: List[str],
    labels: Optional[dict] = None,
    title: str = "",
) -> go.Figure:
    """Side-by-side bars for multiple metrics."""
    labels = labels or {}
    fig = go.Figure()
    colour_list = list(_C.values())

    for i, col in enumerate(y_cols):
        if col not in df.columns:
            continue
        fig.add_trace(
            go.Bar(
                x=df[x],
                y=df[col],
                name=labels.get(col, col.replace("_", " ").title()),
                marker_color=colour_list[i % len(colour_list)],
            )
        )

    fig.update_layout(barmode="group")
    return _base_layout(fig, title)


# ---------------------------------------------------------------------------
# Pie / donut
# ---------------------------------------------------------------------------


def donut_chart(
    labels: List[str],
    values: List[float],
    title: str = "",
) -> go.Figure:
    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.4,
            marker=dict(colors=list(_C.values())),
        )
    )
    return _base_layout(fig, title)


# ---------------------------------------------------------------------------
# Combined actual + forecast
# ---------------------------------------------------------------------------


def forecast_chart(
    historical_df: pd.DataFrame,
    forecast_df: pd.DataFrame,
    metric: str,
    title: str = "",
) -> go.Figure:
    """Plot historical actuals alongside a rolling-average forecast."""
    fig = go.Figure()

    if metric in historical_df.columns:
        fig.add_trace(
            go.Scatter(
                x=historical_df["date"],
                y=historical_df[metric],
                name="Actual",
                mode="lines+markers",
                line=dict(color=_C["primary"], width=2),
            )
        )

    rolling_col = f"{metric}_rolling"
    if rolling_col in historical_df.columns:
        fig.add_trace(
            go.Scatter(
                x=historical_df["date"],
                y=historical_df[rolling_col],
                name=f"{FORECAST_WINDOW}d Rolling Avg",
                mode="lines",
                line=dict(color=_C["warning"], width=1, dash="dot"),
            )
        )

    forecast_col = f"{metric}_forecast"
    if forecast_col in forecast_df.columns:
        fig.add_trace(
            go.Scatter(
                x=forecast_df["date"],
                y=forecast_df[forecast_col],
                name="Forecast",
                mode="lines",
                line=dict(color=_C["success"], width=2, dash="dash"),
            )
        )

    return _base_layout(fig, title)


# ---------------------------------------------------------------------------
# MoM comparison bar
# ---------------------------------------------------------------------------


def mom_comparison_bar(
    comparison_df: pd.DataFrame,
    current_label: str = "Current Month",
    previous_label: str = "Previous Month",
) -> go.Figure:
    """Grouped bar comparing current vs previous month per KPI."""
    if comparison_df.empty:
        return go.Figure()

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=comparison_df["KPI"],
            y=comparison_df["Current Month"],
            name=current_label,
            marker_color=_C["primary"],
        )
    )
    fig.add_trace(
        go.Bar(
            x=comparison_df["KPI"],
            y=comparison_df["Previous Month"],
            name=previous_label,
            marker_color=_C["secondary"],
        )
    )
    fig.update_layout(barmode="group")
    return _base_layout(fig, "Month-over-Month Comparison")
