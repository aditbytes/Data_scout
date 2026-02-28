# DataScout — Frontend Design Document

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Design Philosophy

DataScout's frontend prioritizes **clarity, trust, and accessibility**. Every design decision serves one goal: enabling non-technical users to analyze data confidently through natural language.

### 1.1 Core Design Principles

| Principle | Description |
|-----------|-------------|
| **Simplicity First** | One screen, three actions: Upload → Ask → Read Results |
| **Progressive Disclosure** | Show essentials first; details on demand |
| **Transparent AI** | Always show the "how" behind the "what" — code is visible |
| **Error Empathy** | Errors are friendly, specific, and suggest next steps |
| **Speed Perception** | Spinners, progress, and streaming make waits feel shorter |

---

## 2. Design System

### 2.1 Color Palette

```
PRIMARY PALETTE
┌──────────────────────────────────────────────────────┐
│  Deep Navy     #1E3A5F  → Headers, primary text      │
│  Royal Blue    #4A90D9  → Interactive elements        │
│  Emerald       #2ECC71  → Success states              │
│  Soft Gray     #F8FAFC  → Background                  │
│  White         #FFFFFF  → Cards, surfaces              │
│  Charcoal      #1A1A2E  → Body text                   │
│  Medium Gray   #6C757D  → Secondary text              │
└──────────────────────────────────────────────────────┘

SEMANTIC COLORS
┌──────────────────────────────────────────────────────┐
│  Error         #E74C3C  → Error messages, alerts      │
│  Warning       #F39C12  → Warnings, cautions          │
│  Success       #2ECC71  → Success confirmations       │
│  Info          #3498DB  → Information, hints           │
│  Code BG       #282C34  → Code block background       │
│  Code Text     #ABB2BF  → Code block text             │
└──────────────────────────────────────────────────────┘
```

### 2.2 Typography

| Element | Font | Weight | Size |
|---------|------|--------|------|
| App Title | Inter | Bold (700) | 28px |
| Section Headers | Inter | SemiBold (600) | 22px |
| Sub Headers | Inter | SemiBold (600) | 18px |
| Body Text | Inter | Regular (400) | 16px |
| Captions | Inter | Regular (400) | 14px |
| Code | Fira Code | Regular (400) | 14px |
| Metrics | Inter | Bold (700) | 24px |
| Metric Labels | Inter | Regular (400) | 12px |

### 2.3 Spacing & Layout

```
SPACING SCALE (px)
xs:  4    → Compact padding
sm:  8    → Element gaps
md: 16    → Component padding
lg: 24    → Section gaps
xl: 32    → Major section dividers
2xl: 48   → Page-level spacing

LAYOUT
- Max content width: 1200px (centered)
- Side margins: 1rem (mobile) / 2rem (desktop)
- Card padding: 1.5rem
- Card border-radius: 12px
- Card shadow: 0 2px 8px rgba(0,0,0,0.05)
```

### 2.4 Iconography

| Context | Icon | Source |
|---------|------|--------|
| Upload | 📁 | Emoji |
| Dataset | 📊 | Emoji |
| Query | 💬 | Emoji |
| Results | 📈 | Emoji |
| Code | 💻 | Emoji |
| Success | ✅ | Emoji |
| Error | ❌ | Emoji |
| Warning | ⚠️ | Emoji |
| Info | ℹ️ | Emoji |
| Copy | 📋 | Emoji |
| Download | 📥 | Emoji |
| History | 📜 | Emoji |
| Settings | ⚙️ | Emoji |

---

## 3. Screen Designs

### 3.1 Initial State (No Dataset)

```
╔══════════════════════════════════════════════════════════════╗
║  🔬 DataScout                                                ║
║  Autonomous Enterprise Data Analyst                          ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │                                                       │   ║
║  │     📁 Upload Your Dataset                            │   ║
║  │                                                       │   ║
║  │     Drag and drop a file here, or click to browse    │   ║
║  │                                                       │   ║
║  │     Supported: CSV, Excel (.xlsx), JSON              │   ║
║  │     Maximum size: 100 MB                              │   ║
║  │                                                       │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │  💬 Ask a Question                                    │   ║
║  │  ┌──────────────────────────────────────────┐ [Ask ] │   ║
║  │  │ Upload a dataset first to get started... │        │   ║
║  │  └──────────────────────────────────────────┘ DISABLED│   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
║  ─────────────────────────────────────────────────────────── ║
║  DataScout v1.0 • Powered by Claude 3.5 Sonnet              ║
╚══════════════════════════════════════════════════════════════╝
```

### 3.2 Dataset Loaded State

