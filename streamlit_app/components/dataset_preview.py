"""
DataScout — Dataset Preview Component.

Shows dataset summary metrics in glassmorphic cards and an expandable row preview.
"""

import pandas as pd
import streamlit as st


def render_preview(metadata: dict) -> None:
    """Show dataset summary and optional row preview.

    Display:
        - Compact info bar: filename, rows, columns, size (glassmorphic cards)
        - Expandable preview: first 5 rows as a table
        - Column details: name, type, null count
        - Data quality indicators: missing value warnings

    Args:
        metadata: Dataset metadata dict with keys:
            filename, rows, columns, dtypes, size_mb, preview, null_counts
    """
    if not metadata:
        return

    # ── Compact Metric Bar ────────────────────────────────────────────────
    cols = st.columns(4)
    cols[0].metric("📁 File", metadata.get('filename', 'Unknown'))
    cols[1].metric("📏 Rows", f"{metadata.get('rows', 0):,}")
    cols[2].metric("📐 Columns", len(metadata.get('columns', [])))
    cols[3].metric("💾 Size", f"{metadata.get('size_mb', 0):.1f} MB")

    # ── Expandable Preview ────────────────────────────────────────────────
    with st.expander("🔎 Preview Dataset"):
        preview_data = metadata.get('preview', [])
        if preview_data:
            st.dataframe(
                pd.DataFrame(preview_data),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("No preview data available.")

        # Column details table
        columns = metadata.get('columns', [])
        dtypes = metadata.get('dtypes', {})
        null_counts = metadata.get('null_counts', {})

        if columns:
            st.markdown("**Column Details**")
            col_info = pd.DataFrame({
                'Column': columns,
                'Type': [dtypes.get(c, 'unknown') for c in columns],
                'Nulls': [null_counts.get(c, 0) for c in columns]
            })
            st.table(col_info)

            # Data quality warnings
            high_null_cols = [
                c for c in columns
                if null_counts.get(c, 0) > 0
            ]
            if high_null_cols:
                total_rows = metadata.get('rows', 1)
                for col in high_null_cols:
                    null_pct = (null_counts[col] / total_rows) * 100
                    if null_pct > 50:
                        st.warning(f"⚠️ Column **{col}** has {null_pct:.0f}% missing values")
                    elif null_pct > 10:
                        st.caption(f"ℹ️ Column **{col}** has {null_pct:.0f}% missing values")
