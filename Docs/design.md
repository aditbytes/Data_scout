# DataScout - System Design Specification

## 1. Design Overview

### 1.1 Design Philosophy
DataScout is built on the principle of **execution-based reasoning** rather than text prediction. The system transforms natural language analytical intent into deterministic, auditable Python code that runs in a secure sandbox environment.

### 1.2 Core Design Principles
- **Transparency:** All computations are visible and explainable
- **Determinism:** Results are mathematically correct, never hallucinated
- **Security:** Enterprise-grade isolation and access control
- **Simplicity:** Intuitive interface requiring zero technical knowledge
- **Auditability:** Complete trace of all analytical operations

### 1.3 Design Goals
1. Enable non-technical users to perform complex data analysis via natural language
2. Eliminate numerical hallucinations through code execution
3. Maintain enterprise security boundaries
4. Provide full transparency of analytical methodology
5. Deliver insights in seconds, not hours

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌─────────────────┐
│  User Browser   │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────────────────────────────┐
│       Streamlit Frontend                │
│       (AWS App Runner)                  │
└────────┬────────────────────────────────┘
         │ boto3 SDK
         ▼
┌─────────────────────────────────────────┐
│    Amazon Bedrock Agent                 │
│    (Claude 3.5 Sonnet)                  │
│                                         │
│  ┌──────────────────────────────┐      │
│  │  Agent Orchestration Layer   │      │
│  │  - Query Understanding       │      │
│  │  - Code Generation           │      │
│  │  - Validation Logic          │      │
│  │  - Response Formatting       │      │
│  └──────────────────────────────┘      │
└────┬────────────────────────────────┬───┘
     │                                │
     │ Tool Invocation                │ Data Access
     ▼                                ▼
┌──────────────────────┐    ┌──────────────────────┐
│  Code Interpreter    │    │    Amazon S3         │
│  (Python Sandbox)    │    │                      │
│                      │    │  ┌────────────────┐  │
│  - pandas           │    │  │ User Datasets  │  │
│  - numpy            │    │  └────────────────┘  │
│  - matplotlib       │    │  ┌────────────────┐  │
│  - seaborn          │    │  │   Artifacts    │  │
│  - Execution Engine │    │  └────────────────┘  │
└──────────────────────┘    └──────────────────────┘
         │                            │
         │ Results                    │ IAM Policies
         ▼                            ▼
┌─────────────────────────────────────────┐
│         CloudWatch Logs                 │
│         (Monitoring & Audit)            │
└─────────────────────────────────────────┘
```

### 2.2 Component Interaction Flow

```
[User Query] 
    → Frontend receives input
    → Upload dataset to S3 (if new file)
    → Invoke Bedrock Agent with query + dataset reference
    → Agent analyzes query, generates Python code
    → Agent invokes Code Interpreter tool
    → Code Interpreter loads data from S3
    → Code executes in sandbox
    → Results + visualizations returned
    → Agent formats response
    → Frontend displays results + code + charts
    → User reviews and asks follow-up