```
╔══════════════════════════════════════════════════════════════╗
║  🔬 DataScout                                                ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  ✅ Dataset loaded: sales_data.csv                           ║
║                                                              ║
║  ┌────────┬────────┬──────────┬─────────┐                   ║
║  │📁 File │📏 Rows │📐 Columns│💾 Size  │                   ║
║  │sales_  │ 1,234  │    8     │ 2.3 MB  │                   ║
║  │data.csv│        │          │         │                   ║
║  └────────┴────────┴──────────┴─────────┘                   ║
║                                                              ║
║  ▸ Preview Dataset                                           ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  💬 Ask a Question                                           ║
║  ┌─────────────────────────────────────────────┐ [  Ask  ]  ║
║  │ e.g., What is the average revenue by region? │           ║
║  └─────────────────────────────────────────────┘            ║
║                                                              ║
║  💡 Suggestions:                                             ║
║  [Average revenue by region] [Top 5 products] [Trends]      ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 3.3 Processing State

```
╔══════════════════════════════════════════════════════════════╗
║  🔬 DataScout                                                ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  [Dataset info bar - compact]                                ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  💬 "What is the average revenue by region?"                 ║
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │                                                       │   ║
║  │     🔍 Analyzing your data...                         │   ║
║  │                                                       │   ║
║  │     ████████████░░░░░░░░░  60%                       │   ║
║  │                                                       │   ║
║  │     Generating Python code and executing analysis     │   ║
║  │                                                       │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

### 3.4 Results State (Full)

```
╔══════════════════════════════════════════════════════════════╗
║  🔬 DataScout                                                ║
║  ─────────────────────────────────────────────────────────── ║
║  [Dataset info bar - compact]                                ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  💬 Ask a Question                                           ║
║  ┌──────────────────────────────────────────┐ [  Ask  ]     ║
║  │                                           │              ║
║  └──────────────────────────────────────────┘              ║
║  ─────────────────────────────────────────────────────────── ║
║                                                              ║
║  📈 Results — Average Revenue by Region (2.3s)              ║
║                                                              ║
║  [📝 Explanation] [📊 Results] [💻 Code] [📈 Chart]        ║
║  ═══════════════════════════════════════════                 ║
║                                                              ║
║  📝 Explanation:                                             ║
║  I grouped the data by the 'region' column and calculated   ║
║  the mean of the 'revenue' column for each group.           ║
║                                                              ║
║  📊 Results:                                                 ║
║  ┌──────────┬────────────────┐                              ║
║  │ Region   │ Average Revenue│                              ║
║  ├──────────┼────────────────┤                              ║
║  │ East     │ $156,432.87    │                              ║
║  │ North    │ $145,234.56    │                              ║
║  │ West     │ $141,098.34    │                              ║
║  │ South    │ $132,890.12    │                              ║
║  └──────────┴────────────────┘                              ║
║                                                              ║
║  💻 Code Executed:                                           ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │ import pandas as pd                                   │   ║
║  │ df = pd.read_csv('/tmp/sales_data.csv')              │   ║
║  │ avg_rev = df.groupby('region')['revenue']            │   ║
║  │              .mean().reset_index()                    │   ║
║  │ avg_rev.columns = ['Region', 'Average Revenue']      │   ║
║  │ print(avg_rev.to_markdown(index=False))              │   ║
║  └──────────────────────────────────────────────────────┘   ║
║  [📋 Copy Code]                                             ║
║                                                              ║
║  📈 Visualization:                                           ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │                   [Bar Chart]                         │   ║
║  │  Revenue ($)                                          │   ║
║  │  160k ┤                                               │   ║
║  │  140k ┤  ███   ███         ███                        │   ║
║  │  120k ┤  ███   ███   ███   ███                        │   ║
║  │  100k ┤  ███   ███   ███   ███                        │   ║
║  │       └──East──North─South─West──                     │   ║
║  └──────────────────────────────────────────────────────┘   ║
║  [📥 Download Chart]                                        ║
║                                                              ║
║  ─────────────────────────────────────────────────────────── ║
║  📜 Query History                                            ║
║  ✅ Q1: "What is the average revenue by region?" (2.3s)     ║
║  ─────────────────────────────────────────────────────────── ║
║  DataScout v1.0 • Powered by Claude 3.5 Sonnet              ║
╚══════════════════════════════════════════════════════════════╝
```

### 3.5 Error State

```
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║  ┌──────────────────────────────────────────────────────┐   ║
║  │  ⚠️ Unsupported File Format                           │   ║
║  │                                                       │   ║
║  │  DataScout supports CSV, Excel (.xlsx), and           │   ║
║  │  JSON formats.                                        │   ║
║  │                                                       │   ║
║  │  💡 Convert your file to one of these formats and    │   ║
║  │     try again.                                        │   ║
║  └──────────────────────────────────────────────────────┘   ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
```

---

## 4. Component Interaction Diagram

