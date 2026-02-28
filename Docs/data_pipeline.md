# DataScout — Data Pipeline Documentation

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Pipeline Overview

DataScout's data pipeline handles the complete lifecycle of data — from user upload through secure processing to insight delivery. The pipeline is designed for **zero data leakage**, **deterministic accuracy**, and **full auditability**.

### 1.1 Pipeline Architecture

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DATA INGEST │ ──→ │  DATA STORE  │ ──→ │  DATA PROCESS│ ──→ │  DATA OUTPUT │
│              │     │              │     │              │     │              │
│ • Upload     │     │ • S3 Storage │     │ • Code Gen   │     │ • Results    │
│ • Validate   │     │ • Encryption │     │ • Sandbox    │     │ • Charts     │
│ • Metadata   │     │ • Lifecycle  │     │ • Execution  │     │ • Artifacts  │
└──────────────┘     └──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │                    │
       ▼                    ▼                    ▼                    ▼
┌──────────────────────────────────────────────────────────────────────────┐
│                    AUDIT & MONITORING LAYER                              │
│    CloudWatch Logs • Structured Events • Metrics • Alerts               │
└──────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Stage 1: Data Ingestion

### 2.1 Upload Pipeline

```
User selects file
    │
    ▼
┌────────────────────────────────┐
│ STEP 1: Client-Side Validation │
│                                │
│ • Check file extension         │
│ • Check file size (< 100MB)    │
│ • Verify MIME type             │
│ • Display error if invalid     │
└──────────┬─────────────────────┘
           │ ✅ Valid
           ▼
┌────────────────────────────────┐
│ STEP 2: Upload to S3           │
│                                │
│ • Generate S3 key:             │
│   datasets/{session_id}/       │
│   original/{filename}          │
│ • Server-side encryption       │
│   (AES-256)                    │
│ • Set metadata tags            │
│ • Monitor upload progress      │
└──────────┬─────────────────────┘
           │ ✅ Uploaded
           ▼
┌────────────────────────────────┐
│ STEP 3: Metadata Extraction    │
│                                │
│ • Read with pandas (first 1000)│
│ • Extract schema info:         │
│   - Column names               │
│   - Data types                 │
│   - Row count                  │
│   - Null counts                │
│   - Size (MB)                  │
│ • Generate preview (5 rows)    │
│ • Detect data quality issues   │
└──────────┬─────────────────────┘
           │ ✅ Metadata ready
           ▼
┌────────────────────────────────┐
│ STEP 4: Session State Update   │
│                                │
│ • Store S3 URI in session      │
│ • Store metadata in session    │
│ • Enable query input           │
│ • Log upload event             │
└────────────────────────────────┘
```

### 2.2 Supported Formats & Parsing

| Format | Extension | Parser | Options |
|--------|-----------|--------|---------|
| CSV | `.csv` | `pd.read_csv()` | encoding=utf-8, on_bad_lines='skip' |
| Excel | `.xlsx`, `.xls` | `pd.read_excel()` | engine='openpyxl' (xlsx), 'xlrd' (xls) |
| JSON | `.json` | `pd.read_json()` | orient='records' or auto-detect |

### 2.3 Data Validation Rules

