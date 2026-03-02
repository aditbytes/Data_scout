"""
DataScout — Results Display Component (Enhanced).

Renders analysis results as a rich, vertically-stacked report with
executive summary, key findings, detailed analysis, charts, and code.
"""

from html import escape

import streamlit as st

try:
    from components.code_viewer import render_code_block
    from components.visualization import render_visualization
except ImportError:
    from streamlit_app.components.code_viewer import render_code_block
    from streamlit_app.components.visualization import render_visualization


def _safe_html_text(text: str) -> str:
    """Escape text for HTML injection and preserve line breaks."""
    if not text:
        return ''
    return escape(text).replace('\n', '<br>')


def render_results(response: dict, execution_time_ms: int = 0) -> None:
    """Render analysis results as a structured report.

    Args:
        response: Parsed agent response dict with keys:
            - explanation (str): General explanation text
            - executive_summary (str): 2-3 sentence overview
            - methodology (str): Analytical approach description
            - key_findings (list[str]): Bullet points of discoveries
            - detailed_analysis (str): Full analysis with tables
            - recommendations (list[str]): Action items
            - code (str): Generated Python code
            - results (str): Data tables and statistics
            - visualizations (list[str]): S3 URIs of generated charts
            - chart_images (list[dict]): Direct image bytes
            - next_steps (list[str]): Suggested follow-up analyses
        execution_time_ms: Query execution time in milliseconds.
    """
    st.markdown("---")

    # ── Section Header ─────────────────────────────────────────────────
    st.markdown("""
    <div style="display:flex; align-items:center; gap:10px; margin-bottom:1.25rem;">
        <span style="font-size:1.5rem;">📊</span>
        <span style="font-size:1.3rem; font-weight:800; color:var(--ds-text);
              letter-spacing:-0.02em;">Analysis Report</span>
    </div>
    """, unsafe_allow_html=True)

    # ── Execution Stats Bar ────────────────────────────────────────────
    if execution_time_ms > 0:
        time_str = (f"{execution_time_ms / 1000:.1f}s"
                    if execution_time_ms >= 1000
                    else f"{execution_time_ms}ms")
        st.markdown(f"""
        <div class="exec-stats-bar">
            <div class="exec-stat">
                <span class="stat-icon">⚡</span>
                <span>Execution Time:</span>
                <span class="stat-value">{time_str}</span>
            </div>
            <div class="exec-stat">
                <span class="stat-icon">🤖</span>
                <span>Model:</span>
                <span class="stat-value">Qwen3.5 - 397B-A17B</span>
            </div>
            <div class="exec-stat">
                <span class="stat-icon">🔬</span>
                <span>Engine:</span>
                <span class="stat-value">Amazon Bedrock</span>
            </div>
        </div>
        """, unsafe_allow_html=True)

    # ── 1. Executive Summary Card ──────────────────────────────────────
    summary = response.get('executive_summary', '')
    if summary:
        safe_summary = _safe_html_text(summary)
        st.markdown(f"""
        <div class="summary-card">
            <div class="summary-label">✨ Executive Summary</div>
            <div class="summary-text">{safe_summary}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── 2. Key Findings ────────────────────────────────────────────────
    findings = response.get('key_findings', [])
    if isinstance(findings, str):
        findings = [findings]
    if findings:
        findings_html = ""
        for i, finding in enumerate(findings, 1):
            safe_finding = _safe_html_text(str(finding))
            findings_html += f"""
<div class="finding-item">
    <div class="finding-number">{i}</div>
    <div class="finding-text">{safe_finding}</div>
</div>
"""
        st.markdown(f"""
<div class="report-section">
    <div class="report-section-header">
        <span class="section-icon">🔍</span>
        <span class="section-title">Key Findings</span>
    </div>
    <div class="report-section-body">
        {findings_html}
    </div>
</div>
""", unsafe_allow_html=True)

    # ── 3. Methodology ─────────────────────────────────────────────────
    methodology = response.get('methodology', '')
    if methodology:
        safe_methodology = _safe_html_text(methodology)
        st.markdown(f"""
        <div class="report-section">
            <div class="report-section-header">
                <span class="section-icon">🧪</span>
                <span class="section-title">Methodology</span>
            </div>
            <div class="methodology-block">{safe_methodology}</div>
        </div>
        """, unsafe_allow_html=True)

    # ── 4. Detailed Analysis (uses st.markdown for table rendering) ────
    analysis = response.get('detailed_analysis', '')
    explanation = response.get('explanation', '')
    display_text = analysis or explanation

    if display_text:
        st.markdown("""
        <div class="report-section">
            <div class="report-section-header">
                <span class="section-icon">📋</span>
                <span class="section-title">Detailed Analysis</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        # Use st.markdown for proper table rendering
        st.markdown(display_text)

    # If there's an explanation AND a detailed analysis, show explanation
    # separately as context
    if analysis and explanation and explanation != analysis:
        with st.expander("📝 Additional Context", expanded=False):
            st.markdown(explanation)

    # ── 5. Results Table ───────────────────────────────────────────────
    results = response.get('results', '')
    if results:
        st.markdown("""
        <div class="report-section">
            <div class="report-section-header">
                <span class="section-icon">📊</span>
                <span class="section-title">Data Results</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        st.markdown(results)

        st.download_button(
            label="📥 Download Results",
            data=results,
            file_name="datascout_results.txt",
            mime="text/plain"
        )

    # ── 6. Charts / Visualizations ─────────────────────────────────────
    visualizations = response.get('visualizations', [])
    chart_images = response.get('chart_images', [])
    if visualizations or chart_images:
        chart_count = len(chart_images) or len(visualizations)
        st.markdown(f"""
        <div class="report-section">
            <div class="report-section-header">
                <span class="section-icon">📈</span>
                <span class="section-title">Visualizations</span>
                <div class="chart-gallery-header">
                    <span class="chart-count">{chart_count} chart{'s' if chart_count > 1 else ''}</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        render_visualization(s3_uris=visualizations, chart_images=chart_images)

    # ── 7. Generated Code ──────────────────────────────────────────────
    code = response.get('code', '')
    if code:
        st.markdown("""
        <div class="report-section">
            <div class="report-section-header">
                <span class="section-icon">💻</span>
                <span class="section-title">Generated Code</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
        render_code_block(code)

    # ── 8. Recommendations / Next Steps ────────────────────────────────
    recommendations = response.get('recommendations', [])
    next_steps = response.get('next_steps', [])
    if isinstance(recommendations, str):
        recommendations = [recommendations]
    if isinstance(next_steps, str):
        next_steps = [next_steps]
    steps = recommendations or next_steps

    if steps:
        recs_html = ""
        for step in steps:
            safe_step = _safe_html_text(str(step))
            recs_html += f"""
<div class="recommendation-item">
    <span class="rec-icon">💡</span>
    <span class="rec-text">{safe_step}</span>
</div>
"""
        st.markdown(f"""
<div class="report-section">
    <div class="report-section-header">
        <span class="section-icon">🚀</span>
        <span class="section-title">Recommendations</span>
    </div>
    <div class="report-section-body">
        {recs_html}
    </div>
</div>
""", unsafe_allow_html=True)
