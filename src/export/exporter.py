"""
Report export utilities: CSV, Excel, and optional PDF.
"""

from __future__ import annotations

import io
from typing import Dict, Optional

import pandas as pd


# ---------------------------------------------------------------------------
# CSV
# ---------------------------------------------------------------------------


def to_csv_bytes(df: pd.DataFrame) -> bytes:
    """Return a UTF-8 CSV as bytes for Streamlit's download_button."""
    return df.to_csv(index=False).encode("utf-8")


# ---------------------------------------------------------------------------
# Excel (multi-sheet)
# ---------------------------------------------------------------------------


def to_excel_bytes(sheets: Dict[str, pd.DataFrame]) -> bytes:
    """
    Write multiple DataFrames to an Excel workbook.

    Args:
        sheets: dict of sheet_name → DataFrame

    Returns bytes suitable for Streamlit's download_button.
    """
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        for sheet_name, df in sheets.items():
            safe_name = sheet_name[:31]   # Excel sheet name limit
            df.to_excel(writer, sheet_name=safe_name, index=False)
    return buffer.getvalue()


# ---------------------------------------------------------------------------
# PDF (optional — requires reportlab)
# ---------------------------------------------------------------------------


def to_pdf_bytes(
    title: str,
    df: pd.DataFrame,
    subtitle: Optional[str] = None,
) -> bytes:
    """
    Render a simple PDF report containing a title and a table.

    Requires the *reportlab* package.  Returns an empty bytes object if
    reportlab is not installed (callers should check and warn).
    """
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4, landscape
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import cm
        from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
    except ImportError:
        return b""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(A4),
        rightMargin=1 * cm,
        leftMargin=1 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
    )

    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph(title, styles["Title"]))
    if subtitle:
        elements.append(Paragraph(subtitle, styles["Normal"]))
    elements.append(Spacer(1, 0.5 * cm))

    # Build table data
    headers = list(df.columns)
    rows = [[str(v) if v is not None else "" for v in row] for row in df.values]
    table_data = [headers] + rows

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#2C3E50")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 8),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F2F2F2")]),
                ("GRID", (0, 0), (-1, -1), 0.25, colors.grey),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ]
        )
    )
    elements.append(table)

    doc.build(elements)
    return buffer.getvalue()