```python
class DataValidator:
    """Validate incoming datasets before processing."""

    # File-level rules
    MAX_FILE_SIZE_MB = 100
    MAX_ROWS = 1_000_000
    MIN_COLUMNS = 1
    SUPPORTED_EXTENSIONS = {'.csv', '.xlsx', '.xls', '.json'}

    def validate(self, file_obj) -> ValidationResult:
        """Run all validations and return results."""
        checks = [
            self._check_extension(file_obj),
            self._check_size(file_obj),
            self._check_readable(file_obj),
            self._check_structure(file_obj),
        ]
        return ValidationResult(checks)

    def _check_extension(self, file_obj) -> Check:
        """Verify file has a supported extension."""
        ext = Path(file_obj.name).suffix.lower()
        return Check(
            name='file_format',
            passed=ext in self.SUPPORTED_EXTENSIONS,
            message=f"Format: {ext}" if ext in self.SUPPORTED_EXTENSIONS
                    else f"Unsupported format: {ext}"
        )

    def _check_size(self, file_obj) -> Check:
        """Verify file doesn't exceed size limit."""
        file_obj.seek(0, 2)
        size_mb = file_obj.tell() / (1024 * 1024)
        file_obj.seek(0)
        return Check(
            name='file_size',
            passed=size_mb <= self.MAX_FILE_SIZE_MB,
            message=f"Size: {size_mb:.1f}MB"
                    if size_mb <= self.MAX_FILE_SIZE_MB
                    else f"Too large: {size_mb:.1f}MB > {self.MAX_FILE_SIZE_MB}MB"
        )

    def _check_readable(self, file_obj) -> Check:
        """Verify file can be parsed by pandas."""
        try:
            df = self._read_file(file_obj, nrows=5)
            return Check('readable', True, f"Parsed: {len(df.columns)} columns")
        except Exception as e:
            return Check('readable', False, f"Parse error: {e}")

    def _check_structure(self, file_obj) -> Check:
        """Verify data has minimum structure."""
        try:
            df = self._read_file(file_obj, nrows=100)
            if len(df.columns) < self.MIN_COLUMNS:
                return Check('structure', False, "No valid columns found")
            if df.empty:
                return Check('structure', False, "Dataset is empty")
            return Check('structure', True, f"{len(df.columns)} columns, data present")
        except Exception as e:
            return Check('structure', False, str(e))
```

### 2.4 Column Name Sanitization

```python
def sanitize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure column names are valid Python identifiers.

    Transformations:
    - Strip whitespace
    - Replace spaces/special chars with underscores
    - Remove non-alphanumeric characters
    - Prefix numeric-starting names
    - Handle duplicates
    """
    clean_names = []
    for col in df.columns:
        name = str(col).strip()
        name = re.sub(r'[^a-zA-Z0-9_]', '_', name)
        name = re.sub(r'_+', '_', name)
        name = name.strip('_')
        if name and name[0].isdigit():
            name = f'col_{name}'
        if not name:
            name = f'unnamed_{len(clean_names)}'
        clean_names.append(name)

    # Handle duplicates
    seen = {}
    final_names = []
    for name in clean_names:
        if name in seen:
            seen[name] += 1
            final_names.append(f"{name}_{seen[name]}")
        else:
            seen[name] = 0
            final_names.append(name)

    df.columns = final_names
    return df
```

---

## 3. Stage 2: Data Storage

### 3.1 S3 Storage Architecture

```
datascout-storage/
│
├── datasets/
│   └── {session_id}/                    # Isolated per session
│       ├── original/                     # Raw uploaded files
│       │   └── sales_data.csv           # Exactly as uploaded
│       └── processed/                    # Cleaned versions (future)
│           └── sales_data_cleaned.csv
│
├── artifacts/
│   └── {session_id}/
│       ├── visualizations/               # Generated charts
│       │   ├── chart_001.png
│       │   ├── chart_002.png
│       │   └── chart_003.png
│       └── reports/                      # Generated reports (future)
│           └── analysis_summary.pdf
│
└── logs/
    └── {session_id}/
        └── execution_log.json            # Detailed execution trace
```

### 3.2 Data Lifecycle