```

---

## 3. Detailed Component Design

### 3.1 Streamlit Frontend

#### 3.1.1 Architecture
```
streamlit_app/
├── app.py                    # Main application entry point
├── components/
│   ├── file_upload.py       # Dataset upload widget
│   ├── query_input.py       # Natural language input
│   ├── results_display.py   # Results rendering
│   └── code_viewer.py       # Code display component
├── services/
│   ├── bedrock_client.py    # Bedrock API wrapper
│   ├── s3_handler.py        # S3 operations
│   └── session_manager.py   # User session handling
├── utils/
│   ├── validators.py        # Input validation
│   └── formatters.py        # Output formatting
└── config.py                # Configuration management
```

#### 3.1.2 UI Component Design

**Page Layout:**
```
╔════════════════════════════════════════════════════════╗
║  DataScout - Autonomous Enterprise Data Analyst        ║
╠════════════════════════════════════════════════════════╣
║                                                        ║
║  📁 Upload Dataset                                     ║
║  [Drag and drop or browse] .csv, .xlsx, .json        ║
║                                                        ║
║  ──────────────────────────────────────────────────   ║
║                                                        ║
║  📊 Current Dataset: sales_data.csv (1,234 rows)      ║
║  Columns: date, region, product, revenue, quantity    ║
║                                                        ║
║  ──────────────────────────────────────────────────   ║
║                                                        ║
║  💬 Ask a Question                                     ║
║  [What is the average revenue by region?            ] ║
║                                                 [Ask]  ║
║                                                        ║
║  ──────────────────────────────────────────────────   ║
║                                                        ║
║  📈 Results                                            ║
║  ┌────────────────────────────────────────────────┐   ║
║  │ Analysis: Average Revenue by Region            │   ║
║  │                                                 │   ║
║  │ Region         Average Revenue                 │   ║
║  │ North          $145,234.56                      │   ║
║  │ South          $132,890.12                      │   ║
║  │ East           $156,432.87                      │   ║
║  │ West           $141,098.34                      │   ║
║  │                                                 │   ║
║  │ [Bar Chart Visualization]                       │   ║
║  └────────────────────────────────────────────────┘   ║
║                                                        ║
║  🔍 Code Executed                                      ║
║  ┌────────────────────────────────────────────────┐   ║
║  │ import pandas as pd                            │   ║
║  │ df = pd.read_csv('sales_data.csv')            │   ║
║  │ avg_revenue = df.groupby('region')['revenue'] │   ║
║  │                 .mean()                        │   ║
║  │                 .reset_index()                 │   ║
║  └────────────────────────────────────────────────┘   ║
║                                          [Copy Code]   ║
║                                                        ║
╚════════════════════════════════════════════════════════╝
```

#### 3.1.3 Session State Management
```python
# Session state structure
st.session_state = {
    'dataset_s3_uri': str,           # S3 location of uploaded dataset
    'dataset_metadata': {             # Dataset information
        'filename': str,
        'rows': int,
        'columns': list,
        'size_mb': float
    },
    'conversation_history': [         # Query-response pairs
        {
            'query': str,
            'code': str,
            'results': dict,
            'visualizations': list,
            'timestamp': datetime
        }
    ],
    'bedrock_agent_id': str,         # Bedrock Agent identifier
    'session_id': str                # Unique session identifier
}
```

#### 3.1.4 Key Frontend Methods

```python
class DataScoutApp:
    def __init__(self):
        self.bedrock_client = BedrockAgentClient()
        self.s3_handler = S3Handler()
        
    def upload_dataset(self, file):
        """Upload dataset to S3 and extract metadata"""
        # Validate file format
        # Upload to S3
        # Extract metadata (rows, columns, dtypes)
        # Update session state
        
    def send_query(self, query):
        """Send user query to Bedrock Agent"""
        # Prepare agent input
        # Invoke agent
        # Parse response
        # Update conversation history
        
    def display_results(self, response):
        """Render analysis results"""
        # Show explanation
        # Display data tables
        # Render visualizations
        # Show executed code
```

### 3.2 Amazon Bedrock Agent

#### 3.2.1 Agent Configuration

```yaml
AgentName: DataScout-Analyst
Foundation Model: anthropic.claude-3-5-sonnet-20241022-v2:0
Description: Autonomous data analyst that generates and executes Python code

Agent Instructions: |
  You are DataScout, an autonomous data analyst. Your role is to help users 
  analyze datasets by writing and executing Python code.
  
  CRITICAL RULES:
  1. NEVER guess or hallucinate numerical values
  2. ALWAYS use code to compute statistics, aggregations, and insights
  3. Generate clean, readable Python code using pandas and numpy
  4. Validate inputs and handle errors gracefully
  5. Explain your analytical approach clearly
  6. Show all code to the user for transparency
  
  WORKFLOW:
  1. Understand the user's analytical question
  2. Plan the analysis steps
  3. Write Python code to perform the analysis
  4. Execute the code using the Code Interpreter tool
  5. Validate the results
  6. Create visualizations if helpful
  7. Present results with explanations
  
  AVAILABLE LIBRARIES:
  - pandas: Data manipulation and analysis
  - numpy: Numerical computing
  - matplotlib: Static visualizations
  - seaborn: Statistical visualizations
  
  RESPONSE FORMAT:
  1. Brief explanation of analysis approach
  2. Generated Python code (in code block)
  3. Results (tables, statistics, insights)
  4. Visualizations (if created)
  5. Summary and next steps

Idle Session TTL: 600 seconds
```

#### 3.2.2 Agent Prompt Template

```xml
<agent_role>
You are DataScout, an enterprise data analyst AI that generates accurate 
insights through code execution, not text prediction.
</agent_role>

<critical_constraints>
- NEVER hallucinate numerical values
- ALL calculations MUST be performed through executed Python code
- NO guessing of statistics, aggregations, or insights
- ALWAYS show code to user for transparency
</critical_constraints>

