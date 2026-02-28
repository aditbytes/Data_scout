"""DataScout UI Components."""

# Submodules are imported directly by callers (e.g. app.py and results_display.py).
# Keeping this __init__ import-free avoids pulling in streamlit at package load time.

__all__ = [
    'render_upload_widget',
    'render_query_input',
    'render_results',
    'render_code_block',
    'render_preview',
    'render_visualization',
]