```
                         Upload
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    ACTIVE STORAGE                            │
│                                                              │
│   Day 0 ──────────────────────────────────────→ Day 7       │
│                                                              │
│   datasets/*   → S3 Standard                                │
│   artifacts/*  → S3 Standard                                │
│   logs/*       → S3 Standard                                │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ Day 7
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    ARCHIVE / DELETE                           │
│                                                              │
│   datasets/*   → AUTO-DELETED (expired)                     │
│   artifacts/*  → AUTO-DELETED (expired)                     │
│   logs/*       → Transitioned to S3 Glacier                 │
│                                                              │
└──────────────────────────┬──────────────────────────────────┘
                           │ Day 90
                           │
┌──────────────────────────▼──────────────────────────────────┐
│                    PERMANENT DELETE                           │
│                                                              │
│   logs/*       → AUTO-DELETED from Glacier                  │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

### 3.3 Encryption & Security

| Layer | Method | Details |
|-------|--------|---------|
| At-Rest | AES-256 (SSE-S3) | Server-side encryption on all objects |
| In-Transit | TLS 1.2+ | HTTPS for all S3 API calls |
| Access Control | IAM Policies | Session-scoped read/write paths |
| Public Access | Blocked | All public access denied at bucket level |
| Versioning | Enabled | Recovery from accidental overwrites |

---

## 4. Stage 3: Data Processing

### 4.1 Query Processing Pipeline

```
User Query: "What is the average revenue by region?"
    │
    ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 1: QUERY UNDERSTANDING (Bedrock Agent - Claude 3.5)     │
