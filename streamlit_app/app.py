"""
DataScout — Main Application Entry Point.

Streamlit-based frontend for autonomous enterprise data analysis
powered by Amazon Nova Pro on Amazon Bedrock.
"""

import sys
from pathlib import Path

# Streamlit adds the script's own directory to sys.path, so direct imports work.
# Also ensure the project root is present for any absolute references.
_script_dir = Path(__file__).resolve().parent        # .../Data_scout/streamlit_app
_project_root = _script_dir.parent                  # .../Data_scout
for _p in [str(_script_dir), str(_project_root)]:
    if _p not in sys.path:
        sys.path.insert(0, _p)

import streamlit as st
import uuid
from datetime import datetime, UTC

from config import Config
from services.bedrock_client import BedrockAgentClient
from services.s3_handler import S3Handler
from services.dynamodb_handler import DynamoDBHandler
from components.file_upload import render_upload_widget
from components.query_input import render_query_input
from components.results_display import render_results
from components.dataset_preview import render_preview
from utils.error_handler import handle_error
from utils.logger import log_query_execution, log_dataset_upload

# ── Page Configuration ────────────────────────────────────────────────────────
st.set_page_config(
    page_title="DataScout — Enterprise Data Analyst",
    page_icon="🔬",
    layout="wide",
    initial_sidebar_state="collapsed",
    menu_items={
        'Get Help': 'https://docs.datascout.ai',
        'Report a bug': 'mailto:support@datascout.ai',
        'About': (
            'DataScout v1.0 — Autonomous Enterprise Data Analyst\n'
            'Powered by Amazon Nova Pro on Amazon Bedrock'
        )
    }
)

# ── Load Custom CSS ───────────────────────────────────────────────────────────
css_path = Path(__file__).parent / "assets" / "styles.css"
if css_path.exists():
    with open(css_path) as f:
        st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)


def render_hero() -> None:
    """Render the modern hero section with badge, gradient title, and subtitle."""
    st.markdown("""
    <div class="hero-container">
        <div class="hero-badge">
            <span class="dot"></span>
            DataScout Project
        </div>
        <div class="hero-title">Autonomous Data Intelligence</div>
        <div class="hero-subtitle">
            Upload your datasets, ask natural-language questions, and get
            instant insights powered by Amazon Nova Pro
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_footer() -> None:
    """Render the modern footer with gradient branding."""
    st.markdown("""
    <div class="app-footer">
        <span class="footer-brand">DataScout</span> v1.0 &nbsp;·&nbsp;
        Powered by Amazon Nova Pro on Amazon Bedrock
    </div>
    """, unsafe_allow_html=True)


def initialize_session() -> None:
    """Initialize session state with defaults on first page load."""
    defaults = {
        'session_id': str(uuid.uuid4()),
        'session_created_at': datetime.now(UTC),
        'dataset_loaded': False,
        'dataset_s3_uri': None,
        'dataset_metadata': None,
        'conversation_history': [],
        'current_query': '',
        'is_processing': False,
        'last_error': None,
        'active_tab': 'Explanation'
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def main() -> None:
    """Main application entry point."""
    # Validate configuration
    Config.validate()

    # Initialize session
    initialize_session()

    # Initialize services
    bedrock = BedrockAgentClient()
    s3 = S3Handler()
    dynamodb = DynamoDBHandler()

    # ── Hero Section ──────────────────────────────────────────────────────
    render_hero()

    # ── Section 1: File Upload ────────────────────────────────────────────
    uploaded_file = render_upload_widget()

    if uploaded_file and not st.session_state.dataset_loaded:
        with st.spinner("📤 Uploading and analyzing dataset..."):
            try:
                # Upload to S3
                s3_uri = s3.upload_dataset(
                    uploaded_file,
                    st.session_state.session_id
                )
                st.session_state.dataset_s3_uri = s3_uri

                # Extract metadata
                metadata = s3.get_dataset_metadata(s3_uri)
                st.session_state.dataset_metadata = metadata
                st.session_state.dataset_loaded = True

                # Log upload event
                log_dataset_upload(
                    st.session_state.session_id,
                    metadata['filename'],
                    metadata['rows'],
                    len(metadata['columns']),
                    metadata['size_mb']
                )

                st.success(f"✅ Dataset loaded: **{metadata['filename']}** — "
                           f"{metadata['rows']:,} rows, {len(metadata['columns'])} columns")

                # Persist session to DynamoDB
                dynamodb.save_session(
                    st.session_state.session_id,
                    {
                        'dataset_loaded': True,
                        'filename': metadata['filename'],
                        'rows': metadata['rows'],
                        'num_columns': len(metadata['columns']),
                    }
                )
            except Exception as e:
                handle_error(e)

    # ── Section 2: Dataset Preview ────────────────────────────────────────
    if st.session_state.dataset_loaded:
        render_preview(st.session_state.dataset_metadata)

    # ── Section 3: Query Input ────────────────────────────────────────────
    query = render_query_input(st.session_state.dataset_loaded)

    if query and not st.session_state.is_processing:
        st.session_state.is_processing = True
        start_time = datetime.now(UTC)

        with st.spinner("🔍 Analyzing your data..."):
            try:
                response = bedrock.invoke_agent(
                    query=query,
                    session_id=st.session_state.session_id,
                    dataset_uri=st.session_state.dataset_s3_uri
                )

                execution_time = int(
                    (datetime.now(UTC) - start_time).total_seconds() * 1000
                )

                # Store in conversation history
                st.session_state.conversation_history.append({
                    'id': str(uuid.uuid4()),
                    'query': query,
                    'response': response,
                    'execution_time_ms': execution_time,
                    'success': True,
                    'timestamp': datetime.now(UTC)
                })

                # Log query execution
                log_query_execution(
                    st.session_state.session_id,
                    query, execution_time, True
                )

                # Persist to DynamoDB
                dynamodb.save_query(
                    session_id=st.session_state.session_id,
                    query=query,
                    response=response,
                    execution_time_ms=execution_time,
                    success=True,
                )

            except Exception as e:
                handle_error(e)
                log_query_execution(
                    st.session_state.session_id,
                    query, 0, False, error=e
                )
            finally:
                st.session_state.is_processing = False

    # ── Section 4: Results Display ────────────────────────────────────────
    if st.session_state.conversation_history:
        latest = st.session_state.conversation_history[-1]
        if latest['success']:
            render_results(latest['response'])

    # ── Section 5: Conversation History ───────────────────────────────────
    if len(st.session_state.conversation_history) > 1:
        st.markdown("---")
        st.subheader("📜 Query History")
        for i, entry in enumerate(
            reversed(st.session_state.conversation_history[:-1]), 1
        ):
            status = "✅" if entry['success'] else "❌"
            time_str = f"{entry['execution_time_ms']}ms"
            with st.expander(f"{status} Q{i}: {entry['query']} ({time_str})"):
                render_results(entry['response'])

    # ── Footer ────────────────────────────────────────────────────────────
    render_footer()


if __name__ == '__main__':
    main()
