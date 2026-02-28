"""
DataScout — Query Input Component.

Renders a modern chat-style query input with suggestion pills.
"""

from typing import Optional, List, Dict

import streamlit as st


def generate_suggestions(columns: List[str], dtypes: Dict[str, str]) -> List[str]:
    """Generate contextual query suggestions based on dataset schema.

    Args:
        columns: List of column names.
        dtypes: Dict mapping column name to dtype string.

    Returns:
        Up to 5 query suggestions tailored to the dataset.
    """
    suggestions = []

    numeric_cols = [c for c, d in dtypes.items() if 'int' in d or 'float' in d]
    categorical_cols = [c for c, d in dtypes.items() if 'object' in d or 'category' in d]
    date_cols = [c for c, d in dtypes.items() if 'datetime' in d]

    if numeric_cols and categorical_cols:
        suggestions.append(
            f"Average {numeric_cols[0]} by {categorical_cols[0]}"
        )

    if numeric_cols:
        suggestions.append(f"Top 10 by {numeric_cols[0]}")
        suggestions.append(f"Distribution of {numeric_cols[0]}")

    if date_cols and numeric_cols:
        suggestions.append(
            f"Trends over {date_cols[0]}"
        )

    if len(numeric_cols) >= 2:
        suggestions.append(
            f"Correlation: {numeric_cols[0]} vs {numeric_cols[1]}"
        )

    return suggestions[:5]


def _render_suggestion_pills(suggestions: List[str]) -> None:
    """Render suggestion pills as styled HTML."""
    icons = ["📊", "🔝", "📈", "📉", "🔗"]
    pills_html = ""
    for i, s in enumerate(suggestions):
        icon = icons[i % len(icons)]
        pills_html += (
            f'<span class="suggestion-pill">'
            f'<span class="pill-icon">{icon}</span> {s}'
            f'</span>'
        )
    st.markdown(
        f'<div class="suggestion-pills">{pills_html}</div>',
        unsafe_allow_html=True
    )


def render_query_input(dataset_loaded: bool) -> Optional[str]:
    """Render the natural language query input field.

    Args:
        dataset_loaded: Whether a dataset has been uploaded and is ready.

    Returns:
        The user's query string, or None if no query was submitted.
    """
    if not dataset_loaded:
        st.markdown(
            '<div class="glass-card" style="text-align:center; padding:2rem;">'
            '<p style="color: var(--ds-text-muted); margin:0;">📁 Upload a dataset above to get started</p>'
            '</div>',
            unsafe_allow_html=True
        )
        return None

    # Show suggestions if metadata is available
    metadata = st.session_state.get('dataset_metadata')
    if metadata:
        suggestions = generate_suggestions(
            metadata.get('columns', []),
            metadata.get('dtypes', {})
        )
        if suggestions:
            _render_suggestion_pills(suggestions)

    # Query input — chat-style text area
    query = st.text_area(
        "Your question",
        placeholder="Describe what you want to analyze...",
        key="query_input",
        max_chars=500,
        height=100,
        label_visibility="collapsed"
    )

    # Submit button — right-aligned
    col1, col2 = st.columns([5, 1])
    with col2:
        submitted = st.button("🚀 Analyze", type="primary", use_container_width=True)

    if submitted and query and query.strip():
        return query.strip()

    return None
