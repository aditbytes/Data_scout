# DataScout — Frontend Specification

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Overview

The DataScout frontend is a **Streamlit-based** single-page web application that provides an intuitive interface for non-technical users to upload datasets, ask natural language questions, and receive accurate analytical results powered by AI-driven code execution.

### 1.1 Design Principles
- **Zero Technical Knowledge Required** — Users interact only through natural language and file uploads
- **Full Transparency** — All generated code is visible and copyable
- **Progressive Disclosure** — Simple interface; advanced details available on demand
- **Real-Time Feedback** — Spinners, progress indicators, and streaming responses
- **Error Resilience** — Clear, actionable error messages for every failure mode

### 1.2 Technology Stack

| Component | Technology | Version |
|-----------|-----------|---------|
| Framework | Streamlit | ≥ 1.25.0 |
| Language | Python | 3.9+ |
| Hosting | AWS App Runner | Managed |
| Styling | Streamlit native + custom CSS | — |
| Charts | matplotlib / seaborn (server-rendered PNG) | — |
| State | Streamlit `session_state` | Built-in |

---

## 2. Page Architecture

### 2.1 Single-Page Layout

```
┌────────────────────────────────────────────────────────────┐
│ 🔬 DataScout — Autonomous Enterprise Data Analyst          │
│ ─────────────────────────────────────────────────────────── │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📁 UPLOAD SECTION                                      │ │
│ │ [Drag and drop or browse] .csv .xlsx .json             │ │
│ │ Max 100MB                                               │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📊 DATASET INFO BAR                                    │ │
│ │ sales_data.csv • 1,234 rows • 8 columns • 2.3 MB     │ │
│ │ [Show Preview ▼]                                       │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 💬 QUERY INPUT                                         │ │
│ │ ┌──────────────────────────────────────────────┐ [Ask] │ │
│ │ │ What is the average revenue by region?        │       │ │
│ │ └──────────────────────────────────────────────┘       │ │
│ │ Suggestions: Top products | Monthly trends | Outliers  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📈 RESULTS AREA                                        │ │
│ │                                                         │ │
│ │ [Explanation Tab] [Results Tab] [Code Tab] [Chart Tab] │ │
│ │ ─────────────────────────────────────────────────────── │ │
│ │                                                         │ │
│ │  Analysis: Average Revenue by Region                   │ │
│ │                                                         │ │
│ │  Region    | Average Revenue                           │ │
│ │  ──────────┼────────────────                           │ │
│ │  North     | $145,234.56                               │ │
│ │  South     | $132,890.12                               │ │
│ │  East      | $156,432.87                               │ │
│ │  West      | $141,098.34                               │ │
│ │                                                         │ │
│ │  [📊 Bar Chart]                                        │ │
│ │                                                         │ │
│ │  [Download CSV] [Download Chart] [Copy Code]           │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ┌────────────────────────────────────────────────────────┐ │
│ │ 📜 CONVERSATION HISTORY                                │ │
│ │ ─ Q1: "What is the average revenue by region?" ✅      │ │
│ │ ─ Q2: "Show me the top 5 products" ✅                  │ │
│ └────────────────────────────────────────────────────────┘ │
│                                                             │
│ ──────────────────────────────────────────────────────────  │
│ ⓘ DataScout v1.0 • Powered by Claude 3.5 Sonnet           │
└────────────────────────────────────────────────────────────┘
```

---

## 3. Component Specifications

### 3.1 File Upload Component

**File:** `streamlit_app/components/file_upload.py`

```python
def render_upload_widget() -> Optional[UploadedFile]:
    """
    Render the file upload widget.

    Features:
    - Drag-and-drop support
    - File format validation (.csv, .xlsx, .json)
    - File size validation (max 100MB)
    - Upload progress indicator
    - Success/error feedback

    Returns:
        UploadedFile object or None
    """
```

