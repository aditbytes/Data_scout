"""
DataScout — Main Application Entry Point.

Streamlit-based frontend for autonomous enterprise data analysis
powered by Qwen3.5 - 397B-A17B on Amazon Bedrock.
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
import random
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
            'DataScout betaversion 2 — Autonomous Enterprise Data Analyst\n'
            'Powered by Qwen3.5 - 397B-A17B on Amazon Bedrock'
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
            instant insights powered by Qwen3.5 - 397B-A17B
        </div>
    </div>
    """, unsafe_allow_html=True)


def render_night_sky_theme(seed: str) -> None:
    """Inject a lightweight animated night-sky background layer."""
    rng = random.Random(seed)

    stars_html = []
    for _ in range(72):
        left = rng.uniform(0, 100)
        top = rng.uniform(0, 82)
        size = rng.uniform(1.0, 3.2)
        opacity = rng.uniform(0.30, 0.95)
        delay = rng.uniform(0, 8)
        duration = rng.uniform(2.8, 7.0)
        stars_html.append(
            '<span class="sky-star" '
            f'style="left:{left:.2f}%;top:{top:.2f}%;'
            f'width:{size:.2f}px;height:{size:.2f}px;'
            f'opacity:{opacity:.2f};animation-delay:-{delay:.2f}s;'
            f'animation-duration:{duration:.2f}s;"></span>'
        )

    shooting_html = []
    for _ in range(2):
        top = rng.uniform(8, 34)
        left = rng.uniform(62, 98)
        delay = rng.uniform(0.5, 7.5)
        duration = rng.uniform(8.0, 12.0)
        shooting_html.append(
            '<span class="shooting-star" '
            f'style="top:{top:.2f}%;left:{left:.2f}%;'
            f'animation-delay:{delay:.2f}s;animation-duration:{duration:.2f}s;"></span>'
        )

    st.markdown(
        f"""
        <style>
        .night-sky-layer {{
            position: fixed;
            inset: 0;
            overflow: hidden;
            pointer-events: none;
            z-index: 0;
            background:
                radial-gradient(circle at 18% 16%, rgba(18, 53, 92, 0.26), transparent 42%),
                radial-gradient(circle at 82% 8%, rgba(30, 88, 132, 0.18), transparent 38%),
                linear-gradient(180deg, #030712 0%, #050b16 45%, #06070b 100%);
        }}

        .stApp,
        [data-testid="stAppViewContainer"] {{
            position: relative;
        }}

        .main .block-container,
        .app-footer {{
            position: relative;
            z-index: 2;
        }}

        .sky-star {{
            position: absolute;
            border-radius: 50%;
            background: #f5f9ff;
            box-shadow: 0 0 8px rgba(214, 235, 255, 0.8);
            animation-name: dsTwinkle;
            animation-timing-function: ease-in-out;
            animation-iteration-count: infinite;
            will-change: opacity, transform;
        }}

        @keyframes dsTwinkle {{
            0%, 100% {{
                opacity: 0.2;
                transform: scale(0.85);
            }}
            50% {{
                opacity: 1;
                transform: scale(1.35);
            }}
        }}

        .moon-glow {{
            position: absolute;
            top: 38px;
            right: 46px;
            width: 118px;
            height: 118px;
            border-radius: 50%;
            background: radial-gradient(circle at 35% 35%, rgba(210, 233, 255, 0.55), rgba(132, 179, 235, 0.10) 62%, transparent 70%);
            filter: blur(2px);
        }}

        .moon {{
            position: absolute;
            top: 56px;
            right: 66px;
            width: 70px;
            height: 70px;
            border-radius: 50%;
            background: radial-gradient(circle at 32% 30%, #f9fdff 0%, #d7e9fb 55%, #bfd6ec 100%);
            box-shadow: 0 0 16px rgba(198, 230, 255, 0.65);
        }}

        .shooting-star {{
            position: absolute;
            width: 140px;
            height: 2px;
            opacity: 0;
            border-radius: 999px;
            background: linear-gradient(90deg, rgba(255, 255, 255, 0.0), rgba(193, 230, 255, 0.95), rgba(255, 255, 255, 0.0));
            transform: rotate(-28deg);
            animation-name: dsShoot;
            animation-timing-function: linear;
            animation-iteration-count: infinite;
            will-change: opacity, transform;
        }}

        @keyframes dsShoot {{
            0% {{
                opacity: 0;
                transform: translate3d(0, 0, 0) rotate(-28deg) scaleX(0.35);
            }}
            8% {{
                opacity: 0.85;
            }}
            38% {{
                opacity: 0.75;
                transform: translate3d(-420px, 230px, 0) rotate(-28deg) scaleX(1);
            }}
            100% {{
                opacity: 0;
                transform: translate3d(-420px, 230px, 0) rotate(-28deg) scaleX(0.85);
            }}
        }}

        .skyline {{
            position: absolute;
            left: 0;
            right: 0;
            bottom: 0;
            height: 150px;
            background: linear-gradient(180deg, rgba(4, 6, 10, 0.05) 0%, rgba(4, 7, 12, 0.9) 36%, #03050a 100%);
            clip-path: polygon(
                0% 100%, 0% 62%, 4% 62%, 4% 52%, 7% 52%, 7% 68%, 11% 68%, 11% 45%, 16% 45%, 16% 73%,
                20% 73%, 20% 57%, 24% 57%, 24% 70%, 28% 70%, 28% 43%, 33% 43%, 33% 74%, 38% 74%, 38% 56%,
                43% 56%, 43% 72%, 48% 72%, 48% 41%, 54% 41%, 54% 76%, 58% 76%, 58% 54%, 63% 54%, 63% 71%,
                68% 71%, 68% 47%, 73% 47%, 73% 75%, 77% 75%, 77% 52%, 82% 52%, 82% 72%, 87% 72%, 87% 44%,
                92% 44%, 92% 68%, 96% 68%, 96% 58%, 100% 58%, 100% 100%
            );
        }}

        .skyline::after {{
            content: "";
            position: absolute;
            inset: 0;
            opacity: 0.12;
            background:
                repeating-linear-gradient(90deg, transparent 0 10px, rgba(178, 213, 240, 0.45) 10px 11px, transparent 11px 24px),
                linear-gradient(180deg, transparent 0%, rgba(170, 205, 230, 0.32) 62%, transparent 100%);
        }}

        @media (max-width: 768px) {{
            .moon-glow {{
                top: 28px;
                right: 24px;
                width: 94px;
                height: 94px;
            }}

            .moon {{
                top: 42px;
                right: 40px;
                width: 56px;
                height: 56px;
            }}

            .skyline {{
                height: 110px;
            }}

            .shooting-star {{
                width: 92px;
            }}
        }}
        </style>
        <div class="night-sky-layer" aria-hidden="true">
            <div class="moon-glow"></div>
            <div class="moon"></div>
            {''.join(stars_html)}
            {''.join(shooting_html)}
            <div class="skyline"></div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_footer() -> None:
    """Render the modern footer with gradient branding."""
    st.markdown("""
    <div class="app-footer">
        <span class="footer-brand">DataScout</span> version 5 (beta) &nbsp;·&nbsp;
        Powered by Qwen3.5 - 397B-A17B on Amazon Bedrock
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

    # Render ambient background layer before UI components.
    render_night_sky_theme(st.session_state.session_id)

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
            render_results(
                latest['response'],
                execution_time_ms=latest.get('execution_time_ms', 0)
            )

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
                render_results(
                    entry['response'],
                    execution_time_ms=entry.get('execution_time_ms', 0)
                )

    # ── Footer ────────────────────────────────────────────────────────────
    render_footer()


if __name__ == '__main__':
    main()