<available_tools>
- Code Interpreter: Secure Python sandbox with pandas, numpy, matplotlib, seaborn
- Data Access: Read datasets from S3 via provided URIs
</available_tools>

<workflow>
1. Parse user query to understand analytical intent
2. Identify required data columns and operations
3. Generate Python code to perform analysis
4. Execute code using Code Interpreter
5. Validate outputs (check for nulls, errors, unexpected values)
6. Format results for presentation
7. Generate visualizations if they add value
8. Explain methodology and findings
</workflow>

<example_interaction>
User: "What is the average sales by region?"

Assistant Thinking:
- Need to group data by 'region' column
- Calculate mean of 'sales' column
- Present results in a table
- Create a bar chart for visualization

Code to Execute:
```python
import pandas as pd
import matplotlib.pyplot as plt

# Load dataset
df = pd.read_csv('/tmp/uploaded_data.csv')

# Calculate average sales by region
avg_sales = df.groupby('region')['sales'].mean().reset_index()
avg_sales.columns = ['Region', 'Average Sales']

# Create visualization
plt.figure(figsize=(10, 6))
plt.bar(avg_sales['Region'], avg_sales['Average Sales'])
plt.xlabel('Region')
plt.ylabel('Average Sales ($)')
plt.title('Average Sales by Region')
plt.xticks(rotation=45)
plt.tight_layout()
plt.savefig('/tmp/sales_by_region.png')

# Return results
print(avg_sales.to_markdown(index=False))
```

Results:
Region | Average Sales
North  | 145234.56
South  | 132890.12
East   | 156432.87
West   | 141098.34

Visualization saved to: /tmp/sales_by_region.png

Explanation:
I grouped your sales data by region and calculated the mean sales value 
for each. The East region has the highest average sales at $156,432.87, 
while the South region has the lowest at $132,890.12.
</example_interaction>
```

#### 3.2.3 Code Generation Strategy

**Design Pattern: Planning → Coding → Execution → Validation**

```python
# Agent mental model for code generation

class AnalyticalCodeGenerator:
    def generate(self, query, dataset_metadata):
        # Step 1: Parse query intent
        intent = self.parse_intent(query)
        
        # Step 2: Identify required columns
        columns = self.identify_columns(intent, dataset_metadata)
        
        # Step 3: Determine operations
        operations = self.determine_operations(intent)
        
        # Step 4: Generate code
        code = self.construct_code(
            operations=operations,
            columns=columns,
            dataset_path=dataset_metadata['s3_path']
        )
        
        # Step 5: Add error handling
        code = self.wrap_error_handling(code)
        
        # Step 6: Add visualization if appropriate
        if self.should_visualize(intent):
            code += self.generate_visualization_code(operations)
        
        return code
```

**Code Template Structure:**
```python
# Standard code structure for all analyses

# 1. Imports
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# 2. Data Loading
try:
    df = pd.read_csv('s3://bucket/path/dataset.csv')
except Exception as e:
    print(f"Error loading data: {e}")
    raise

# 3. Data Validation
if df.empty:
    raise ValueError("Dataset is empty")

required_columns = ['col1', 'col2']
missing_cols = set(required_columns) - set(df.columns)
if missing_cols:
    raise ValueError(f"Missing columns: {missing_cols}")

# 4. Analysis Logic
result = df.groupby('category')['value'].mean()

# 5. Validation
if result.isnull().any():
    print("Warning: Null values in results")

# 6. Visualization (if applicable)
plt.figure(figsize=(10, 6))
# ... plotting code ...
plt.savefig('/tmp/output.png')

# 7. Output
print(result.to_markdown())
```

### 3.3 Code Interpreter (Python Sandbox)

#### 3.3.1 Execution Environment

```yaml
Environment:
  Runtime: Python 3.11
  Memory: 2GB
  CPU: 2 vCPU
  Execution Timeout: 30 seconds
  Network Access: None (air-gapped)
  
Pre-installed Libraries:
  - pandas==2.0.3
  - numpy==1.24.3
  - matplotlib==3.7.1
  - seaborn==0.12.2
  - scipy==1.11.1
  - scikit-learn==1.3.0

File System:
  - Read Access: /tmp (for datasets from S3)
  - Write Access: /tmp (for generated artifacts)
  - Storage Limit: 512MB
  