**Behavior:**
| State | Display |
|-------|---------|
| No file | Drag-and-drop zone with accepted formats |
| Uploading | Progress bar with percentage |
| Success | ✅ Green success message + dataset metadata |
| Error | ❌ Red error with specific issue and suggestion |
| File loaded | Compact info bar showing filename, rows, columns |

**Validation Rules:**
- Accepted formats: `.csv`, `.xlsx`, `.xls`, `.json`
- Max file size: 100 MB
- File must be readable by pandas
- Must have at least 1 valid column
- Column names sanitized for Python compatibility

### 3.2 Query Input Component

**File:** `streamlit_app/components/query_input.py`

```python
def render_query_input(dataset_loaded: bool) -> Optional[str]:
    """
    Render the natural language query input.

    Features:
    - Text input with placeholder examples
    - Disabled when no dataset is loaded
    - Query suggestions based on dataset schema
    - Submit button + Enter key support
    - Character limit indicator

    Args:
        dataset_loaded: Whether a dataset has been uploaded

    Returns:
        User query string or None
    """
```

**Query Suggestions (Auto-Generated from Schema):**
```python
def generate_suggestions(columns: list, dtypes: dict) -> list:
    """Generate contextual query suggestions based on dataset."""
    suggestions = []

    # Find numeric columns for aggregation suggestions
    numeric_cols = [c for c, d in dtypes.items() if 'int' in d or 'float' in d]
    categorical_cols = [c for c, d in dtypes.items() if 'object' in d]
    date_cols = [c for c, d in dtypes.items() if 'datetime' in d]

    if numeric_cols and categorical_cols:
        suggestions.append(
            f"What is the average {numeric_cols[0]} by {categorical_cols[0]}?"
        )

    if numeric_cols:
        suggestions.append(f"Show me the top 10 rows by {numeric_cols[0]}")
        suggestions.append(f"What is the distribution of {numeric_cols[0]}?")

    if date_cols and numeric_cols:
        suggestions.append(
            f"Show me {numeric_cols[0]} trends over {date_cols[0]}"
        )

    return suggestions[:5]
```

### 3.3 Results Display Component

**File:** `streamlit_app/components/results_display.py`

```python
def render_results(response: dict) -> None:
    """
    Render analysis results with tabs for different views.

    Args:
        response: Parsed agent response with keys:
            - explanation: str
            - code: str
            - results: str
            - visualizations: list[str]  (S3 URIs)
            - next_steps: list[str]

    Display Structure:
        Tab 1 — Explanation: Plain-language analysis approach
        Tab 2 — Results: Data tables and statistics
        Tab 3 — Code: Syntax-highlighted Python code
        Tab 4 — Visualization: Charts and graphs
    """
```

**Tab Details:**

| Tab | Content | Features |
|-----|---------|----------|
| 📝 Explanation | Plain-text analytical approach | Markdown rendering |
| 📊 Results | Data tables, statistics, findings | Sortable tables, number formatting |
| 💻 Code | Generated Python code | Syntax highlighting, copy button |
| 📈 Charts | Matplotlib/Seaborn visualizations | Full-size display, download button |

### 3.4 Code Viewer Component

**File:** `streamlit_app/components/code_viewer.py`

```python
def render_code_block(code: str, language: str = 'python') -> None:
    """
    Display generated code with syntax highlighting.

    Features:
    - Syntax-highlighted Python code
    - Line numbers
    - Copy-to-clipboard button
    - Expandable/collapsible view
    - Code explanation annotations (optional)
    """
    with st.expander("🔍 View Generated Code", expanded=True):
        st.code(code, language=language, line_numbers=True)

        col1, col2 = st.columns([1, 5])
        with col1:
            if st.button("📋 Copy Code"):
                st.session_state.clipboard = code
                st.toast("Code copied to clipboard!")
```

### 3.5 Dataset Preview Component

**File:** `streamlit_app/components/dataset_preview.py`

