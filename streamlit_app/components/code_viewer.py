"""
DataScout — Code Viewer Component.

Displays generated Python code with syntax highlighting and a copy button.
"""

import streamlit as st


def render_code_block(code: str, language: str = 'python') -> None:
    """Display generated code with syntax highlighting.

    Features:
        - Syntax-highlighted Python code
        - Line numbers
        - Expandable/collapsible view
        - Copy-to-clipboard button

    Args:
        code: The source code string to display.
        language: Programming language for syntax highlighting (default: python).
    """
    if not code:
        st.info("No code to display.")
        return

    with st.expander("🔍 View Generated Code", expanded=True):
        st.code(code, language=language, line_numbers=True)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("📋 Copy Code", key=f"copy_{hash(code)}"):
                st.session_state['clipboard'] = code
                st.toast("✅ Code copied to clipboard!")