Security:
  - No network access
  - No system calls
  - Restricted file operations
  - Resource limits enforced
```

#### 3.3.2 Execution Flow

```
Code Received
    ↓
Syntax Validation
    ↓
Security Scan (no malicious patterns)
    ↓
Load Dataset from S3 to /tmp
    ↓
Execute Code in Sandbox
    ↓
Monitor Resource Usage
    ↓
Capture stdout, stderr, exceptions
    ↓
Collect Generated Artifacts
    ↓
Upload Artifacts to S3
    ↓
Return Results to Agent
```

#### 3.3.3 Security Constraints

```python
# Blocked operations
BLOCKED_IMPORTS = [
    'os',           # System operations
    'subprocess',   # Process execution
    'socket',       # Network access
    'urllib',       # HTTP requests
    'requests',     # HTTP requests
    'sys.exit',     # Process termination
]

# Resource limits
MAX_EXECUTION_TIME = 30  # seconds
MAX_MEMORY_MB = 2048
MAX_FILE_SIZE_MB = 100
MAX_OUTPUT_LINES = 10000

# File system restrictions
ALLOWED_READ_PATHS = ['/tmp']
ALLOWED_WRITE_PATHS = ['/tmp']
```

### 3.4 Amazon S3 Storage

#### 3.4.1 Bucket Structure

```
datascout-storage/
├── datasets/
│   └── {session_id}/
│       ├── original/
│       │   └── {filename}
│       └── processed/
│           └── {filename}_cleaned.csv
├── artifacts/
│   └── {session_id}/
│       ├── visualizations/
│       │   ├── chart_001.png
│       │   └── chart_002.png
│       └── reports/
│           └── analysis_summary.pdf
└── logs/
    └── {session_id}/
        └── execution_log.json
```

#### 3.4.2 Lifecycle Policies

```yaml
Lifecycle Rules:
  - Rule: Delete Session Data
    Prefix: datasets/{session_id}
    Expiration: 7 days
    
  - Rule: Delete Artifacts
    Prefix: artifacts/{session_id}
    Expiration: 7 days
    
  - Rule: Archive Logs
    Prefix: logs/
    Transition:
      - Days: 7
        StorageClass: GLACIER
    Expiration: 90 days
```

#### 3.4.3 IAM Policies

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject"
      ],
      "Resource": "arn:aws:s3:::datascout-storage/datasets/${aws:userid}/*"
    },
    {
      "Effect": "Deny",
      "Action": "s3:*",
      "Resource": "arn:aws:s3:::datascout-storage/datasets/",
      "Condition": {
        "StringNotEquals": {
          "s3:prefix": "${aws:userid}"
        }
      }
    }
  ]
}
```

### 3.5 Integration Layer

#### 3.5.1 Bedrock Client Wrapper

```python
class BedrockAgentClient:
    def __init__(self, region='us-east-1'):
        self.client = boto3.client('bedrock-agent-runtime', region_name=region)
        self.agent_id = os.environ['BEDROCK_AGENT_ID']
        self.agent_alias_id = os.environ['BEDROCK_AGENT_ALIAS_ID']
        
    def invoke_agent(self, query, session_id, dataset_uri):
        """Invoke Bedrock Agent with query and dataset context"""
        
        response = self.client.invoke_agent(
            agentId=self.agent_id,
            agentAliasId=self.agent_alias_id,
            sessionId=session_id,
            inputText=query,
            sessionState={
                'sessionAttributes': {
                    'dataset_uri': dataset_uri,
                    'dataset_format': 'csv'
                }
            }
        )
        
        return self.parse_response(response)
    
    def parse_response(self, response):
        """Parse streaming response from agent"""
        
        chunks = []
        for event in response['completion']:
            if 'chunk' in event:
                chunks.append(event['chunk']['bytes'].decode('utf-8'))
        
        full_response = ''.join(chunks)
        return self.extract_components(full_response)
    
    def extract_components(self, response_text):
        """Extract code, results, and explanations from response"""
        
        components = {
            'explanation': '',
            'code': '',
            'results': '',
            'visualizations': [],
            'next_steps': []
        }
        
        # Parse structured response
        # Extract code blocks
        # Identify S3 URIs for visualizations
        # Parse results tables
        
        return components
```

#### 3.5.2 S3 Handler

