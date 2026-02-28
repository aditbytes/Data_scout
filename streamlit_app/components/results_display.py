"""
DataScout — Results Display Component.

Renders analysis results with modern tabbed views for explanation, data, code, and charts.
"""

import streamlit as st

try:
    from components.code_viewer import render_code_block
    from components.visualization import render_visualization
except ImportError:
    from streamlit_app.components.code_viewer import render_code_block
    from streamlit_app.components.visualization import render_visualization


def render_results(response: dict) -> None:
    """Render analysis results with tabs for different views.

    Args:
        response: Parsed agent response dict with keys:
            - explanation (str): Plain-language analysis approach
            - code (str): Generated Python code
            - results (str): Data tables and statistics
            - visualizations (list[str]): S3 URIs of generated charts
            - next_steps (list[str]): Suggested follow-up analyses
    """
    st.markdown(
        '<div class="glass-card" style="margin-top:1.5rem;">',
        unsafe_allow_html=True
    )

    st.subheader("📈 Results")

    # Create tabbed view
    tab_explanation, tab_results, tab_code, tab_charts = st.tabs([
        "📝 Explanation",
        "📊 Results",
        "💻 Code",
        "📈 Charts"
    ])

    # Tab 1: Explanation
    with tab_explanation:
        explanation = response.get('explanation', '')
        if explanation:
            st.markdown(explanation)
        else:
            st.info("No explanation was provided for this analysis.")

    # Tab 2: Results
    with tab_results:
        results = response.get('results', '')
        if results:
            st.markdown(results)
        else:
            st.info("No tabular results were generated for this query.")

        # Download results as text
        if results:
            st.download_button(
                label="📥 Download Results",
                data=results,
                file_name="datascout_results.txt",
                mime="text/plain"
            )

    # Tab 3: Code
    with tab_code:
        code = response.get('code', '')
        if code:
            render_code_block(code)
        else:
            st.info("No code was generated for this query.")

    # Tab 4: Charts
    with tab_charts:
        visualizations = response.get('visualizations', [])
        chart_images = response.get('chart_images', [])
        if visualizations or chart_images:
            render_visualization(s3_uris=visualizations, chart_images=chart_images)
        else:
            st.info("No visualizations were generated for this query.")

    st.markdown('</div>', unsafe_allow_html=True)

    # Next steps suggestions as pills
    next_steps = response.get('next_steps', [])
    if next_steps:
        pills_html = ''.join(
            f'<span class="suggestion-pill"><span class="pill-icon">→</span> {step}</span>'
            for step in next_steps
        )
        st.markdown(
            f'<div class="suggestion-pills" style="margin-top:1rem;">{pills_html}</div>',
            unsafe_allow_html=True
        )
