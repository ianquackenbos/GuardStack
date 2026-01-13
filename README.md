# GuardStack - AI Safety & Security Platform

[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![Kubernetes](https://img.shields.io/badge/kubernetes-native-326CE5.svg)](https://kubernetes.io/)
[![Rancher](https://img.shields.io/badge/rancher-extension-0075A8.svg)](https://rancher.com/)

<p align="center">
  <img src="docs/assets/guardstack-logo.svg" alt="GuardStack Logo" width="200"/>
</p>

**GuardStack** is a comprehensive, open-source AI safety and security platform designed for Kubernetes-native deployment. It provides quantitative risk metrics for AI models across the entire AI lifecycle, from development through production inference.

> **Open-source alternative to Chatterbox Labs AIMI** - Enterprise-grade AI risk management without vendor lock-in.

---

## 📋 Table of Contents

- [Features](#-features)
- [Architecture](#-architecture)
- [Quick Start](#-quick-start)
- [Installation](#-installation)
- [Configuration](#-configuration)
- [Usage](#-usage)
- [API Reference](#-api-reference)
- [Connectors](#-connectors)
- [Compliance](#-compliance)
- [Contributing](#-contributing)
- [License](#-license)

---

## ✨ Features

### Evaluation Modules

| Module | Pillars | Description |
|--------|---------|-------------|
| **Predictive AI** | 8 Pillars | Explain, Actions, Fairness, Robustness, Trace, Testing, Imitation, Privacy |
| **Gen AI** | 4 Pillars | Privacy, Toxicity, Fairness, Security |
| **AI-SPM** | Security Posture | Comprehensive AI security posture management |
| **Agentic AI** | Agent Security | MCP tool calling security and agent guardrails |

### Key Capabilities

- 🛡️ **Automated Red Teaming** - Garak integration for LLM security testing
- 🔍 **PII Detection** - Presidio-powered personal data identification
- ⚖️ **Fairness Analysis** - Bias detection across demographics
- 🎯 **Adversarial Testing** - IBM ART for robustness evaluation
- 📊 **Executive Dashboard** - Pass/Warn/Fail portfolio view with trends
- 📋 **Compliance Reports** - EU AI Act, SOC2, HIPAA, ISO 27001 mapping
- 🔒 **Runtime Guardrails** - Real-time inference protection with NeMo Guardrails
- 🔄 **CI/CD Integration** - GitHub Actions, GitLab CI, Jenkins support
- 📈 **Vector Embeddings** - pgvector for semantic similarity and RAG evaluation

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                       GuardStack Platform (Kubernetes)                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                    Rancher UI Extension (Vue 3)                      │   │
│  │  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐  │   │
│  │  │Dashboard │ │Predictive│ │  Gen AI  │ │  AI-SPM  │ │ Agentic  │  │   │
│  │  │ Overview │ │ 8 Pillars│ │ 4 Pillars│ │ Posture  │ │ Security │  │   │
│  │  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                     API Gateway (FastAPI)                            │   │
│  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ ┌────────┐ │   │
│  │  │ Models │ │ Evals  │ │Comply  │ │Guards  │ │Connect │ │  WS    │ │   │
│  │  └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ └────────┘ │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                    │                                         │
│         ┌──────────────────────────┼──────────────────────────┐             │
│         ▼                          ▼                          ▼             │
│  ┌─────────────┐         ┌─────────────────┐         ┌─────────────┐       │
│  │    Argo     │         │   Evaluation    │         │  Real-time  │       │
│  │  Workflows  │         │     Engine      │         │  Guardrails │       │
│  │   (DAGs)    │         │  (Garak, ART,   │         │   (NeMo)    │       │
│  │             │         │   Fairlearn)    │         │             │       │
│  └─────────────┘         └─────────────────┘         └─────────────┘       │
│         │                          │                          │             │
│         └──────────────────────────┼──────────────────────────┘             │
│                                    ▼                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐     │   │
│  │  │   PostgreSQL    │  │      Redis      │  │    MinIO/S3     │     │   │
│  │  │   + pgvector    │  │   (Cache/PubSub)│  │   (Artifacts)   │     │   │
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘     │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 🚀 Quick Start

### Option 1: Docker Compose (Development)

The fastest way to get started locally:

```bash
# Clone the repository
git clone https://github.com/guardstack/guardstack.git
cd guardstack

# Start all services
docker-compose up -d

# Access the UI
open http://localhost:8080
```

### Option 2: Kubernetes with Helm (Production)

```bash
# Add the GuardStack Helm repository
helm repo add guardstack https://guardstack.github.io/charts
helm repo update

# Install GuardStack
helm install guardstack guardstack/guardstack \
  --namespace guardstack \
  --create-namespace \
  --values values.yaml
```

### Option 3: Local Development

```bash
# Clone the repository
git clone https://github.com/guardstack/guardstack.git
cd guardstack

# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -e ".[dev]"

# Start infrastructure (PostgreSQL, Redis, MinIO)
docker-compose up -d postgres redis minio

# Run database migrations
alembic upgrade head

# Start the API server
uvicorn guardstack.main:app --reload --host 0.0.0.0 --port 8000

# In another terminal, start the frontend
cd pkg/guardstack
npm install
npm run dev
```

---

## 📦 Installation

### Prerequisites

| Requirement | Version | Notes |
|-------------|---------|-------|
| Python | 3.11+ | Required for backend |
| Node.js | 18+ | Required for UI development |
| Docker | 24+ | For containerized deployment |
| Kubernetes | 1.28+ | For production deployment |
| Helm | 3.12+ | For Kubernetes installation |
| PostgreSQL | 16+ | With pgvector extension |
| Redis | 7+ | For caching and pub/sub |

### Kubernetes Installation

#### 1. Install Prerequisites

```bash
# Install Argo Workflows (required for evaluation orchestration)
kubectl create namespace argo
kubectl apply -n argo -f https://github.com/argoproj/argo-workflows/releases/download/v3.5.0/install.yaml

# Verify Argo is running
kubectl -n argo get pods
```

#### 2. Configure Values

Create a `values.yaml` file:

```yaml
# values.yaml
global:
  storageClass: "standard"

api:
  replicas: 2
  resources:
    requests:
      memory: "512Mi"
      cpu: "250m"
    limits:
      memory: "2Gi"
      cpu: "1000m"

postgresql:
  enabled: true
  auth:
    postgresPassword: "your-secure-password"
    database: "guardstack"
  primary:
    persistence:
      size: 50Gi

redis:
  enabled: true
  auth:
    password: "your-redis-password"

minio:
  enabled: true
  rootUser: "guardstack"
  rootPassword: "your-minio-password"
  persistence:
    size: 100Gi

# LLM Connector Configuration
connectors:
  openai:
    enabled: true
    apiKeySecret: "openai-api-key"
  anthropic:
    enabled: true
    apiKeySecret: "anthropic-api-key"
  ollama:
    enabled: true
    endpoint: "http://ollama.default.svc:11434"

# Rancher UI Extension
ui:
  enabled: true
```

#### 3. Create Secrets

```bash
# Create namespace
kubectl create namespace guardstack

# Create API key secrets
kubectl create secret generic openai-api-key \
  --namespace guardstack \
  --from-literal=api-key="sk-your-openai-key"

kubectl create secret generic anthropic-api-key \
  --namespace guardstack \
  --from-literal=api-key="sk-ant-your-anthropic-key"
```

#### 4. Install GuardStack

```bash
helm install guardstack guardstack/guardstack \
  --namespace guardstack \
  --values values.yaml \
  --wait
```

#### 5. Verify Installation

```bash
# Check pods
kubectl -n guardstack get pods

# Check services
kubectl -n guardstack get svc

# Get the API endpoint
kubectl -n guardstack get ingress
```

---

## ⚙️ Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GUARDSTACK_HOST` | API server host | `0.0.0.0` |
| `GUARDSTACK_PORT` | API server port | `8000` |
| `GUARDSTACK_DEBUG` | Enable debug mode | `false` |
| `GUARDSTACK_DATABASE_URL` | PostgreSQL connection string | `postgresql+asyncpg://...` |
| `GUARDSTACK_REDIS_URL` | Redis connection string | `redis://localhost:6379/0` |
| `GUARDSTACK_S3_ENDPOINT` | MinIO/S3 endpoint | `localhost:9000` |
| `GUARDSTACK_S3_ACCESS_KEY` | S3 access key | `minioadmin` |
| `GUARDSTACK_S3_SECRET_KEY` | S3 secret key | `minioadmin` |
| `GUARDSTACK_ARGO_NAMESPACE` | Argo Workflows namespace | `argo` |
| `GUARDSTACK_OPENAI_API_KEY` | OpenAI API key | - |
| `GUARDSTACK_ANTHROPIC_API_KEY` | Anthropic API key | - |
| `GUARDSTACK_OLLAMA_ENDPOINT` | Ollama server endpoint | `http://localhost:11434` |

### Configuration File

Create a `.env` file in the project root:

```env
# Server
GUARDSTACK_ENVIRONMENT=development
GUARDSTACK_DEBUG=true

# Database
GUARDSTACK_DATABASE_URL=postgresql+asyncpg://guardstack:guardstack@localhost:5432/guardstack

# Redis
GUARDSTACK_REDIS_URL=redis://localhost:6379/0

# Storage
GUARDSTACK_S3_ENDPOINT=localhost:9000
GUARDSTACK_S3_ACCESS_KEY=minioadmin
GUARDSTACK_S3_SECRET_KEY=minioadmin
GUARDSTACK_S3_BUCKET=guardstack

# Model Connectors
GUARDSTACK_OPENAI_API_KEY=sk-your-key
GUARDSTACK_ANTHROPIC_API_KEY=sk-ant-your-key
GUARDSTACK_OLLAMA_ENDPOINT=http://localhost:11434

# Scoring
GUARDSTACK_SCORE_PASS_THRESHOLD=80.0
GUARDSTACK_SCORE_WARN_THRESHOLD=50.0
```

---

## 📖 Usage

### Registering a Model

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/models \
  -H "Content-Type: application/json" \
  -d '{
    "name": "gpt-4-production",
    "description": "Production GPT-4 model for customer support",
    "model_type": "genai",
    "connector_type": "openai",
    "connector_config": {
      "model": "gpt-4",
      "temperature": 0.7
    },
    "tags": ["production", "customer-support"]
  }'
```

#### Via Python SDK

```python
from guardstack import GuardStackClient

client = GuardStackClient(base_url="http://localhost:8000")

model = client.models.create(
    name="gpt-4-production",
    model_type="genai",
    connector_type="openai",
    connector_config={
        "model": "gpt-4",
        "temperature": 0.7
    }
)
print(f"Registered model: {model.id}")
```

### Running an Evaluation

#### Via API

```bash
curl -X POST http://localhost:8000/api/v1/evaluations \
  -H "Content-Type: application/json" \
  -d '{
    "model_id": "your-model-uuid",
    "evaluation_type": "genai",
    "config": {
      "pillars": ["privacy", "toxicity", "fairness", "security"],
      "sample_size": 1000,
      "garak_probes": ["dan", "encoding", "glitch"]
    }
  }'
```

#### Via Python SDK

```python
evaluation = client.evaluations.create(
    model_id=model.id,
    evaluation_type="genai",
    pillars=["privacy", "toxicity", "fairness", "security"],
    config={
        "sample_size": 1000,
        "garak_probes": ["dan", "encoding", "glitch"]
    }
)

# Start the evaluation
client.evaluations.start(evaluation.id)

# Monitor progress via WebSocket
async for progress in client.evaluations.stream(evaluation.id):
    print(f"Progress: {progress.percentage}% - {progress.current_step}")
```

### Viewing Results

```python
# Get evaluation results
results = client.evaluations.get_results(evaluation.id)

print(f"Overall Score: {results.overall_score}")
print(f"Status: {results.status}")  # pass, warn, fail

for pillar, score in results.pillar_scores.items():
    print(f"  {pillar}: {score}")
```

### Generating Compliance Reports

```python
report = client.compliance.generate_report(
    model_id=model.id,
    framework="eu_ai_act",
    format="pdf"
)

# Download the report
client.compliance.download(report.id, "compliance-report.pdf")
```

---

## 📡 API Reference

### Models

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/models` | GET | List all registered models |
| `/api/v1/models` | POST | Register a new model |
| `/api/v1/models/{id}` | GET | Get model details |
| `/api/v1/models/{id}` | PATCH | Update model |
| `/api/v1/models/{id}` | DELETE | Delete model |
| `/api/v1/models/{id}/evaluations` | GET | List model evaluations |

### Evaluations

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/evaluations` | GET | List all evaluations |
| `/api/v1/evaluations` | POST | Create new evaluation |
| `/api/v1/evaluations/{id}` | GET | Get evaluation details |
| `/api/v1/evaluations/{id}/start` | POST | Start evaluation |
| `/api/v1/evaluations/{id}/cancel` | POST | Cancel evaluation |
| `/api/v1/evaluations/{id}/results` | GET | Get evaluation results |

### Compliance

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/compliance/status` | GET | Get compliance status |
| `/api/v1/compliance/eu-ai-act/{model_id}` | GET | EU AI Act status |
| `/api/v1/compliance/reports` | POST | Generate report |
| `/api/v1/compliance/reports/{id}` | GET | Get report |

### WebSocket

| Endpoint | Description |
|----------|-------------|
| `/ws/evaluations/{id}` | Real-time evaluation progress |
| `/ws/user/{id}` | User notifications |
| `/ws/broadcast` | System-wide announcements |

### Full API Documentation

Interactive API documentation is available at:
- **Swagger UI**: `http://localhost:8000/api/docs`
- **ReDoc**: `http://localhost:8000/api/redoc`
- **OpenAPI Spec**: `http://localhost:8000/api/openapi.json`

---

## 🔌 Connectors

GuardStack supports 12 LLM providers out of the box:

| Provider | Type | Configuration |
|----------|------|---------------|
| **OpenAI** | Cloud | `api_key`, `model`, `organization` |
| **Anthropic** | Cloud | `api_key`, `model` |
| **Azure OpenAI** | Cloud | `api_key`, `endpoint`, `deployment`, `api_version` |
| **AWS Bedrock** | Cloud | `region`, `access_key`, `secret_key`, `model_id` |
| **GCP Vertex AI** | Cloud | `project_id`, `location`, `model` |
| **Mistral AI** | Cloud | `api_key`, `model` |
| **Cohere** | Cloud | `api_key`, `model` |
| **Ollama** | Self-hosted | `endpoint`, `model` |
| **vLLM** | Self-hosted | `endpoint`, `model` |
| **LM Studio** | Self-hosted | `endpoint`, `model` |
| **HuggingFace** | Self-hosted | `api_key`, `model`, `endpoint` |
| **Custom** | Any | `endpoint`, `headers`, `request_template` |

### Adding a Custom Connector

```python
from guardstack.connectors import BaseConnector

class MyCustomConnector(BaseConnector):
    async def generate(self, prompt: str, **kwargs) -> str:
        # Your implementation
        pass
    
    async def health_check(self) -> bool:
        # Your implementation
        pass
```

---

## 📋 Compliance

### Supported Frameworks

| Framework | Coverage | Auto-Mapping |
|-----------|----------|--------------|
| **EU AI Act** | Full | ✅ Yes |
| **SOC 2** | Type II | ✅ Yes |
| **HIPAA** | Technical Safeguards | ✅ Yes |
| **ISO 27001** | Annex A Controls | ✅ Yes |
| **NIST AI RMF** | Full Framework | ✅ Yes |

### EU AI Act Risk Classification

GuardStack automatically classifies AI systems according to EU AI Act risk levels:

- **Unacceptable Risk**: Systems that are prohibited
- **High Risk**: Systems requiring conformity assessment
- **Limited Risk**: Systems requiring transparency obligations
- **Minimal Risk**: No specific requirements

---

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=guardstack --cov-report=html

# Run specific test modules
pytest tests/test_predictive.py
pytest tests/test_genai.py
pytest tests/test_connectors.py

# Run integration tests (requires Docker)
pytest tests/integration/ --integration
```

---

## 📁 Project Structure

```
guardstack/
├── src/guardstack/              # Python backend
│   ├── api/                     # FastAPI routers
│   │   ├── routers/            # API endpoints
│   │   │   ├── models.py
│   │   │   ├── evaluations.py
│   │   │   ├── compliance.py
│   │   │   ├── guardrails.py
│   │   │   ├── connectors.py
│   │   │   ├── dashboard.py
│   │   │   └── websocket.py
│   │   └── dependencies.py     # Auth, pagination
│   ├── predictive/             # 8-pillar predictive AI
│   │   ├── pillars/
│   │   │   ├── explain.py      # SHAP, LIME, Captum
│   │   │   ├── actions.py      # Recourse analysis
│   │   │   ├── fairness.py     # Fairlearn, AIF360
│   │   │   ├── robustness.py   # IBM ART
│   │   │   ├── trace.py        # Lineage tracking
│   │   │   ├── testing.py      # Metamorphic testing
│   │   │   ├── imitation.py    # Model extraction
│   │   │   └── privacy.py      # Differential privacy
│   │   └── evaluator.py
│   ├── genai/                  # 4-pillar Gen AI
│   │   ├── pillars/
│   │   │   ├── privacy.py      # PII detection
│   │   │   ├── toxicity.py     # Detoxify
│   │   │   ├── fairness.py     # Demographic bias
│   │   │   └── security.py     # Prompt injection
│   │   ├── garak/              # Garak integration
│   │   │   ├── runner.py
│   │   │   ├── probes.py
│   │   │   └── parsers.py
│   │   └── evaluator.py
│   ├── spm/                    # AI Security Posture
│   │   ├── scanner.py
│   │   └── checks.py
│   ├── agentic/                # Agentic AI Security
│   │   ├── evaluator.py
│   │   ├── interceptor.py
│   │   ├── sandbox.py
│   │   └── tool_security.py
│   ├── connectors/             # LLM integrations
│   │   ├── providers/
│   │   │   ├── openai.py
│   │   │   ├── anthropic.py
│   │   │   ├── azure.py
│   │   │   ├── aws_bedrock.py
│   │   │   ├── gcp_vertex.py
│   │   │   ├── ollama.py
│   │   │   ├── vllm.py
│   │   │   ├── lmstudio.py
│   │   │   ├── mistral.py
│   │   │   ├── cohere.py
│   │   │   ├── huggingface.py
│   │   │   └── custom.py
│   │   ├── base.py
│   │   └── registry.py
│   ├── guardrails/             # Runtime guardrails
│   │   ├── policies.py
│   │   └── filters.py
│   ├── compliance/             # Compliance mapping
│   │   ├── frameworks.py
│   │   ├── assessor.py
│   │   ├── mapper.py
│   │   └── reporter.py
│   ├── scoring/                # Score aggregation
│   │   ├── aggregator.py
│   │   ├── normalizer.py
│   │   ├── weights.py
│   │   └── thresholds.py
│   ├── workflows/              # Argo integration
│   │   ├── argo_client.py
│   │   └── templates.py
│   ├── models/                 # Data models
│   │   ├── core.py
│   │   └── evaluation.py
│   ├── services/               # Backend services
│   │   ├── database.py
│   │   ├── cache.py
│   │   └── storage.py
│   ├── config.py               # Settings
│   └── main.py                 # FastAPI app
├── pkg/guardstack/             # Rancher UI Extension
│   ├── pages/                  # Vue pages
│   ├── components/             # Vue components
│   ├── store/                  # Pinia stores
│   ├── composables/            # Vue composables
│   ├── services/               # API services
│   ├── types/                  # TypeScript types
│   └── routing/                # Vue Router config
├── charts/guardstack/          # Helm chart
│   ├── templates/
│   └── values.yaml
├── docker/                     # Docker configurations
├── migrations/                 # Alembic migrations
├── tests/                      # Test suites
└── docs/                       # Documentation
```

---

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/guardstack.git
cd guardstack

# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Run linting
ruff check src/
mypy src/
```

### Code Style

- **Python**: We use `ruff` for linting and `black` for formatting
- **TypeScript/Vue**: We use ESLint and Prettier
- **Commits**: Follow [Conventional Commits](https://www.conventionalcommits.org/)

---

## 📜 License

This project is licensed under the Apache License 2.0 - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

GuardStack builds upon excellent open-source projects:

| Project | Usage |
|---------|-------|
| [Garak](https://github.com/leondz/garak) | LLM security probes |
| [IBM ART](https://github.com/Trusted-AI/adversarial-robustness-toolbox) | Adversarial robustness |
| [Fairlearn](https://github.com/fairlearn/fairlearn) | Fairness assessment |
| [AIF360](https://github.com/Trusted-AI/AIF360) | AI fairness toolkit |
| [SHAP](https://github.com/shap/shap) | Model explanations |
| [LIME](https://github.com/marcotcr/lime) | Local explanations |
| [Captum](https://github.com/pytorch/captum) | PyTorch interpretability |
| [Presidio](https://github.com/microsoft/presidio) | PII detection |
| [Detoxify](https://github.com/unitaryai/detoxify) | Toxicity detection |
| [NeMo Guardrails](https://github.com/NVIDIA/NeMo-Guardrails) | Runtime guardrails |
| [Argo Workflows](https://github.com/argoproj/argo-workflows) | Workflow orchestration |
| [LiteLLM](https://github.com/BerriAI/litellm) | LLM abstraction |

---

## 📞 Support

- **Documentation**: [docs.guardstack.io](https://docs.guardstack.io)
- **Issues**: [GitHub Issues](https://github.com/guardstack/guardstack/issues)
- **Discussions**: [GitHub Discussions](https://github.com/guardstack/guardstack/discussions)
- **Discord**: [Join our community](https://discord.gg/guardstack)

---

<p align="center">
  <strong>Built with ❤️ for the AI Safety Community</strong>
</p>
