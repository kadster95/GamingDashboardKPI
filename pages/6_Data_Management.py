"""
Data Management page.

Tabs:
  1. Upload File     — CSV or Excel, supports daily + game data in same workbook
  2. Manual Entry    — form to enter a single day's KPIs
  3. View / Edit     — browse, overwrite, or delete stored records
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from datetime import date

import pandas as pd
import streamlit as st

from src.database.db_manager import (
    delete_daily_record,
    fetch_daily_data,
    initialize_database,
    upsert_daily_data,
    upsert_game_data,
)
from src.ingestion.file_processor import process_manual_entry, process_upload
from src.metrics.kpi_calculator import compute_kpis
from src.export.exporter import to_csv_bytes, to_excel_bytes

st.set_page_config(page_title="Data Management | Casino Analytics", page_icon="📁", layout="wide")
initialize_database()

st.title("📁 Data Management")

tab_upload, tab_manual, tab_view = st.tabs(
    ["📤 Upload File", "✏️ Manual Entry", "🗄️ View / Edit Data"]
)

# ===========================================================================
# TAB 1 — FILE UPLOAD
# ===========================================================================

with tab_upload:
    st.header("Upload Daily Report")
    st.markdown(
        """
        **Supported formats:** CSV, Excel (.xls / .xlsx)

        **Expected columns (daily sheet):**
        `Date`, `Bets`, `Wins`, `GGR`, `Bonuses`, `Deposits Amount`,
        `Deposits Count`, `Withdrawals Amount`, `Withdrawals Count`,
        `Active Players`, `New Players`

        **Game-level sheet** (optional, detected automatically):
        `Date`, `Game Name`, `Provider`, `Bets`, `Wins`, `GGR`, `Active Players`

        Duplicate dates are **upserted** (existing rows are overwritten).
        """
    )

    uploaded_file = st.file_uploader(
        "Choose a CSV or Excel file",
        type=["csv", "xls", "xlsx"],
        key="file_uploader",
    )

    overwrite_toggle = st.checkbox(
        "Overwrite existing data for matching dates", value=True
    )

    if uploaded_file is not None:
        if st.button("🚀 Process & Save", type="primary"):
            with st.spinner("Processing file…"):
                daily_df, game_df, warnings = process_upload(
                    uploaded_file.read(), uploaded_file.name
                )

            # Show warnings
            if warnings:
                with st.expander("⚠️ Validation warnings", expanded=True):
                    for w in warnings:
                        st.warning(w)

            # Save daily data
            if daily_df is not None and not daily_df.empty:
                daily_df = compute_kpis(daily_df)
                stats = upsert_daily_data(daily_df)
                st.success(
                    f"✅ Daily data saved: "
                    f"**{stats['inserted']}** inserted, "
                    f"**{stats['updated']}** updated, "
                    f"**{stats['errors']}** errors."
                )
                with st.expander("Preview daily data"):
                    preview = daily_df.copy()
                    if "date" in preview.columns:
                        preview["date"] = pd.to_datetime(preview["date"]).dt.strftime("%Y-%m-%d")
                    st.dataframe(preview, use_container_width=True)
            else:
                if not warnings:
                    st.info("No daily data found in the uploaded file.")

            # Save game data
            if game_df is not None and not game_df.empty:
                gstats = upsert_game_data(game_df)
                st.success(
                    f"🎮 Game data saved: "
                    f"**{gstats['inserted']}** inserted, "
                    f"**{gstats['updated']}** updated, "
                    f"**{gstats['errors']}** errors."
                )
                with st.expander("Preview game data"):
                    gpreview = game_df.copy()
                    if "date" in gpreview.columns:
                        gpreview["date"] = pd.to_datetime(gpreview["date"]).dt.strftime("%Y-%m-%d")
                    st.dataframe(gpreview, use_container_width=True)

    # ---------------------------------------------------------------------------
    # Sample CSV download
    # ---------------------------------------------------------------------------

    st.markdown("---")
    st.subheader("📥 Download Sample Template")

    sample_daily = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-02"],
            "Bets": [1_000_000, 1_050_000],
            "Wins": [850_000, 900_000],
            "GGR": [150_000, 150_000],
            "Bonuses": [20_000, 22_000],
            "Deposits Amount": [500_000, 520_000],
            "Deposits Count": [1200, 1250],
            "Withdrawals Amount": [200_000, 210_000],
            "Withdrawals Count": [800, 830],
            "Active Players": [5000, 5200],
            "New Players": [200, 220],
        }
    )

    sample_game = pd.DataFrame(
        {
            "Date": ["2024-01-01", "2024-01-01", "2024-01-02"],
            "Game Name": ["Starburst", "Book of Dead", "Starburst"],
            "Provider": ["NetEnt", "Play'n GO", "NetEnt"],
            "Bets": [100_000, 80_000, 110_000],
            "Wins": [85_000, 67_000, 93_000],
            "GGR": [15_000, 13_000, 17_000],
            "Active Players": [500, 400, 520],
        }
    )

    col_s1, col_s2 = st.columns(2)
    with col_s1:
        st.download_button(
            "⬇️ Sample Daily CSV",
            data=to_csv_bytes(sample_daily),
            file_name="sample_daily_report.csv",
            mime="text/csv",
        )
    with col_s2:
        st.download_button(
            "⬇️ Sample Excel (Daily + Game sheets)",
            data=to_excel_bytes({"Daily": sample_daily, "Game Data": sample_game}),
            file_name="sample_report.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        )

# ===========================================================================
# TAB 2 — MANUAL ENTRY
# ===========================================================================

with tab_manual:
    st.header("Manual Data Entry")
    st.markdown("Enter a single day's KPIs directly. Leave fields blank if unknown.")

    with st.form("manual_entry_form", clear_on_submit=True):
        col_a, col_b, col_c = st.columns(3)

        with col_a:
            entry_date = st.date_input("Date *", value=date.today())
            bets       = st.number_input("Bets / Turnover", min_value=0.0, step=1000.0)
            wins       = st.number_input("Wins", min_value=0.0, step=1000.0)
            ggr_input  = st.number_input("GGR (leave 0 to auto-calculate)", min_value=0.0, step=100.0)

        with col_b:
            bonuses        = st.number_input("Bonuses", min_value=0.0, step=100.0)
            dep_amount     = st.number_input("Deposits Amount", min_value=0.0, step=1000.0)
            dep_count      = st.number_input("Deposits Count", min_value=0, step=1)
            with_amount    = st.number_input("Withdrawals Amount", min_value=0.0, step=1000.0)
            with_count     = st.number_input("Withdrawals Count", min_value=0, step=1)

        with col_c:
            active_players = st.number_input("Active Players", min_value=0, step=1)
            new_players    = st.number_input("New Players", min_value=0, step=1)

        submitted = st.form_submit_button("💾 Save Entry", type="primary")

    if submitted:
        data = {
            "date": str(entry_date),
            "bets": bets or None,
            "wins": wins or None,
            "ggr": ggr_input or None,
            "bonuses": bonuses or None,
            "deposits_amount": dep_amount or None,
            "deposits_count": int(dep_count) if dep_count else None,
            "withdrawals_amount": with_amount or None,
            "withdrawals_count": int(with_count) if with_count else None,
            "active_players": int(active_players) if active_players else None,
            "new_players": int(new_players) if new_players else None,
        }

        cleaned_df, warnings = process_manual_entry(data)

        if warnings:
            for w in warnings:
                st.warning(w)

        if cleaned_df is not None and not cleaned_df.empty:
            cleaned_df = compute_kpis(cleaned_df)
            stats = upsert_daily_data(cleaned_df)
            if stats["errors"] == 0:
                st.success(
                    f"✅ Entry saved for **{entry_date}**. "
                    f"({'Updated existing record' if stats['updated'] else 'New record inserted'})"
                )
            else:
                st.error("Failed to save entry. Check the values and try again.")
        else:
            st.error("Could not process entry. Ensure the date is valid.")

# ===========================================================================
# TAB 3 — VIEW / EDIT / DELETE
# ===========================================================================

with tab_view:
    st.header("Stored Daily Data")

    stored = fetch_daily_data()

    if stored.empty:
        st.info("No records stored yet.")
    else:
        # Search / filter
        with st.expander("🔍 Filter options"):
            col_f1, col_f2 = st.columns(2)
            with col_f1:
                filter_from = st.date_input(
                    "From", value=stored["date"].min().date(), key="filter_from"
                )
            with col_f2:
                filter_to = st.date_input(
                    "To", value=stored["date"].max().date(), key="filter_to"
                )

        mask = (stored["date"].dt.date >= filter_from) & (stored["date"].dt.date <= filter_to)
        filtered = stored[mask].copy()

        display = filtered.copy()
        if "date" in display.columns:
            display["date"] = display["date"].dt.strftime("%Y-%m-%d")

        # Show editable columns via Streamlit's data editor
        st.markdown(f"**{len(display)} records** in selected range")

        edited = st.data_editor(
            display.drop(columns=["id", "created_at", "updated_at"], errors="ignore"),
            use_container_width=True,
            num_rows="dynamic",
            key="data_editor",
        )

        col_save, col_dl1, col_dl2 = st.columns([1, 1, 1])

        with col_save:
            if st.button("💾 Save edits", type="primary"):
                if not edited.empty:
                    to_save = compute_kpis(edited.copy())
                    stats = upsert_daily_data(to_save)
                    st.success(
                        f"Saved: {stats['inserted']} inserted, {stats['updated']} updated, "
                        f"{stats['errors']} errors."
                    )
                    st.rerun()

        with col_dl1:
            st.download_button(
                "⬇️ Export CSV",
                data=to_csv_bytes(filtered),
                file_name="casino_data_export.csv",
                mime="text/csv",
            )

        with col_dl2:
            st.download_button(
                "⬇️ Export Excel",
                data=to_excel_bytes({"Casino Data": filtered}),
                file_name="casino_data_export.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

        # Delete single record
        st.markdown("---")
        st.subheader("🗑️ Delete a Record")
        available_dates = sorted(filtered["date"].dt.strftime("%Y-%m-%d").tolist(), reverse=True)
        if available_dates:
            del_date = st.selectbox("Select date to delete", options=available_dates, key="del_date")
            if st.button("🗑️ Delete selected record", type="secondary"):
                if delete_daily_record(del_date):
                    st.success(f"Record for {del_date} deleted.")
                    st.rerun()
                else:
                    st.error("Could not delete record.")