```python
class S3Handler:
    def __init__(self, bucket_name):
        self.s3 = boto3.client('s3')
        self.bucket = bucket_name
        
    def upload_dataset(self, file_obj, session_id):
        """Upload user dataset to S3"""
        
        key = f"datasets/{session_id}/original/{file_obj.name}"
        
        self.s3.upload_fileobj(
            file_obj,
            self.bucket,
            key,
            ExtraArgs={'ServerSideEncryption': 'AES256'}
        )
        
        return f"s3://{self.bucket}/{key}"
    
    def get_dataset_metadata(self, s3_uri):
        """Extract metadata from uploaded dataset"""
        
        # Download file
        # Read with pandas
        # Extract shape, columns, dtypes
        # Return metadata dict
        
        return {
            'rows': int,
            'columns': list,
            'dtypes': dict,
            'size_mb': float
        }
    
    def download_artifact(self, s3_uri):
        """Download generated artifact (chart, report)"""
        
        # Parse S3 URI
        # Download object
        # Return file bytes
        
        return bytes
```

---

## 4. Data Flow Design

### 4.1 Upload Flow

```
User selects file
    ↓
Frontend validates format (csv/xlsx/json)
    ↓
Frontend uploads to S3Handler
    ↓
S3Handler saves to: s3://bucket/datasets/{session_id}/original/{filename}
    ↓
S3Handler extracts metadata (rows, columns, dtypes)
    ↓
Frontend updates session_state with S3 URI and metadata
    ↓
Frontend displays dataset preview
```

### 4.2 Query Execution Flow

```
User enters query: "What is the average revenue by region?"
    ↓
Frontend sends to Bedrock Agent via BedrockAgentClient
    ↓
Agent receives query + session context (dataset S3 URI)
    ↓
Agent analyzes query intent:
  - Action: Calculate average
  - Column: revenue
  - Group by: region
    ↓
Agent generates Python code:
  ```python
  df = pd.read_csv('s3://...')
  avg_revenue = df.groupby('region')['revenue'].mean()
  print(avg_revenue)
  ```
    ↓
Agent invokes Code Interpreter tool with code
    ↓
Code Interpreter:
  - Downloads dataset from S3 to /tmp
  - Executes code in sandbox
  - Captures output and any generated files
  - Uploads artifacts to S3
  - Returns results to agent
    ↓
Agent formats response:
  - Explanation of approach
  - Executed code
  - Results table
  - Visualization (if created)
    ↓
BedrockAgentClient parses response
    ↓
Frontend displays:
  - Explanation
  - Results table
  - Code block (with copy button)
  - Visualization (if present)
```

### 4.3 Visualization Generation Flow

```
Agent determines visualization is helpful
    ↓
Generates matplotlib/seaborn code:
  ```python
  plt.figure(figsize=(10, 6))
  plt.bar(data['region'], data['revenue'])
  plt.savefig('/tmp/revenue_by_region.png')
  ```
    ↓
Code Interpreter executes visualization code
    ↓
Saves PNG to /tmp/revenue_by_region.png
    ↓
Code Interpreter uploads PNG to S3:
  s3://bucket/artifacts/{session_id}/visualizations/chart_001.png
    ↓
Returns S3 URI in response
    ↓
Frontend downloads image from S3
    ↓
Displays inline in results section
```

---

## 5. Security Design

### 5.1 Security Architecture

```
Defense in Depth:

Layer 1: Network Security
  - VPC isolation
  - Security groups
  - No public internet access from backend

Layer 2: IAM & Access Control
  - Least privilege IAM roles
  - Session-scoped S3 access
  - No cross-session data access

Layer 3: Code Execution Sandbox
  - Air-gapped environment
  - No network access
  - Resource limits enforced
  - Blocked imports

Layer 4: Data Encryption
  - TLS 1.2+ in transit
  - AES-256 at rest (S3)
  - Encrypted CloudWatch logs

Layer 5: Audit & Monitoring
  - All API calls logged
  - CloudWatch alarms
  - Anomaly detection
```

### 5.2 Threat Model & Mitigations

| Threat | Mitigation |
|--------|-----------|
| Malicious code injection | Syntax validation, blocked imports, sandboxing |
| Data exfiltration | No network access in sandbox, IAM isolation |
| Prompt injection | Agent instruction hardening, output validation |
| Session hijacking | Secure session IDs, timeout enforcement |
| Resource exhaustion | CPU/memory/time limits in sandbox |
| Unauthorized data access | S3 bucket policies, IAM role isolation |

### 5.3 Data Privacy