```
┌──────────────────────────────────────────────────────────┐
│                      app.py (Main)                        │
│                                                           │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────┐ │
│  │ file_upload  │→ │ dataset_    │→ │ query_input     │ │
│  │ .py          │  │ preview.py  │  │ .py             │ │
│  └──────┬───────┘  └─────────────┘  └────────┬────────┘ │
│         │                                      │          │
│     upload_file()                        send_query()     │
│         │                                      │          │
│         ▼                                      ▼          │
│  ┌──────────────────────────────────────────────────────┐ │
│  │              services/ (Backend Layer)                │ │
│  │                                                       │ │
│  │  s3_handler.py          bedrock_client.py            │ │
│  │  ├─ upload_dataset()    ├─ invoke_agent()            │ │
│  │  ├─ get_metadata()      └─ _parse_response()         │ │
│  │  └─ download_artifact()                              │ │
│  │                                                       │ │
│  │  session_manager.py                                   │ │
│  │  ├─ create_session()                                  │ │
│  │  └─ validate_session()                                │ │
│  └──────────────────────────────────────────────────────┘ │
│         │                                      │          │
│         ▼                                      ▼          │
│  ┌─────────────────────┐  ┌─────────────────────────────┐│
│  │ results_display.py  │  │ visualization.py            ││
│  │ ├─ render_results() │  │ ├─ render_visualization()   ││
│  │ └─ render_tabs()    │  │ └─ download_chart()         ││
│  └─────────────────────┘  └─────────────────────────────┘│
│                                                           │
│  ┌───────────────────────────────────────────────────────┐│
│  │ code_viewer.py                                        ││
│  │ ├─ render_code_block()                                ││
│  │ └─ copy_to_clipboard()                                ││
│  └───────────────────────────────────────────────────────┘│
└──────────────────────────────────────────────────────────┘
```

---

## 5. Animation & Feedback Patterns

### 5.1 Loading States

| Trigger | Animation | Duration |
|---------|-----------|----------|
| File uploading | Progress bar (determinate) | 1–5 seconds |
| Query processing | Spinner + "Analyzing..." text | 5–30 seconds |
| Chart loading | Skeleton placeholder → image fade-in | < 2 seconds |
| Session initializing | Brief flash then ready | < 1 second |

### 5.2 State Transitions

```
Upload Success:
  [Drag Zone] → [fade out] → [✅ Success Toast] → [Info Bar slides in]

Query Submit:
  [Input] → [Spinner appears] → [Results fade in] → [Scroll to results]

Error:
  [Action] → [Red error card slides in] → [Suggestion below error]

Tab Switch:
  [Tab click] → [Content cross-fade] → [New tab content]
```

### 5.3 Toast Notifications

| Event | Toast | Duration | Color |
|-------|-------|----------|-------|
| Dataset uploaded | ✅ "Dataset loaded successfully" | 3 seconds | Green |
| Code copied | 📋 "Code copied to clipboard!" | 2 seconds | Blue |
| Chart downloaded | 📥 "Chart saved to downloads" | 2 seconds | Blue |
| Session expired | ⏱️ "Session expired. Upload dataset again." | 5 seconds | Yellow |

---

## 6. Responsive Behavior

### 6.1 Desktop (≥ 992px)

- Full-width layout (max 1200px)
- Metrics displayed in 4-column row
- Side-by-side elements where appropriate
- Expanded code viewer by default

### 6.2 Tablet (768px – 991px)

- Metrics in 2-column grid
- Full-width query input
- Full-width results
- Code viewer collapsed by default

### 6.3 Mobile (< 768px)

- Single-column layout
- Stacked metrics
- Full-width everything
- Compact dataset info
- Simplified suggestions (2 max)

---

## 7. Dark Mode (Phase 2)

### 7.1 Dark Mode Palette

```
DARK PALETTE (Future)
┌──────────────────────────────────────────────────────┐
│  Background   #0D1117  → Main background             │
│  Surface      #161B22  → Cards, panels               │
│  Border       #30363D  → Borders, dividers           │
│  Text         #E6EDF3  → Primary text                │
│  Text Muted   #8B949E  → Secondary text              │
│  Primary      #58A6FF  → Links, interactive elements │
│  Success      #3FB950  → Success states              │
│  Error        #F85149  → Error states                │
│  Code BG      #0D1117  → Code background             │
│  Code Text    #E6EDF3  → Code text                   │
└──────────────────────────────────────────────────────┘
```

---

## 8. Accessibility Guidelines

| Guideline | Implementation |
|-----------|---------------|
| Color contrast ≥ 4.5:1 | Verified for all text/background combinations |
| Focus indicators | Visible focus rings on all interactive elements |
| Alt text | All images/charts include descriptive captions |
| Keyboard navigation | Tab order follows visual hierarchy |
| Error identification | Errors not conveyed by color alone (icons + text) |
| Labels | All form inputs have associated labels |
| Motion respect | Respect `prefers-reduced-motion` (Phase 2) |

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