```python
def render_preview(metadata: dict) -> None:
    """
    Show dataset summary and optional row preview.

    Display:
    - Compact info bar: filename, rows, columns, size
    - Expandable preview: first 5 rows as table
    - Column details: name, type, null count
    - Data quality indicators: missing value warnings
    """
    # Compact info bar
    cols = st.columns(4)
    cols[0].metric("📁 File", metadata['filename'])
    cols[1].metric("📏 Rows", f"{metadata['rows']:,}")
    cols[2].metric("📐 Columns", len(metadata['columns']))
    cols[3].metric("💾 Size", f"{metadata['size_mb']:.1f} MB")

    # Expandable preview
    with st.expander("Preview Dataset"):
        st.dataframe(pd.DataFrame(metadata['preview']), use_container_width=True)

        # Column info
        st.subheader("Column Details")
        col_info = pd.DataFrame({
            'Column': metadata['columns'],
            'Type': [metadata['dtypes'][c] for c in metadata['columns']],
            'Nulls': [metadata['null_counts'].get(c, 0) for c in metadata['columns']]
        })
        st.table(col_info)
```

### 3.6 Visualization Component

**File:** `streamlit_app/components/visualization.py`

```python
def render_visualization(s3_uris: list, s3_handler: S3Handler) -> None:
    """
    Download and display chart images from S3.

    Features:
    - Auto-download from S3
    - Full-width image display
    - Download button for each chart
    - Caption with chart description
    """
    for i, uri in enumerate(s3_uris):
        image_bytes = s3_handler.download_artifact(uri)
        st.image(image_bytes, caption=f"Chart {i + 1}", use_column_width=True)

        st.download_button(
            label=f"📥 Download Chart {i + 1}",
            data=image_bytes,
            file_name=f"datascout_chart_{i + 1}.png",
            mime="image/png"
        )
```

---

## 4. Session State Management

### 4.1 State Structure

```python
# Complete session_state schema
st.session_state = {
    # Session identity
    'session_id': str,                    # UUID for Bedrock session
    'session_created_at': datetime,       # Session start time

    # Dataset state
    'dataset_loaded': bool,               # Is a dataset uploaded?
    'dataset_s3_uri': str,                # S3 URI of uploaded dataset
    'dataset_metadata': {                  # Extracted metadata
        'filename': str,
        'rows': int,
        'columns': list[str],
        'dtypes': dict[str, str],
        'size_mb': float,
        'preview': list[dict],
        'null_counts': dict[str, int]
    },

    # Conversation state
    'conversation_history': [              # All query-response pairs
        {
            'id': str,                     # Unique query ID
            'query': str,                  # User's question
            'response': {
                'explanation': str,
                'code': str,
                'results': str,
                'visualizations': list[str],
                'next_steps': list[str]
            },
            'execution_time_ms': int,
            'success': bool,
            'timestamp': datetime
        }
    ],

    # UI state
    'current_query': str,                  # Active query being processed
    'is_processing': bool,                 # Is a query in flight?
    'last_error': str,                     # Last error message (if any)
    'active_tab': str,                     # Active results tab
}
```

### 4.2 State Initialization

```python
def initialize_session():
    """Initialize session state with defaults on first load."""
    defaults = {
        'session_id': str(uuid.uuid4()),
        'session_created_at': datetime.utcnow(),
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
```

---

## 5. User Flow Specifications

### 5.1 First-Time User Flow

```
1. User opens DataScout URL
       ↓
2. Page loads with upload widget and disabled query input
       ↓
3. User drags a CSV file into the upload zone
       ↓
4. System validates → uploads to S3 → extracts metadata
       ↓
5. Dataset info bar appears (filename, rows, columns, size)
       ↓
6. Query input is enabled with auto-generated suggestions
       ↓
7. User types: "What are the top 5 products by revenue?"
       ↓
8. System shows spinner: "Analyzing your data..."
       ↓
9. Results appear in tabbed view:
   - Explanation of approach
   - Data table with results
   - Generated Python code
   - Bar chart visualization
       ↓
10. User asks follow-up: "Show me the monthly trend for those products"
       ↓
11. Agent uses session context → returns trend analysis
```

