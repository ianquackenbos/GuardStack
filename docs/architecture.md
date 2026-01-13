# GuardStack Architecture

This document provides a comprehensive overview of GuardStack's architecture, components, and design decisions.

## System Overview

GuardStack is built as a cloud-native, Kubernetes-first platform designed for scalability, reliability, and security. The architecture follows microservices principles while maintaining operational simplicity.

## High-Level Architecture

```
                                    ┌──────────────────┐
                                    │   Load Balancer  │
                                    └────────┬─────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              │     Rancher UI Extension    │
                              │       (Vue 3 + Pinia)       │
                              └──────────────┬──────────────┘
                                             │
                              ┌──────────────┴──────────────┐
                              │      API Gateway Layer      │
                              │         (FastAPI)           │
                              │                             │
                              │  ┌───────┐ ┌───────┐        │
                              │  │Models │ │Evals  │ ...    │
                              │  │Router │ │Router │        │
                              │  └───────┘ └───────┘        │
                              └──────────────┬──────────────┘
                                             │
        ┌────────────────────────────────────┼────────────────────────────────────┐
        │                                    │                                    │
        ▼                                    ▼                                    ▼
┌───────────────┐                 ┌───────────────────┐                 ┌───────────────┐
│   Gen AI      │                 │   Predictive AI   │                 │   Agentic AI  │
│   Module      │                 │      Module       │                 │    Module     │
│               │                 │                   │                 │               │
│ Privacy       │                 │ Accuracy          │                 │ Interceptor   │
│ Toxicity      │                 │ Fairness          │                 │ Sandbox       │
│ Fairness      │                 │ Robustness        │                 │ Tool Security │
│ Security      │                 │ Explainability    │                 │ Evaluator     │
└───────┬───────┘                 │ Privacy           │                 └───────┬───────┘
        │                         │ Security          │                         │
        │                         │ Reliability       │                         │
        │                         │ Governance        │                         │
        │                         └─────────┬─────────┘                         │
        │                                   │                                   │
        └───────────────────────────────────┼───────────────────────────────────┘
                                            │
                              ┌─────────────┴─────────────┐
                              │      Services Layer       │
                              └─────────────┬─────────────┘
                                            │
            ┌───────────────┬───────────────┼───────────────┬───────────────┐
            │               │               │               │               │
            ▼               ▼               ▼               ▼               ▼
     ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐
     │PostgreSQL│    │  Redis   │    │  MinIO   │    │   Argo   │    │Connectors│
     │+ pgvector│    │  Cache   │    │    S3    │    │Workflows │    │  Layer   │
     └──────────┘    └──────────┘    └──────────┘    └──────────┘    └──────────┘
```

## Component Details

### Frontend Layer

#### Rancher UI Extension
- **Framework**: Vue 3 with Composition API
- **State Management**: Pinia stores
- **Routing**: Vue Router
- **UI Components**: Rancher Shell components
- **Build Tool**: Vite

Key pages:
- Dashboard: Overview statistics and risk distribution
- Models: Model registry and management
- Evaluations: Evaluation execution and results
- Compliance: Regulatory framework tracking
- Guardrails: Real-time protection rules
- Settings: Platform configuration

### API Layer

#### FastAPI Backend
- **Framework**: FastAPI with async support
- **Authentication**: OAuth2/OIDC, API keys
- **Rate Limiting**: Redis-backed limiter
- **Documentation**: OpenAPI/Swagger auto-generated

Routers:
- `/api/v1/models` - Model registry CRUD
- `/api/v1/evaluations` - Evaluation management
- `/api/v1/dashboard` - Statistics and analytics
- `/api/v1/compliance` - Compliance tracking
- `/api/v1/guardrails` - Guardrail management
- `/api/v1/connectors` - Provider integrations

### Evaluation Modules

#### Gen AI Module
Evaluates generative AI models across 4 pillars:

| Pillar | Components | Purpose |
|--------|------------|---------|
| Privacy | PII detector, data leakage analyzer | Protect sensitive information |
| Toxicity | Content classifier, harm detector | Identify harmful outputs |
| Fairness | Bias detector, demographic analyzer | Ensure equitable responses |
| Security | Injection detector, jailbreak scanner | Prevent attacks |

#### Predictive AI Module
Evaluates traditional ML models across 8 pillars:

| Pillar | Metrics | Purpose |
|--------|---------|---------|
| Accuracy | Precision, Recall, F1, AUC | Model performance |
| Fairness | Demographic parity, Equalized odds | Bias mitigation |
| Robustness | Adversarial accuracy, Noise sensitivity | Attack resilience |
| Explainability | SHAP, Feature importance | Model interpretability |
| Privacy | Membership inference, DP compliance | Data protection |
| Security | Extraction resistance, Poisoning detection | Model security |
| Reliability | Calibration, Consistency | Prediction quality |
| Governance | Documentation, Lineage, Compliance | Operational oversight |

#### SPM Module
Security Posture Management capabilities:

- **Inventory**: Discover and track AI systems
- **Scanner**: Continuous security assessment
- **Policies**: Rule-based compliance enforcement
- **Reporting**: Compliance and risk reports

#### Agentic AI Module
Agent safety and monitoring:

