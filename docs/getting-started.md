# Getting Started with GuardStack

This guide will help you get GuardStack up and running quickly, whether you're evaluating it locally or deploying to production.

## Overview

GuardStack is an AI safety and security platform that helps you:

1. **Register** AI models (predictive ML, Gen AI, or agentic systems)
2. **Evaluate** models against safety and security pillars
3. **Monitor** risks with real-time dashboards
4. **Generate** compliance reports (EU AI Act, SOC 2, etc.)
5. **Protect** inference with runtime guardrails

## Prerequisites

Before you begin, ensure you have:

| Requirement | Version | Purpose |
|-------------|---------|---------|
| Python | 3.11+ | Backend API |
| Docker | 24+ | Infrastructure |
| Node.js | 18+ | UI development (optional) |

## Quick Start (5 minutes)

### 1. Clone the Repository

```bash
git clone https://github.com/guardstack/guardstack.git
cd guardstack
```

### 2. Start with Docker Compose

```bash
# Start all services
docker-compose up -d

# Verify services are running
docker-compose ps
```

This starts:
- **GuardStack API** on `http://localhost:8000`
- **PostgreSQL** with pgvector extension
- **Redis** for caching and pub/sub
- **MinIO** for artifact storage

### 3. Access the UI

Open your browser to `http://localhost:8080`

### 4. Register Your First Model

```bash
curl -X POST http://localhost:8000/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-first-model",
    "model_type": "genai",
    "connector_type": "openai",
    "connector_config": {
      "model": "gpt-3.5-turbo"
    }
  }'
```

### 5. Run an Evaluation

```bash
# Replace MODEL_ID with the ID from the previous response
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "MODEL_ID",
    "evaluation_type": "genai",
    "config": {
      "pillars": ["privacy", "toxicity"]
    }
  }'
```

## Local Development Setup

For developers who want to contribute or customize GuardStack:

### 1. Create Virtual Environment

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
# Install with development extras
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install
```

### 3. Start Infrastructure

```bash
# Start only database services
docker-compose up -d postgres redis minio
```

### 4. Configure Environment

Create a `.env` file:

```env
GUARDSTACK_ENVIRONMENT=development
GUARDSTACK_DEBUG=true
GUARDSTACK_DATABASE_URL=postgresql+asyncpg://guardstack:guardstack@localhost:5432/guardstack
GUARDSTACK_REDIS_URL=redis://localhost:6379/0
GUARDSTACK_S3_ENDPOINT=localhost:9000
GUARDSTACK_OPENAI_API_KEY=sk-your-key-here
```

### 5. Run Migrations

```bash
alembic upgrade head
```

### 6. Start the API Server

```bash
uvicorn guardstack.main:app --reload --host 0.0.0.0 --port 8000
```

### 7. Start the Frontend (Optional)

```bash
cd pkg/guardstack
npm install
npm run dev
```

## Connecting Your First Model

### OpenAI

```python
from guardstack import GuardStackClient

client = GuardStackClient("http://localhost:8000")

model = client.models.create(
    name="gpt-4-assistant",
    model_type="genai",
    connector_type="openai",
    connector_config={
        "model": "gpt-4",
        "api_key": "sk-...",  # Or use environment variable
    }
)
```

### Anthropic Claude

```python
model = client.models.create(
    name="claude-assistant",
    model_type="genai",
    connector_type="anthropic",
    connector_config={
        "model": "claude-3-opus-20240229",
        "api_key": "sk-ant-...",
    }
)
```

### Self-Hosted (Ollama)

```python
model = client.models.create(
    name="llama3-local",
    model_type="genai",
    connector_type="ollama",
    connector_config={
        "model": "llama3",
        "endpoint": "http://localhost:11434",
    }
)
```

### Predictive ML Model

```python
model = client.models.create(
    name="fraud-detector",
    model_type="predictive",
    connector_type="custom",
    connector_config={
        "endpoint": "http://my-model-server:8080/predict",
        "headers": {"Authorization": "Bearer token"},
    }
)
```

## Running Evaluations

### Gen AI Evaluation (4 Pillars)

```python
evaluation = client.evaluations.create(
    model_id=model.id,
    evaluation_type="genai",
    config={
        "pillars": ["privacy", "toxicity", "fairness", "security"],
        "sample_size": 500,
        "garak_probes": ["dan", "encoding"],
    }
)

# Start and wait for results
client.evaluations.start(evaluation.id)
```

### Predictive ML Evaluation (8 Pillars)

```python
evaluation = client.evaluations.create(
    model_id=model.id,
    evaluation_type="predictive",
    config={
        "pillars": [
            "explain", "actions", "fairness", "robustness",
            "trace", "testing", "imitation", "privacy"
        ],
        "test_dataset": "path/to/test_data.csv",
    }
)
```

### Security Posture Scan

```python
scan = client.spm.scan(
    model_id=model.id,
    checks=["supply_chain", "model_access", "data_exposure"],
)
```

## Understanding Results

### Score Interpretation

| Score | Status | Meaning |
|-------|--------|---------|
| ≥80 | 🟢 Pass | Ready for production |
| 50-79 | 🟡 Warn | Needs attention |
| <50 | 🔴 Fail | Critical issues |

### Pillar Results

Each pillar provides:
- **Score**: 0-100 normalized score
- **Findings**: Specific issues discovered
- **Recommendations**: Suggested remediations
- **Evidence**: Supporting data and examples

## Next Steps

Now that you have GuardStack running:

1. **Explore the Dashboard**: View your model portfolio at `http://localhost:8080`
2. **Set Up Guardrails**: Configure real-time protection for inference
3. **Generate Reports**: Create compliance documentation
4. **Integrate CI/CD**: Add evaluations to your deployment pipeline

## Common Issues

### Connection Refused

```bash
# Check if services are running
docker-compose ps

# View logs
docker-compose logs guardstack-api
```

### Database Migration Errors

```bash
# Reset database
docker-compose down -v
docker-compose up -d postgres
alembic upgrade head
```

### API Key Issues

Ensure your API keys are correctly set in environment variables or connector config.

## Getting Help

- **Documentation**: [docs.guardstack.io](https://docs.guardstack.io)
- **GitHub Issues**: [Report bugs](https://github.com/guardstack/guardstack/issues)
- **Discord**: [Join our community](https://discord.gg/guardstack)
