# DataScout — Folder Structure

**Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team  

---

## 1. Project Root

```
datascout/
├── 📁 streamlit_app/          # Frontend application (Streamlit)
│   ├── app.py                 # Main application entry point
│   ├── components/            # Reusable UI components
│   │   ├── __init__.py
│   │   ├── file_upload.py     # Dataset upload widget
│   │   ├── query_input.py     # Natural language query input
│   │   ├── results_display.py # Analysis results rendering
│   │   ├── code_viewer.py     # Code display with syntax highlighting
│   │   ├── dataset_preview.py # Dataset preview table
│   │   └── visualization.py   # Chart/visualization display
│   ├── services/              # Backend service integrations
│   │   ├── __init__.py
│   │   ├── bedrock_client.py  # Amazon Bedrock Agent wrapper
│   │   ├── s3_handler.py      # S3 upload/download operations
│   │   └── session_manager.py # User session lifecycle
│   ├── utils/                 # Utility functions
│   │   ├── __init__.py
│   │   ├── validators.py      # Input validation (file format, size)
│   │   ├── formatters.py      # Output formatting (tables, markdown)
│   │   ├── error_handler.py   # Error classification & user messages
│   │   └── logger.py          # Structured CloudWatch logging
│   ├── assets/                # Static assets
│   │   ├── logo.png           # DataScout logo
│   │   ├── favicon.ico        # Browser favicon
│   │   └── styles.css         # Custom CSS overrides
│   └── config.py              # Application configuration
│
├── 📁 tests/                  # Test suite
│   ├── __init__.py
│   ├── conftest.py            # Shared fixtures & test config
│   ├── unit/                  # Unit tests (mocked AWS services)
│   │   ├── __init__.py
│   │   ├── test_bedrock_client.py
│   │   ├── test_s3_handler.py
│   │   ├── test_session_manager.py
│   │   ├── test_validators.py
│   │   ├── test_formatters.py
│   │   └── test_error_handler.py
│   ├── integration/           # Integration tests (live AWS)
│   │   ├── __init__.py
│   │   ├── test_upload_flow.py
│   │   ├── test_query_flow.py
│   │   └── test_end_to_end.py
│   └── fixtures/              # Test data & fixtures
│       ├── sample_sales.csv
│       ├── sample_customers.xlsx
│       ├── sample_products.json
│       └── mock_responses.py
│
├── 📁 cloudformation/         # Infrastructure as Code
│   ├── datascout-stack.yaml   # Main CloudFormation template
│   ├── parameters/
│   │   ├── dev.json           # Dev environment parameters
│   │   ├── staging.json       # Staging parameters
│   │   └── prod.json          # Production parameters
│   └── scripts/
│       ├── deploy.sh          # Deployment automation script
│       └── teardown.sh        # Stack teardown script
│
├── 📁 scripts/                # Utility & operational scripts
│   ├── setup_agent.sh         # Bedrock Agent setup automation
│   ├── create_buckets.sh      # S3 bucket creation & config
│   ├── create_iam_roles.sh    # IAM role creation
│   ├── seed_demo_data.py      # Upload demo datasets to S3
│   └── run_demo.py            # Automated demo scenario runner
│
├── 📁 Docs/                   # Project documentation
│   ├── design.md              # System design specification
│   ├── requirements.md        # Requirements specification
│   ├── prd.md                 # Product Requirements Document
│   ├── api_integration.md     # API integration guide
│   ├── deployment.md          # Deployment guide
│   ├── folder_structure.md    # This file — folder structure
│   ├── frontend_spec.md       # Frontend specification
│   ├── roadmap.md             # Product roadmap
│   ├── implementation.md      # Implementation guide
│   ├── test_plan.md           # Test plan
│   ├── frontend_design.md     # Frontend design specification
│   └── data_pipeline.md       # Data pipeline documentation
│
├── 📁 demo/                   # Demo assets
│   ├── datasets/              # Sample datasets for demo
│   │   ├── sales_data.csv
│   │   ├── customer_data.xlsx
│   │   └── product_catalog.json
│   ├── screenshots/           # UI screenshots for docs
│   └── demo_script.md         # Step-by-step demo guide
│
├── 📁 .github/                # GitHub-specific config
│   ├── workflows/
│   │   ├── deploy.yml         # CI/CD deployment pipeline
│   │   ├── test.yml           # Automated test runner
│   │   └── lint.yml           # Code quality checks
│   └── PULL_REQUEST_TEMPLATE.md
│
├── .env.example               # Environment variable template
├── .gitignore                 # Git ignore rules
├── .flake8                    # Linter configuration
├── Dockerfile                 # Docker build for App Runner
├── requirements.txt           # Production dependencies
├── requirements-dev.txt       # Development/test dependencies
├── pyproject.toml             # Project metadata & tool config
├── README.md                  # Project overview & quickstart
└── LICENSE                    # License file
```

---

## 2. Component Descriptions