### 5.2 Error Recovery Flow

```
User uploads unsupported file (.pdf)
       ↓
Error displayed:
  ⚠️ Unsupported File Format
  DataScout supports CSV, Excel (.xlsx), and JSON formats.
  💡 Convert your file to one of these formats and try again.
       ↓
User uploads correct .csv file
       ↓
Normal flow continues
```

---

## 6. Responsive Design

### 6.1 Browser Support

| Browser | Version | Status |
|---------|---------|--------|
| Chrome | Latest 2 versions | ✅ Full support |
| Firefox | Latest 2 versions | ✅ Full support |
| Safari | Latest 2 versions | ✅ Full support |
| Edge | Latest 2 versions | ✅ Full support |
| Mobile browsers | — | ⚠️ Functional (not optimized) |

### 6.2 Viewport Breakpoints

| Screen | Width | Layout |
|--------|-------|--------|
| Desktop Large | ≥ 1200px | Full layout, side-by-side elements |
| Desktop | ≥ 992px | Full layout |
| Tablet | ≥ 768px | Stacked layout, full-width components |
| Mobile | < 768px | Single column, compact view |

### 6.3 Custom CSS

```css
/* streamlit_app/assets/styles.css */

/* DataScout theme overrides */
:root {
    --ds-primary: #1E3A5F;
    --ds-secondary: #4A90D9;
    --ds-accent: #2ECC71;
    --ds-background: #F8FAFC;
    --ds-surface: #FFFFFF;
    --ds-text: #1A1A2E;
    --ds-text-secondary: #6C757D;
    --ds-error: #E74C3C;
    --ds-success: #2ECC71;
    --ds-warning: #F39C12;
}

/* Header styling */
.main .block-container {
    max-width: 1200px;
    padding: 2rem 1rem;
}

/* Upload zone */
.stFileUploader > div {
    border: 2px dashed var(--ds-secondary);
    border-radius: 12px;
    padding: 2rem;
    background: var(--ds-background);
}

/* Results card */
.results-card {
    background: var(--ds-surface);
    border: 1px solid #E9ECEF;
    border-radius: 12px;
    padding: 1.5rem;
    box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
}

/* Code block styling */
.stCodeBlock {
    border-radius: 8px;
    font-size: 14px;
}

/* Metric cards */
.stMetric {
    background: var(--ds-background);
    border-radius: 8px;
    padding: 0.5rem;
}

/* Loading animation */
.stSpinner > div {
    color: var(--ds-secondary);
}
```

---

## 7. Accessibility (WCAG 2.1 Level AA)

### 7.1 Current Implementation

| Feature | Status | Notes |
|---------|--------|-------|
| Keyboard navigation | ✅ | Streamlit native support |
| Screen reader support | ⚠️ | Partial (Streamlit limitation) |
| Color contrast (4.5:1) | ✅ | Verified via custom CSS |
| Alt text for images | ✅ | Charts include captions |
| Focus indicators | ✅ | Streamlit default styling |
| Error announcements | ⚠️ | Planned for Phase 2 |

### 7.2 Planned Improvements (Phase 2)
- ARIA labels for custom components
- Screen reader announcements for query results
- High contrast mode toggle
- Font size adjustment
- Keyboard shortcuts for common actions

---

## 8. Performance Requirements

| Metric | Target | Notes |
|--------|--------|-------|
| Initial page load | < 3 seconds | Streamlit cold start |
| File upload feedback | Immediate | Progress bar appears instantly |
| Query submission to spinner | < 500ms | UI responsiveness |
| Results rendering | < 2 seconds | After receiving agent response |
| Visualization display | < 1 second | After S3 download |
| Session state restore | < 1 second | On page refresh |

---

## 9. Frontend Configuration

```python
# Streamlit page configuration in app.py
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
            'Powered by Claude 3.5 Sonnet on Amazon Bedrock'
        )
    }
)
```

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