```python
# Privacy-preserving design principles

1. No persistent storage of raw data beyond 7 days
2. No logging of data values, only metadata
3. No model training on user data
4. Session isolation prevents cross-contamination
5. User data never leaves AWS infrastructure
6. Automated data deletion on session expiry

# Example: Audit log (data values redacted)
{
  "timestamp": "2026-02-01T10:30:00Z",
  "session_id": "abc123",
  "action": "execute_query",
  "query_type": "aggregation",
  "dataset_rows": 1234,
  "execution_time_ms": 2500,
  "columns_accessed": ["region", "revenue"],
  "code_lines": 15,
  "success": true
  # NOTE: Actual data values NOT logged
}
```

---

## 6. Error Handling Design

### 6.1 Error Categories

```python
class DataScoutError(Exception):
    """Base exception for DataScout"""
    pass

class DataUploadError(DataScoutError):
    """Dataset upload or validation failed"""
    # User action: Check file format, size
    
class CodeGenerationError(DataScoutError):
    """Agent failed to generate valid code"""
    # System action: Retry with clarification
    
class CodeExecutionError(DataScoutError):
    """Code execution in sandbox failed"""
    # Agent action: Debug and regenerate code
    
class DataValidationError(DataScoutError):
    """Data doesn't meet requirements"""
    # User action: Clean data or provide different dataset
    
class TimeoutError(DataScoutError):
    """Operation exceeded time limit"""
    # System action: Optimize code or split query
```

### 6.2 Error Handling Strategy

```
Error Occurs
    ↓
Classify Error Type
    ↓
Log Error with Context
    ↓
Determine Recovery Strategy:
  - Retryable? → Retry with exponential backoff
  - User action needed? → Display helpful message
  - Agent can fix? → Regenerate code
  - Unrecoverable? → Fail gracefully
    ↓
Execute Recovery Strategy
    ↓
Provide Feedback to User:
  - What went wrong
  - Why it happened
  - How to fix it
  - Alternative approaches
```

### 6.3 User-Facing Error Messages

```python
ERROR_MESSAGES = {
    'file_too_large': {
        'title': 'File Too Large',
        'message': 'Your dataset is {size}MB, but the maximum allowed is 100MB.',
        'suggestion': 'Try uploading a sample of your data or splitting it into smaller files.',
        'technical_details': 'S3 upload rejected: size limit exceeded'
    },
    
    'invalid_format': {
        'title': 'Unsupported File Format',
        'message': 'DataScout supports CSV, Excel (.xlsx), and JSON formats.',
        'suggestion': 'Convert your file to one of these formats and try again.',
        'technical_details': 'MIME type detection failed'
    },
    
    'execution_timeout': {
        'title': 'Analysis Taking Too Long',
        'message': 'Your analysis exceeded the 30-second time limit.',
        'suggestion': 'Try simplifying your query or using a smaller dataset.',
        'technical_details': 'Code execution timeout in sandbox'
    },
    
    'missing_column': {
        'title': 'Column Not Found',
        'message': 'The column "{column}" doesn\'t exist in your dataset.',
        'suggestion': 'Available columns: {available_columns}',
        'technical_details': 'KeyError during pandas operation'
    }
}
```

---

## 7. Performance Optimization

### 7.1 Optimization Strategies

#### Code Generation Optimization
```python
# Generate efficient pandas code
BAD:  df.apply(lambda x: custom_func(x), axis=1)  # Slow
GOOD: df['col'].str.method()                       # Vectorized

# Minimize data loading
BAD:  df = pd.read_csv(); df2 = pd.read_csv()     # Redundant
GOOD: df = pd.read_csv(); df2 = df.copy()          # Efficient
```

#### Visualization Optimization
```python
# Lazy rendering for large datasets
if len(df) > 10000:
    # Sample data for visualization
    df_viz = df.sample(n=10000, random_state=42)
else:
    df_viz = df
```

#### Caching Strategy
```python
# Frontend caching
@st.cache_data
def load_dataset(s3_uri):
    """Cache dataset for session"""
    return s3_handler.download_and_parse(s3_uri)

# Agent-level caching (via session state)
# Reuse data analysis across related queries
```

### 7.2 Performance Targets

| Operation | Target | Measurement |
|-----------|--------|-------------|
| File upload | < 5s for 50MB | Time to S3 success |
| Query understanding | < 2s | Agent thinking time |
| Code generation | < 3s | Agent to tool call |
| Code execution | < 30s | Sandbox runtime |
| Visualization | < 3s | Matplotlib render |
| Full E2E query | < 45s | User input to results |

