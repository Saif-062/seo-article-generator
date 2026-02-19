# SEO Article Generator

An AI-powered backend service that generates SEO-optimized articles by analyzing search engine results and producing high-quality, publish-ready content.

## Features

- **SERP Analysis**: Fetches and analyzes top 10 Google search results for any topic
- **Theme Extraction**: Identifies common themes, search intent, and content gaps
- **Smart Outline Generation**: Creates structured outlines with word count allocation
- **Article Generation**: Produces full, human-readable articles following SEO best practices
- **SEO Validation**: Validates content against SEO criteria with automatic revision loop
- **Job Persistence**: Saves progress to JSON files, enabling crash recovery and resume
- **Async Processing**: Background job execution with status polling

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         FastAPI Server                          │
├─────────────────────────────────────────────────────────────────┤
│  POST /jobs        GET /jobs/{id}        POST /jobs/{id}/resume │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Pipeline Orchestrator                         │
├─────────────────────────────────────────────────────────────────┤
│  Step 1: SERP Analysis      → serp_data                         │
│  Step 2: Theme Extraction   → theme_analysis                    │
│  Step 3: Outline Generation → outline                           │
│  Step 4: Article Generation → draft_article                     │
│  Step 5: SEO Validation     → final_article (with revision)     │
└─────────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┴───────────────┐
              ▼                               ▼
┌─────────────────────────┐     ┌─────────────────────────┐
│     SERP Provider       │     │      LLM Provider       │
├─────────────────────────┤     ├─────────────────────────┤
│  • Serper.dev (real)    │     │  • Groq (Llama 3.3 70B) │
│  • Mock (testing)       │     │  • Mock (testing)       │
└─────────────────────────┘     └─────────────────────────┘
```

## Quick Start

### 1. Clone and Install

```bash
git clone <repo-url>
cd seo-article-generator

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Configure API Keys

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your API keys
# Get Serper.dev key: https://serper.dev (2,500 free searches)
# Get Groq key: https://console.groq.com (free tier)
```

### 3. Run the Server

```bash
# Development mode
uvicorn app.main:app --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### 4. Generate an Article