- **Interceptor**: Tool call interception and analysis
- **Tool Security**: Permission and rate limit enforcement
- **Sandbox**: Isolated code execution environment
- **Evaluator**: Agent behavior assessment

### Services Layer

#### PostgreSQL + pgvector
- **Purpose**: Primary data store with vector search
- **Features**: ACID compliance, advanced indexing
- **Extensions**: pgvector for embedding similarity

Tables:
- `models` - Model registry
- `evaluations` - Evaluation records
- `pillar_results` - Individual pillar scores
- `compliance_mappings` - Regulatory mappings
- `embeddings` - Vector embeddings for RAG

#### Redis
- **Purpose**: Caching and pub/sub
- **Features**: Session management, rate limiting
- **Usage**: Query cache, real-time updates

#### MinIO/S3
- **Purpose**: Object storage
- **Features**: Model artifacts, evaluation reports
- **Compatibility**: S3 API compatible

#### Argo Workflows
- **Purpose**: Evaluation pipeline orchestration
- **Features**: DAG execution, retry logic
- **Integration**: Kubernetes native

### Connector Layer

Standardized interface for LLM providers:

```python
class BaseConnector(ABC):
    @abstractmethod
    async def chat(self, messages: List[Message]) -> Response:
        pass
    
    @abstractmethod
    async def embed(self, text: str) -> Embedding:
        pass
```

Supported providers:
- OpenAI (GPT-4, GPT-3.5)
- Anthropic (Claude)
- Azure OpenAI
- AWS Bedrock
- HuggingFace
- Ollama (local)
- vLLM (self-hosted)

## Data Flow

### Evaluation Flow

```
1. User initiates evaluation
       │
       ▼
2. API creates evaluation record
       │
       ▼
3. Argo Workflow triggered
       │
       ▼
4. Parallel pillar evaluation
   ┌───┴───┬───────┬───────┐
   │       │       │       │
   ▼       ▼       ▼       ▼
Pillar1 Pillar2 Pillar3 Pillar4
   │       │       │       │
   └───┬───┴───────┴───────┘
       │
       ▼
5. Results aggregation
       │
       ▼
6. Store in PostgreSQL
       │
       ▼
7. Update dashboard via WebSocket
```

### Real-time Guardrail Flow

```
1. Request arrives at interceptor
       │
       ▼
2. Check rate limits (Redis)
       │
       ▼
3. Evaluate guardrail rules
       │
       ▼
4. Content analysis (if needed)
       │
       ▼
5. Approve/Block/Modify
       │
       ▼
6. Log decision (PostgreSQL)
       │
       ▼
7. Return response
```

## Deployment Architecture

### Kubernetes Resources

```yaml
Namespace: guardstack
├── Deployments
│   ├── guardstack-api (3 replicas)
│   └── guardstack-worker (5 replicas)
├── Services
│   ├── guardstack-api (ClusterIP)
│   └── guardstack-headless (Headless)
├── Ingress
│   └── guardstack (HTTPS)
├── ConfigMaps
│   └── guardstack-config
├── Secrets
│   └── guardstack-secrets
├── HPA
│   ├── guardstack-api-hpa
│   └── guardstack-worker-hpa
├── PDB
│   └── guardstack-pdb
└── NetworkPolicy
    └── guardstack-network-policy
```

### Scaling Strategy

| Component | Min | Max | Metric |
|-----------|-----|-----|--------|
| API | 3 | 10 | CPU 70% |
| Worker | 5 | 20 | Queue depth |
| Redis | 3 | 3 | Fixed (cluster) |
| PostgreSQL | 3 | 3 | Fixed (HA) |

## Security Architecture

### Authentication Flow

```
1. User authenticates via OIDC/OAuth2
       │
       ▼
2. JWT token issued
       │
       ▼
3. Token validated on each request
       │
       ▼
4. RBAC policies enforced
       │
       ▼
5. Audit log recorded
```

### Network Security

- **Ingress**: TLS termination, rate limiting
- **NetworkPolicy**: Pod-to-pod restrictions
- **mTLS**: Service mesh encryption (optional)

### Data Security

- **At Rest**: AES-256 encryption
- **In Transit**: TLS 1.3
- **Secrets**: Kubernetes Secrets / HashiCorp Vault

## Performance Considerations

### Caching Strategy

| Cache Level | TTL | Purpose |
|-------------|-----|---------|
| API Response | 5m | Dashboard stats |
| Model Metadata | 1h | Registry queries |
| Evaluation Results | 24h | Historical data |
| Embeddings | ∞ | Similarity search |

### Database Optimization

- Connection pooling via asyncpg
- Read replicas for analytics
- Partitioning for evaluation results
- Indexes on common query patterns

## Observability

### Metrics (Prometheus)

- Request latency histograms
- Evaluation duration gauges
- Error rate counters
- Resource utilization

### Logging (Structured JSON)

- Request/Response logging
- Evaluation step logging
- Error tracking with context

### Tracing (OpenTelemetry)

- Distributed trace propagation
- Span correlation
- Performance profiling

## Future Architecture

### Planned Enhancements

1. **Multi-tenancy**: Namespace isolation
2. **Federation**: Multi-cluster support
3. **ML Pipeline Integration**: MLflow, Kubeflow
4. **Event Streaming**: Kafka for real-time analytics
5. **Graph Database**: Neo4j for lineage tracking