│                                                               │
│  Input: "What is the average revenue by region?"             │
│  Session Context: dataset_uri, columns, dtypes               │
│                                                               │
│  Agent Reasoning:                                             │
│  ├─ Intent: Aggregation (average)                            │
│  ├─ Target Column: revenue                                   │
│  ├─ Group By: region                                         │
│  └─ Visualization: Bar chart (recommended)                   │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 2: CODE GENERATION (Agent → Python)                     │
│                                                               │
│  Generated Code:                                              │
│  ```python                                                    │
│  import pandas as pd                                         │
│  import matplotlib.pyplot as plt                             │
│                                                               │
│  # Load data                                                  │
│  df = pd.read_csv('/tmp/sales_data.csv')                    │
│                                                               │
│  # Validate                                                   │
│  assert 'region' in df.columns, "Missing 'region' column"   │
│  assert 'revenue' in df.columns, "Missing 'revenue' column" │
│                                                               │
│  # Compute                                                    │
│  avg_revenue = (df.groupby('region')['revenue']              │
│                   .mean()                                     │
│                   .sort_values(ascending=False)               │
│                   .reset_index())                             │
│  avg_revenue.columns = ['Region', 'Average Revenue']         │
│                                                               │
│  # Visualize                                                  │
│  plt.figure(figsize=(10, 6))                                 │
│  plt.bar(avg_revenue['Region'],                              │
│          avg_revenue['Average Revenue'],                      │
│          color='#4A90D9')                                     │
│  plt.xlabel('Region')                                         │
│  plt.ylabel('Average Revenue ($)')                            │
│  plt.title('Average Revenue by Region')                       │
│  plt.tight_layout()                                           │
│  plt.savefig('/tmp/revenue_by_region.png', dpi=150)          │
│                                                               │
│  # Output                                                     │
│  print(avg_revenue.to_markdown(index=False))                 │
│  ```                                                          │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 3: SANDBOX EXECUTION (Code Interpreter)                 │
│                                                               │
│  Environment:                                                 │
│  ├─ Python 3.11                                              │
│  ├─ 2 GB RAM, 2 vCPU                                        │
│  ├─ 30-second timeout                                        │
│  ├─ No network access                                        │
│  └─ /tmp read/write only                                     │
│                                                               │
│  Execution Steps:                                             │
│  1. Download dataset: S3 → /tmp/sales_data.csv               │
│  2. Execute generated code                                    │
│  3. Monitor resources (CPU, memory, time)                    │
│  4. Capture stdout → results text                            │
│  5. Capture /tmp/*.png → visualization artifacts             │
│  6. Upload artifacts: /tmp/chart.png → S3 artifacts/         │
│  7. Return results + artifact URIs                           │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 4: RESULT VALIDATION (Agent)                            │
│                                                               │
│  Checks:                                                      │
│  ├─ No NaN/null in computed values                           │
│  ├─ Data types are correct                                   │
│  ├─ Row counts match expectations                            │
│  ├─ Values are within reasonable ranges                      │
│  └─ No code execution errors                                 │
│                                                               │
│  If validation fails:                                         │
│  ├─ Agent modifies code                                      │
│  └─ Re-executes (max 2 retries)                              │
└──────────┬──────────────────────────────────────────────────┘
           │
           ▼
┌─────────────────────────────────────────────────────────────┐
│ STEP 5: RESPONSE FORMATTING (Agent → Frontend)               │
│                                                               │
│  Structured Output:                                           │
│  {                                                            │
│    "explanation": "I grouped data by region...",             │
│    "code": "import pandas as pd\n...",                       │
│    "results": "| Region | Avg Revenue |\n...",               │
│    "visualizations": ["s3://bucket/artifacts/.../chart.png"],│
│    "next_steps": ["Break down by product", "Add trends"]    │
│  }                                                            │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 Supported Analysis Types

| Category | Operations | Complexity |
|----------|-----------|------------|
| **Descriptive Statistics** | mean, median, mode, std, min, max, percentiles | Low |
| **Aggregation** | groupby + sum/mean/count, pivot tables | Low–Medium |
| **Ranking** | top N, bottom N, sorting, filtering | Low |
| **Trends** | time-series analysis, moving averages | Medium |
| **Correlation** | Pearson/Spearman correlation, scatter plots | Medium |
| **Distribution** | histograms, box plots, density plots | Medium |
| **Comparison** | cross-tabulation, side-by-side analysis | Medium |
| **Anomaly Detection** | outlier identification (IQR, z-score) | Medium–High |
| **Segmentation** | K-means clustering, grouping | High |
| **Forecasting** | Trend extrapolation, simple time-series models | High |

### 4.3 Code Generation Patterns

```python
# Pattern 1: Simple Aggregation
df.groupby('category')['value'].mean()

# Pattern 2: Multi-Column Aggregation
df.groupby('region').agg({
    'revenue': ['sum', 'mean', 'count'],
    'quantity': ['sum', 'mean']
})

# Pattern 3: Time-Series
df['date'] = pd.to_datetime(df['date'])
monthly = df.resample('M', on='date')['revenue'].sum()

# Pattern 4: Correlation
correlation = df[['price', 'quantity', 'revenue']].corr()
sns.heatmap(correlation, annot=True, cmap='coolwarm')

# Pattern 5: Distribution
df['revenue'].hist(bins=50, edgecolor='black')
plt.axvline(df['revenue'].mean(), color='red', linestyle='--')

# Pattern 6: Top N Ranking
top_n = df.nlargest(10, 'revenue')[['product', 'revenue']]
```

---

## 5. Stage 4: Data Output

### 5.1 Output Formats

| Output Type | Format | Delivery |
|-------------|--------|----------|
| **Results Table** | Markdown table via `to_markdown()` | Displayed in UI results tab |
| **Statistics** | Formatted numbers | Displayed inline |
| **Code** | Syntax-highlighted Python | Displayed in code viewer tab |
| **Charts** | PNG (matplotlib/seaborn) | Downloaded from S3, displayed inline |
| **Raw Data** | CSV download | User-initiated download button |
| **Reports** | PDF (future) | User-initiated download |

### 5.2 Visualization Generation

```python
class VisualizationGenerator:
    """Standard visualization patterns for common analysis types."""

    CHART_CONFIG = {
        'figsize': (10, 6),
        'dpi': 150,
        'style': 'seaborn-v0_8-whitegrid',
        'color_palette': ['#4A90D9', '#2ECC71', '#E74C3C', '#F39C12',
                          '#9B59B6', '#1ABC9C', '#E67E22', '#3498DB']
    }

    @staticmethod
    def bar_chart(data, x, y, title, save_path='/tmp/chart.png'):
        """Generate a styled bar chart."""
        plt.style.use(VisualizationGenerator.CHART_CONFIG['style'])
        fig, ax = plt.subplots(figsize=(10, 6))

        colors = VisualizationGenerator.CHART_CONFIG['color_palette']
        ax.bar(data[x], data[y], color=colors[:len(data)])

        ax.set_xlabel(x, fontsize=12)
        ax.set_ylabel(y, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')
        ax.tick_params(axis='x', rotation=45)

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return save_path

    @staticmethod
    def line_chart(data, x, y, title, save_path='/tmp/chart.png'):
        """Generate a styled line chart for trends."""
        plt.style.use(VisualizationGenerator.CHART_CONFIG['style'])
        fig, ax = plt.subplots(figsize=(10, 6))

        ax.plot(data[x], data[y], marker='o', linewidth=2,
                color='#4A90D9', markersize=6)
        ax.fill_between(data[x], data[y], alpha=0.1, color='#4A90D9')

        ax.set_xlabel(x, fontsize=12)
        ax.set_ylabel(y, fontsize=12)
        ax.set_title(title, fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return save_path

    @staticmethod
    def heatmap(data, title, save_path='/tmp/chart.png'):
        """Generate a correlation heatmap."""
        plt.style.use(VisualizationGenerator.CHART_CONFIG['style'])
        fig, ax = plt.subplots(figsize=(8, 6))

        sns.heatmap(data, annot=True, cmap='coolwarm', center=0,
                    fmt='.2f', linewidths=0.5, ax=ax)
        ax.set_title(title, fontsize=14, fontweight='bold')

        plt.tight_layout()
        plt.savefig(save_path, dpi=150, bbox_inches='tight')
        plt.close()

        return save_path
```

---

## 6. Data Quality Handling

### 6.1 Missing Data Strategy

```python
class MissingDataHandler:
    """Handle missing values in datasets."""

    @staticmethod
    def analyze_missing(df: pd.DataFrame) -> dict:
        """Generate missing data report."""
        total = len(df)
        missing = df.isnull().sum()
        pct_missing = (missing / total * 100).round(2)

        return {
            col: {
                'missing_count': int(m),
                'missing_pct': float(p),
                'severity': 'high' if p > 50 else 'medium' if p > 10 else 'low'
            }
            for col, m, p in zip(df.columns, missing, pct_missing)
            if m > 0
        }

    @staticmethod
    def suggest_handling(missing_report: dict) -> list:
        """Suggest appropriate handling for missing data."""
        suggestions = []
        for col, info in missing_report.items():
            if info['severity'] == 'high':
                suggestions.append(
                    f"⚠️ '{col}' has {info['missing_pct']}% missing — "
                    f"consider dropping or imputing"
                )
            elif info['severity'] == 'medium':
                suggestions.append(
                    f"ℹ️ '{col}' has {info['missing_pct']}% missing — "
                    f"mean/median imputation may help"
                )
        return suggestions
```

### 6.2 Data Type Detection

```python
def detect_column_types(df: pd.DataFrame) -> dict:
    """Detect semantic types beyond pandas dtypes."""
    type_map = {}

    for col in df.columns:
        dtype = str(df[col].dtype)

        # Detect dates stored as strings
        if dtype == 'object':
            try:
                pd.to_datetime(df[col].head(10))
                type_map[col] = 'datetime (string)'
                continue
            except (ValueError, TypeError):
                pass

        # Detect categorical vs free-text
        if dtype == 'object':
            unique_ratio = df[col].nunique() / len(df)
            if unique_ratio < 0.05:
                type_map[col] = 'categorical'
            else:
                type_map[col] = 'text'
        elif 'int' in dtype or 'float' in dtype:
            type_map[col] = 'numeric'
        elif 'datetime' in dtype:
            type_map[col] = 'datetime'
        elif 'bool' in dtype:
            type_map[col] = 'boolean'
        else:
            type_map[col] = dtype

    return type_map
```

---

## 7. Audit Trail

### 7.1 Audit Events

Every data operation generates an audit event:

| Event | Logged Fields | NOT Logged |
|-------|--------------|------------|
| `dataset_uploaded` | session_id, filename_hash, row_count, column_count, size_mb | Actual data values |
| `query_executed` | session_id, query_length, query_type, execution_time, success | Query text (hashed) |
| `code_generated` | session_id, code_lines, libraries_used | Full code text |
| `code_executed` | session_id, execution_time, success, error_type | Data values |
| `artifact_created` | session_id, artifact_type, artifact_size | Artifact content |
| `artifact_downloaded` | session_id, artifact_key | — |
| `session_expired` | session_id, duration, query_count | — |

### 7.2 Audit Log Format

```json
{
    "timestamp": "2026-02-24T10:30:00Z",
    "event": "query_executed",
    "session_id": "abc123-def456",
    "details": {
        "query_length": 45,
        "query_type": "aggregation",
        "columns_accessed": ["region", "revenue"],
        "execution_time_ms": 2500,
        "code_lines": 15,
        "visualization_generated": true,
        "success": true
    }
}
```

---

## 8. Pipeline Performance Optimization

### 8.1 Optimization Strategies

| Strategy | Technique | Impact |
|----------|-----------|--------|
| **Data Loading** | Read only required columns with `usecols` | 30–60% faster reads |
| **Subsampling** | Sample large datasets for visualization | Prevents chart overload |
| **Caching** | `@st.cache_data` for dataset metadata | Eliminates re-downloads |
| **Vectorization** | Agent generates vectorized pandas, not loops | 10–100x faster computation |
| **Lazy Parsing** | Parse only first 1000 rows for metadata | Fast initial feedback |
| **Streaming** | Stream agent response instead of waiting | Better perceived speed |

### 8.2 Code Generation Optimization Rules

```python
# Rules the Bedrock Agent follows for efficient code generation:

# ✅ GOOD: Vectorized operations
df['profit'] = df['revenue'] - df['cost']

# ❌ BAD: Row-by-row iteration
df['profit'] = df.apply(lambda row: row['revenue'] - row['cost'], axis=1)

# ✅ GOOD: Use built-in aggregations
df.groupby('region')['revenue'].agg(['mean', 'sum', 'count'])

# ❌ BAD: Manual loop aggregation
for region in df['region'].unique():
    subset = df[df['region'] == region]
    print(region, subset['revenue'].mean())

# ✅ GOOD: Read only needed columns
df = pd.read_csv('data.csv', usecols=['region', 'revenue'])

# ❌ BAD: Read entire file
df = pd.read_csv('data.csv')

# ✅ GOOD: Sample for visualization
if len(df) > 10000:
    df_viz = df.sample(n=10000, random_state=42)
```

---

## 9. Pipeline Monitoring

### 9.1 Key Pipeline Metrics

| Metric | Alert Threshold | Dashboard |
|--------|----------------|-----------|
| Upload success rate | < 95% | CloudWatch |
| Average upload time | > 5 seconds | CloudWatch |
| Query success rate | < 85% | CloudWatch |
| Average query latency | > 30 seconds | CloudWatch |
| Code execution error rate | > 10% | CloudWatch |
| Sandbox timeout rate | > 5% | CloudWatch |
| S3 storage usage | > 100 GB | Billing Alert |
| Concurrent sessions | > 100 | CloudWatch |

### 9.2 Health Check Pipeline

```python
def pipeline_health_check() -> dict:
    """Run health checks on all pipeline components."""
    results = {}

    # S3 connectivity
    try:
        s3.head_bucket(Bucket=Config.S3_BUCKET)
        results['s3'] = {'status': 'healthy', 'latency_ms': latency}
    except Exception as e:
        results['s3'] = {'status': 'unhealthy', 'error': str(e)}

    # Bedrock Agent
    try:
        response = bedrock.invoke_agent("ping", test_session, test_uri)
        results['bedrock'] = {'status': 'healthy', 'latency_ms': latency}
    except Exception as e:
        results['bedrock'] = {'status': 'unhealthy', 'error': str(e)}

    # CloudWatch
    try:
        cw.put_metric_data(Namespace='DataScout', MetricData=[...])
        results['cloudwatch'] = {'status': 'healthy'}
    except Exception as e:
        results['cloudwatch'] = {'status': 'unhealthy', 'error': str(e)}

    return results
```

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