---

## 8. Testing Strategy

### 8.1 Unit Tests

```python
# Test code generation
def test_aggregation_code_generation():
    query = "What is the average sales by region?"
    metadata = {'columns': ['region', 'sales']}
    code = agent.generate_code(query, metadata)
    
    assert 'groupby' in code
    assert 'mean()' in code
    assert 'region' in code

# Test data validation
def test_dataset_validation():
    invalid_file = create_invalid_csv()
    with pytest.raises(DataValidationError):
        s3_handler.upload_dataset(invalid_file)
```

### 8.2 Integration Tests

```python
# Test full query execution flow
def test_end_to_end_query():
    # Upload dataset
    s3_uri = upload_test_dataset()
    
    # Execute query
    response = bedrock_client.invoke_agent(
        query="What is the average sales?",
        dataset_uri=s3_uri
    )
    
    # Verify response
    assert response['code'] is not None
    assert response['results'] is not None
    assert isinstance(response['results'], dict)
```

### 8.3 Demo Test Scenarios

```python
# Critical path testing before demo
DEMO_SCENARIOS = [
    {
        'dataset': 'sales_data.csv',
        'queries': [
            'What are the top 5 products by revenue?',
            'Show me monthly sales trends',
            'What is the correlation between price and quantity?'
        ]
    },
    {
        'dataset': 'customer_data.xlsx',
        'queries': [
            'What is the customer churn rate by region?',
            'Show me customer lifetime value distribution',
        ]
    }
]
```

---

## 9. Monitoring & Observability

### 9.1 Metrics to Track

```python
# Application metrics
METRICS = {
    'query_success_rate': 'Percentage of queries that complete successfully',
    'avg_execution_time': 'Average time from query to results',
    'code_error_rate': 'Percentage of code executions that error',
    'agent_hallucination_rate': 'Detected numerical hallucinations (should be 0%)',
    'concurrent_users': 'Number of active sessions',
    'dataset_size_avg': 'Average dataset size in MB',
}

# Infrastructure metrics
CLOUDWATCH_METRICS = {
    'bedrock_invocations': 'Count of agent invocations',
    'code_interpreter_duration': 'Code execution time',
    's3_upload_time': 'Time to upload datasets',
    'error_rate_by_type': 'Categorized error counts'
}
```

### 9.2 Logging Strategy

```python
# Structured logging
import logging
import json

logger = logging.getLogger('datascout')

def log_query(session_id, query, execution_time, success):
    logger.info(json.dumps({
        'event': 'query_executed',
        'session_id': session_id,
        'query_length': len(query),
        'execution_time_ms': execution_time,
        'success': success,
        'timestamp': datetime.utcnow().isoformat()
        # NOTE: Never log actual query content or data values
    }))
```

### 9.3 Alerting

```yaml
CloudWatch Alarms:
  - Name: HighErrorRate
    Metric: ErrorCount
    Threshold: > 10 errors in 5 minutes
    Action: SNS notification to team
    
  - Name: LongExecutionTime
    Metric: ExecutionDuration
    Threshold: > 45 seconds (p95)
    Action: Log for investigation
    
  - Name: AgentFailure
    Metric: BedrockAgentErrors
    Threshold: > 5 in 5 minutes
    Action: Page on-call engineer
```

---

## 10. Deployment Architecture

### 10.1 AWS Infrastructure

```yaml
Resources:
  
  # Frontend
  AppRunnerService:
    Type: AWS::AppRunner::Service
    Properties:
      ServiceName: datascout-frontend
      SourceConfiguration:
        CodeRepository:
          RepositoryUrl: github.com/org/datascout
          SourceCodeVersion: main
      InstanceConfiguration:
        Cpu: 1 vCPU
        Memory: 2 GB
        
  # Storage
  DataBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: datascout-storage
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: DeleteOldData
            ExpirationInDays: 7
            Status: Enabled
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
              
  # IAM Role for App Runner
  AppRunnerRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: tasks.apprunner.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonBedrockFullAccess
        - !Ref S3AccessPolicy
        
  # Bedrock Agent
  BedrockAgent:
    Type: AWS::Bedrock::Agent
    Properties:
      AgentName: DataScout-Analyst
      FoundationModel: anthropic.claude-3-5-sonnet-20241022-v2:0
      Instruction: !Sub |
        ${AgentInstructions}
      AgentResourceRoleArn: !GetAtt BedrockAgentRole.Arn
```