```bash
# Create a job
curl -X POST http://localhost:8000/api/v1/jobs \
  -H "Content-Type: application/json" \
  -d '{"topic": "best productivity tools for remote teams", "word_count": 1500}'

# Response: {"job_id": "abc12345", "status": "pending", ...}

# Check status
curl http://localhost:8000/api/v1/jobs/abc12345/status

# Get results when complete
curl http://localhost:8000/api/v1/jobs/abc12345
```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/health` | GET | Health check with provider status |
| `/api/v1/jobs` | POST | Create new article generation job |
| `/api/v1/jobs` | GET | List all jobs (with optional status filter) |
| `/api/v1/jobs/{id}` | GET | Get job details and results |
| `/api/v1/jobs/{id}/status` | GET | Get lightweight job status |
| `/api/v1/jobs/{id}/resume` | POST | Resume a failed/interrupted job |

## Input/Output Example

### Input

```json
{
  "topic": "best productivity tools for remote teams",
  "word_count": 1500,
  "language": "en"
}
```

### Output (when complete)

```json
{
  "job_id": "abc12345",
  "status": "completed",
  "article": {
    "article_markdown": "# Best Productivity Tools for Remote Teams\n\nRemote work has transformed...",
    "heading_structure": [
      {"level": 1, "text": "Best Productivity Tools for Remote Teams"},
      {"level": 2, "text": "Introduction"},
      {"level": 2, "text": "Top Communication Tools"},
      {"level": 3, "text": "Slack"},
      ...
    ],
    "seo_metadata": {
      "title_tag": "Best Productivity Tools for Remote Teams in 2025",
      "meta_description": "Discover the top productivity tools that help remote teams collaborate effectively. Compare features, pricing, and find the perfect fit.",
      "slug": "best-productivity-tools-remote-teams",
      "primary_keyword": "productivity tools for remote teams",
      "secondary_keywords": ["remote work tools", "team collaboration", "project management"]
    },
    "keyword_analysis": {
      "primary_keyword": "productivity tools for remote teams",
      "primary_count": 12,
      "primary_density": 0.008,
      "secondary_keywords": ["remote work", "collaboration"],
      "secondary_counts": {"remote work": 8, "collaboration": 5}
    },
    "internal_links": [
      {
        "anchor_text": "project management software",
        "target_topic": "project management guide",
        "placement_hint": "tools comparison section"
      },
      ...
    ],
    "external_references": [
      {
        "url": "https://example.com/remote-work-study",
        "source_name": "Harvard Business Review",
        "why_authoritative": "Leading business publication with research-backed insights",
        "placement_hint": "introduction section"
      },
      ...
    ],
    "seo_validation": {
      "passed": true,
      "score": 92.5,
      "checks": [
        {"name": "single_h1", "passed": true, "message": "Article has exactly one H1"},
        {"name": "keyword_in_title", "passed": true, "message": "Primary keyword appears in title"},
        ...
      ],
      "issues": []
    },
    "word_count": 1523
  }
}
```

## Running Tests

```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test file
pytest tests/test_seo_validator.py -v
```

## Project Structure

```
seo-article-generator/
├── app/
│   ├── api/
│   │   ├── routes.py          # FastAPI endpoints
│   │   └── schemas.py         # Request/response models
│   ├── models/
│   │   ├── article.py         # Article and SEO models
│   │   ├── job.py             # Job state models
│   │   └── serp.py            # SERP data models
│   ├── pipeline/
│   │   ├── orchestrator.py    # Pipeline coordination
│   │   └── steps/
│   │       ├── serp_analysis.py
│   │       ├── theme_extraction.py
│   │       ├── outline_generation.py
│   │       ├── article_generation.py
│   │       └── seo_validation.py
│   ├── providers/
│   │   ├── serp/
│   │   │   ├── serper.py      # Serper.dev implementation
│   │   │   └── mock.py        # Mock for testing
│   │   └── llm/
│   │       ├── groq.py        # Groq implementation
│   │       └── mock.py        # Mock for testing
│   ├── persistence/
│   │   └── job_store.py       # JSON file storage
│   ├── config.py              # Settings management
│   └── main.py                # FastAPI application
├── tests/
│   ├── test_api.py
│   ├── test_models.py
│   ├── test_seo_validator.py
│   └── test_job_persistence.py
├── data/
│   └── jobs/                  # Job JSON files
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Design Decisions

### 1. Checkpoint-based Persistence
Each pipeline step saves progress to a JSON file. If the process crashes after completing SERP analysis, it can resume from theme extraction without re-fetching search results.

### 2. Provider Abstraction
SERP and LLM providers are abstracted behind interfaces, allowing:
- Easy swapping between real APIs and mocks
- Testing without consuming API credits
- Future extensibility to other providers

### 3. Async Background Processing
Jobs run asynchronously to keep the API responsive. Clients poll for status rather than waiting for long-running operations.

### 4. SEO Validation with Revision Loop
Articles are validated against SEO criteria (keyword placement, heading structure, meta description length). If validation fails, the system automatically requests LLM revisions up to 2 times.

### 5. Structured Output
All outputs use Pydantic models for type safety and validation. The final article package includes everything needed for publishing: content, metadata, keywords, and linking suggestions.

## Configuration

Environment variables (via `.env` file):

| Variable | Description | Default |
|----------|-------------|---------|
| `SERPER_API_KEY` | Serper.dev API key | - |
| `GROQ_API_KEY` | Groq API key | - |
| `USE_MOCK_SERP` | Use mock SERP provider | `false` |
| `USE_MOCK_LLM` | Use mock LLM provider | `false` |
| `LLM_MODEL` | Groq model to use | `llama-3.3-70b-versatile` |

## Running Without API Keys

The system falls back to mock providers when API keys aren't configured:

```bash
# Run with mocks (no API keys needed)
USE_MOCK_SERP=true USE_MOCK_LLM=true uvicorn app.main:app --reload
```

Mock providers return realistic fixture data, useful for:
- Demo/testing without costs
- Development workflow
- CI/CD pipelines

## License

MIT