### 2.1 `streamlit_app/` — Frontend Application

| File | Responsibility | Key Classes/Functions |
|------|---------------|----------------------|
| `app.py` | Main entry point; page layout; routing | `main()`, page config, sidebar |
| `components/file_upload.py` | File upload widget; drag-and-drop | `render_upload_widget()` |
| `components/query_input.py` | Text input for NL queries | `render_query_input()` |
| `components/results_display.py` | Tables, stats, text results | `render_results()` |
| `components/code_viewer.py` | Syntax-highlighted code display | `render_code_block()` |
| `components/dataset_preview.py` | Dataset summary and preview table | `render_preview()` |
| `components/visualization.py` | Chart/image display from S3 | `render_visualization()` |
| `services/bedrock_client.py` | Bedrock Agent API wrapper | `BedrockAgentClient` |
| `services/s3_handler.py` | S3 upload, download, metadata | `S3Handler` |
| `services/session_manager.py` | Session lifecycle management | `SessionManager` |
| `utils/validators.py` | File format/size validation | `validate_file()` |
| `utils/formatters.py` | Output formatting utilities | `format_table()`, `format_stats()` |
| `utils/error_handler.py` | Error classification + messages | `handle_error()`, `ERROR_MESSAGES` |
| `utils/logger.py` | Structured CloudWatch logging | `log_query()`, `log_upload()` |
| `config.py` | Centralized config from env vars | `Config` class |

### 2.2 `tests/` — Test Suite

| Directory | Purpose | Test Framework |
|-----------|---------|---------------|
| `unit/` | Test individual components with mocked AWS | pytest + unittest.mock |
| `integration/` | Test real AWS service interactions | pytest (marked `@pytest.mark.integration`) |
| `fixtures/` | Sample data files and mock response factories | Shared across tests |

### 2.3 `cloudformation/` — Infrastructure as Code

| File | Purpose |
|------|---------|
| `datascout-stack.yaml` | Full stack: S3 + IAM + App Runner + CloudWatch |
| `parameters/*.json` | Environment-specific parameter overrides |
| `scripts/deploy.sh` | One-command deployment automation |
| `scripts/teardown.sh` | Clean stack teardown |

### 2.4 `scripts/` — Operational Scripts

| Script | Purpose |
|--------|---------|
| `setup_agent.sh` | Create & configure Bedrock Agent (idempotent) |
| `create_buckets.sh` | Create S3 bucket with encryption, lifecycle, policies |
| `create_iam_roles.sh` | Create all required IAM roles and policies |
| `seed_demo_data.py` | Upload demo CSV/XLSX/JSON to S3 for testing |
| `run_demo.py` | Execute a sequence of demo queries and capture output |

---

## 3. Dependency Files

### 3.1 `requirements.txt` (Production)

```txt
streamlit>=1.25.0
boto3>=1.26.0
botocore>=1.29.0
pandas>=1.5.0
numpy>=1.23.0
matplotlib>=3.5.0
seaborn>=0.12.0
python-dotenv>=1.0.0
watchtower>=3.0.0
```

### 3.2 `requirements-dev.txt` (Development)

```txt
-r requirements.txt
pytest>=7.4.0
pytest-cov>=4.1.0
pytest-mock>=3.11.0
moto>=4.2.0          # AWS service mocking
flake8>=6.1.0
black>=23.7.0
mypy>=1.5.0
```

### 3.3 `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*.egg-info/
dist/
venv/
.venv/

# Environment
.env
.env.local

# IDE
.vscode/
.idea/
*.swp

# OS
.DS_Store
Thumbs.db

# AWS
*.pem
trust-policy.json
*-policy.json

# Test artifacts
.coverage
htmlcov/
.pytest_cache/
```

---

## 4. File Naming Conventions

| Convention | Example | Applies To |
|------------|---------|-----------|
| Snake case | `bedrock_client.py` | All Python files |
| Lowercase | `config.py` | All source files |
| Test prefix | `test_bedrock_client.py` | All test files |
| Uppercase | `README.md`, `LICENSE` | Root documentation |
| Lowercase with underscores | `sample_sales.csv` | Fixture/demo files |
| Kebab case | `datascout-stack.yaml` | CloudFormation templates |

---

## 5. Directory Guidelines

### Do's ✅
- Keep components focused on a single responsibility
- Place all AWS service interactions in `services/`
- Put shared utilities in `utils/`
- Store test data in `tests/fixtures/`
- Keep infrastructure code in `cloudformation/`
- Document every new file in this folder structure document

### Don'ts ❌
- Don't put business logic directly in `app.py` — use components/services
- Don't mix unit and integration tests in the same directory
- Don't hardcode credentials — use environment variables via `config.py`
- Don't put demo assets in the source code directory
- Don't commit `.env` files — use `.env.example` as a template

---

**Document Version:** 1.0  
**Last Updated:** February 24, 2026  
**Owner:** DataScout Development Team