### 10.2 Environment Configuration

```python
# config.py

import os

class Config:
    # AWS Configuration
    AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
    S3_BUCKET = os.getenv('S3_BUCKET', 'datascout-storage')
    BEDROCK_AGENT_ID = os.getenv('BEDROCK_AGENT_ID')
    BEDROCK_AGENT_ALIAS = os.getenv('BEDROCK_AGENT_ALIAS', 'PRODUCTION')
    
    # Application Configuration
    MAX_FILE_SIZE_MB = 100
    SUPPORTED_FORMATS = ['.csv', '.xlsx', '.json']
    SESSION_TIMEOUT_MINUTES = 30
    
    # Performance Configuration
    CODE_EXECUTION_TIMEOUT = 30  # seconds
    MAX_CONCURRENT_QUERIES = 5
    
    # Feature Flags
    ENABLE_VISUALIZATIONS = True
    ENABLE_ADVANCED_STATS = True
    DEBUG_MODE = os.getenv('DEBUG', 'false').lower() == 'true'
```

---

## 11. Future Enhancements

### 11.1 Phase 2 Features

#### SQL Database Integration
```python
# Connect to enterprise databases
class SQLDataSource:
    def __init__(self, connection_string):
        self.conn = create_engine(connection_string)
        
    def execute_query(self, sql):
        """Execute SQL query generated by agent"""
        df = pd.read_sql(sql, self.conn)
        return df
```

#### Automated Reporting
```python
# Schedule regular reports
class ScheduledAnalytics:
    def create_schedule(self, queries, frequency, recipients):
        """Create scheduled analysis job"""
        # Run queries on schedule
        # Generate PDF reports
        # Email to recipients
```

#### Advanced Analytics
```python
# ML-powered insights
class AdvancedAnalytics:
    def detect_anomalies(self, df, column):
        """Automatic anomaly detection"""
        
    def forecast_trends(self, df, date_col, value_col):
        """Time series forecasting"""
        
    def segment_customers(self, df):
        """Clustering and segmentation"""
```

### 11.2 UI Enhancements

- **Interactive Dashboards:** Real-time filtering and drill-down
- **Collaboration:** Share analyses with team members
- **History:** Browse past queries and results
- **Templates:** Pre-built analysis templates for common use cases
- **Data Catalog:** Browse available datasets and schemas

---

## 12. Documentation

### 12.1 User Documentation

```markdown
# DataScout User Guide

## Getting Started
1. Upload your dataset (CSV, Excel, or JSON)
2. Ask your question in plain English
3. Review the analysis and generated code
4. Download visualizations and results

## Example Queries
- "What are the top 10 customers by revenue?"
- "Show me sales trends over the last 12 months"
- "What is the correlation between price and sales volume?"
- "Group products by category and show average profit margin"

## Tips for Best Results
- Be specific about what you want to analyze
- Mention the columns you're interested in
- Ask for visualizations when helpful
- Break complex questions into steps
```

### 12.2 Developer Documentation

```markdown
# DataScout Developer Guide

## Architecture Overview
DataScout uses a serverless architecture on AWS...

## Local Development Setup
```bash
# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials
aws configure

# Run locally
streamlit run app.py
```

## Adding New Analytical Capabilities
1. Update agent instructions
2. Add Python library to requirements.txt
3. Test with sample queries
4. Deploy to App Runner

## API Reference
[Document all classes and methods]
```

---

## Appendix: Design Decisions

### Why Claude 3.5 Sonnet?
- Superior code generation capabilities
- Strong reasoning for analytical planning
- Excellent instruction following
- Balance of speed and quality

### Why Streamlit?
- Python-native (matches backend)
- Rapid prototyping for hackathon
- Built-in components for data apps
- Easy deployment to AWS App Runner

### Why Code Interpreter over Direct LLM Output?
- Guarantees deterministic accuracy
- Eliminates hallucination risk
- Provides transparency (code visible)
- Enables complex multi-step analyses
- Creates audit trail

### Why S3 over Database?
- Simpler for MVP
- Handles unstructured data
- Built-in lifecycle management
- Cost-effective for temporary storage
- Easy integration with Bedrock

---

**Document Version:** 1.0  
**Last Updated:** February 1, 2026  
**Owner:** DataScout Development Team  
**Status:** Hackathon Implementation Guide
