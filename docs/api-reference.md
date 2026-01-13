# API Reference

This document provides the complete API reference for GuardStack's REST API.

## Base URL

```
https://guardstack.yourdomain.com/api/v1
```

## Authentication

### API Key Authentication

Include your API key in the request header:

```http
Authorization: Bearer <your-api-key>
```

### OAuth2/OIDC

For OAuth2 authentication, redirect users to:

```
GET /auth/login
```

## Common Response Formats

### Success Response

```json
{
  "data": { ... },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_abc123"
  }
}
```

### Error Response

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": [
      {
        "field": "name",
        "message": "Name is required"
      }
    ]
  },
  "meta": {
    "timestamp": "2024-01-01T00:00:00Z",
    "request_id": "req_abc123"
  }
}
```

## Endpoints

---

## Models

### List Models

```http
GET /models
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `page` | integer | Page number (default: 1) |
| `limit` | integer | Items per page (default: 20, max: 100) |
| `type` | string | Filter by model type (genai, predictive, agentic) |
| `status` | string | Filter by status (active, inactive, archived) |
| `search` | string | Search by name or description |

**Response:**

```json
{
  "data": [
    {
      "id": "model_abc123",
      "name": "GPT-4 Customer Service",
      "type": "genai",
      "provider": "openai",
      "version": "gpt-4-turbo",
      "status": "active",
      "risk_tier": "high",
      "created_at": "2024-01-01T00:00:00Z",
      "updated_at": "2024-01-01T00:00:00Z"
    }
  ],
  "meta": {
    "total": 42,
    "page": 1,
    "limit": 20,
    "pages": 3
  }
}
```

### Create Model

```http
POST /models
```

**Request Body:**

```json
{
  "name": "GPT-4 Customer Service",
  "type": "genai",
  "provider": "openai",
  "version": "gpt-4-turbo",
  "description": "Customer service chatbot",
  "endpoint": "https://api.openai.com/v1/chat/completions",
  "risk_tier": "high",
  "metadata": {
    "department": "customer_success",
    "owner": "john@example.com"
  }
}
```

**Response:** `201 Created`

```json
{
  "data": {
    "id": "model_abc123",
    "name": "GPT-4 Customer Service",
    "type": "genai",
    "status": "active",
    "created_at": "2024-01-01T00:00:00Z"
  }
}
```

### Get Model

```http
GET /models/{model_id}
```

**Response:**

```json
{
  "data": {
    "id": "model_abc123",
    "name": "GPT-4 Customer Service",
    "type": "genai",
    "provider": "openai",
    "version": "gpt-4-turbo",
    "description": "Customer service chatbot",
    "endpoint": "https://api.openai.com/v1/chat/completions",
    "status": "active",
    "risk_tier": "high",
    "metadata": { ... },
    "evaluations": {
      "total": 5,
      "latest": {
        "id": "eval_xyz789",
        "overall_score": 0.85,
        "status": "completed"
      }
    },
    "created_at": "2024-01-01T00:00:00Z",
    "updated_at": "2024-01-01T00:00:00Z"
  }
}
```

### Update Model

```http
PUT /models/{model_id}
```

**Request Body:**

```json
{
  "description": "Updated description",
  "risk_tier": "critical",
  "metadata": { ... }
}
```

**Response:** `200 OK`

### Delete Model

```http
DELETE /models/{model_id}
```

**Response:** `204 No Content`

---

## Evaluations

### List Evaluations

```http
GET /evaluations
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `model_id` | string | Filter by model |
| `status` | string | Filter by status (pending, running, completed, failed) |
| `from` | datetime | Filter by start date |
| `to` | datetime | Filter by end date |

**Response:**

```json
{
  "data": [
    {
      "id": "eval_xyz789",
      "model_id": "model_abc123",
      "model_name": "GPT-4 Customer Service",
      "status": "completed",
      "overall_score": 0.85,
      "pillar_summary": {
        "privacy": 0.92,
        "toxicity": 0.88,
        "fairness": 0.80,
        "security": 0.82
      },
      "started_at": "2024-01-01T10:00:00Z",
      "completed_at": "2024-01-01T10:15:00Z"
    }
  ],
  "meta": { ... }
}
```

### Start Evaluation

```http
POST /evaluations
```

**Request Body:**

```json
{
  "model_id": "model_abc123",
  "config": {
    "pillars": ["privacy", "toxicity", "fairness", "security"],
    "threshold": 0.7,
    "dataset_id": "dataset_abc123",
    "sample_size": 1000
  }
}
```

**Response:** `202 Accepted`

```json
{
  "data": {
    "id": "eval_xyz789",
    "model_id": "model_abc123",
    "status": "pending",
    "message": "Evaluation queued"
  }
}
```

### Get Evaluation

```http
GET /evaluations/{evaluation_id}
```

**Response:**

```json
{
  "data": {
    "id": "eval_xyz789",
    "model_id": "model_abc123",
    "status": "completed",
    "overall_score": 0.85,
    "overall_status": "pass",
    "pillar_results": {
      "privacy": {
        "score": 0.92,
        "status": "pass",
        "metrics": {
          "pii_detection_rate": 0.98,
          "data_leakage_incidents": 0
        },
        "findings": []
      },
      "toxicity": {
        "score": 0.88,
        "status": "pass",
        "metrics": {
          "toxic_content_rate": 0.02,
          "harmful_response_rate": 0.01
        },
        "findings": []
      },
      "fairness": {
        "score": 0.80,
        "status": "warn",
        "metrics": {
          "demographic_parity_difference": 0.08,
          "bias_detected": true
        },
        "findings": [
          {
            "severity": "medium",
            "message": "Slight gender bias detected",
            "recommendation": "Review training data"
          }
        ]
      },
      "security": {
        "score": 0.82,
        "status": "pass",
        "metrics": {
          "injection_resistance": 0.95,
          "jailbreak_resistance": 0.90
        },
        "findings": []
      }
    },
    "config": { ... },
    "started_at": "2024-01-01T10:00:00Z",
    "completed_at": "2024-01-01T10:15:00Z"
  }
}
```

### Cancel Evaluation

```http
POST /evaluations/{evaluation_id}/cancel
```

**Response:** `200 OK`

```json
{
  "data": {
    "id": "eval_xyz789",
    "status": "cancelled"
  }
}
```

### Get Evaluation Report

```http
GET /evaluations/{evaluation_id}/report
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Report format (json, pdf, html) |

**Response:** Report file or JSON

---

## Dashboard

### Get Statistics

```http
GET /dashboard/stats
```

**Response:**

```json
{
  "data": {
    "total_models": 42,
    "active_models": 38,
    "total_evaluations": 156,
    "evaluations_this_month": 23,
    "risk_distribution": {
      "critical": 2,
      "high": 10,
      "medium": 18,
      "low": 12
    },
    "status_distribution": {
      "pass": 28,
      "warn": 8,
      "fail": 2
    },
    "compliance_coverage": {
      "eu_ai_act": 0.75,
      "nist_ai_rmf": 0.82,
      "soc2": 0.90
    },
    "trend": {
      "evaluations": [
        {"date": "2024-01-01", "count": 5},
        {"date": "2024-01-02", "count": 8}
      ],
      "average_score": [
        {"date": "2024-01-01", "score": 0.82},
        {"date": "2024-01-02", "score": 0.85}
      ]
    }
  }
}
```

### Get Recent Activity

```http
GET /dashboard/activity
```

**Response:**

```json
{
  "data": [
    {
      "type": "evaluation_completed",
      "model_id": "model_abc123",
      "model_name": "GPT-4 Customer Service",
      "evaluation_id": "eval_xyz789",
      "score": 0.85,
      "timestamp": "2024-01-01T10:15:00Z"
    }
  ]
}
```

---

## Compliance

### List Frameworks

```http
GET /compliance/frameworks
```

**Response:**

```json
{
  "data": [
    {
      "id": "eu-ai-act",
      "name": "EU AI Act",
      "description": "European Union AI regulation",
      "controls_count": 45,
      "coverage": 0.75
    },
    {
      "id": "nist-ai-rmf",
      "name": "NIST AI RMF",
      "description": "NIST AI Risk Management Framework",
      "controls_count": 72,
      "coverage": 0.82
    }
  ]
}
```

### Get Framework Details

```http
GET /compliance/frameworks/{framework_id}
```

**Response:**

```json
{
  "data": {
    "id": "eu-ai-act",
    "name": "EU AI Act",
    "description": "European Union AI regulation",
    "controls": [
      {
        "id": "article-9",
        "name": "Risk Management System",
        "description": "...",
        "status": "implemented",
        "evidence": [ ... ]
      }
    ],
    "coverage": 0.75,
    "last_assessment": "2024-01-01T00:00:00Z"
  }
}
```

### Get Compliance Report

```http
GET /compliance/report
```

**Query Parameters:**

| Parameter | Type | Description |
|-----------|------|-------------|
| `framework_id` | string | Specific framework |
| `format` | string | Report format |

---

## Guardrails

### List Guardrails

```http
GET /guardrails
```

**Response:**

```json
{
  "data": [
    {
      "id": "gr_abc123",
      "name": "PII Blocker",
      "type": "content_filter",
      "enabled": true,
      "config": {
        "patterns": ["email", "phone", "ssn"],
        "action": "block"
      },
      "stats": {
        "triggered_count": 156,
        "last_triggered": "2024-01-01T10:00:00Z"
      }
    }
  ]
}
```

### Create Guardrail

```http
POST /guardrails
```

**Request Body:**

```json
{
  "name": "Toxicity Filter",
  "type": "content_filter",
  "config": {
    "threshold": 0.7,
    "action": "block",
    "categories": ["harassment", "hate_speech", "violence"]
  },
  "applies_to": ["model_abc123"]
}
```

**Response:** `201 Created`

### Update Guardrail

```http
PUT /guardrails/{guardrail_id}
```

### Toggle Guardrail

```http
POST /guardrails/{guardrail_id}/toggle
```

**Request Body:**

```json
{
  "enabled": false
}
```

### Delete Guardrail

```http
DELETE /guardrails/{guardrail_id}
```

---

## Connectors

### List Connectors

```http
GET /connectors
```

**Response:**

```json
{
  "data": [
    {
      "id": "openai",
      "name": "OpenAI",
      "status": "connected",
      "models_available": 15,
      "last_sync": "2024-01-01T00:00:00Z"
    }
  ]
}
```

### Configure Connector

```http
POST /connectors/{connector_id}/configure
```

**Request Body:**

```json
{
  "api_key": "sk-...",
  "organization_id": "org-..."
}
```

### Test Connector

```http
POST /connectors/{connector_id}/test
```

**Response:**

```json
{
  "data": {
    "status": "healthy",
    "latency_ms": 125,
    "models_count": 15
  }
}
```

---

## WebSocket API

### Evaluation Progress

```
WS /ws/evaluations/{evaluation_id}
```

**Message Format:**

```json
{
  "type": "progress",
  "data": {
    "pillar": "privacy",
    "progress": 75,
    "status": "running"
  }
}
```

### Real-time Alerts

```
WS /ws/alerts
```

**Message Format:**

```json
{
  "type": "alert",
  "data": {
    "severity": "high",
    "message": "Guardrail triggered",
    "model_id": "model_abc123",
    "timestamp": "2024-01-01T10:00:00Z"
  }
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| `VALIDATION_ERROR` | 422 | Invalid request data |
| `NOT_FOUND` | 404 | Resource not found |
| `UNAUTHORIZED` | 401 | Authentication required |
| `FORBIDDEN` | 403 | Permission denied |
| `RATE_LIMITED` | 429 | Too many requests |
| `INTERNAL_ERROR` | 500 | Server error |
| `SERVICE_UNAVAILABLE` | 503 | Service temporarily unavailable |

---

## Rate Limiting

Default rate limits:

| Tier | Requests/minute | Requests/hour |
|------|-----------------|---------------|
| Free | 60 | 1,000 |
| Pro | 300 | 10,000 |
| Enterprise | Unlimited | Unlimited |

Rate limit headers:

```http
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 1704110400
```

---

## SDKs

### Python

```python
from guardstack import GuardStack

client = GuardStack(api_key="your-api-key")

# List models
models = client.models.list()

# Start evaluation
evaluation = client.evaluations.create(
    model_id="model_abc123",
    config={"pillars": ["privacy", "toxicity"]}
)

# Wait for completion
result = client.evaluations.wait(evaluation.id)
print(f"Score: {result.overall_score}")
```

### JavaScript/TypeScript

```typescript
import { GuardStack } from '@guardstack/sdk';

const client = new GuardStack({ apiKey: 'your-api-key' });

// List models
const models = await client.models.list();

// Start evaluation
const evaluation = await client.evaluations.create({
  modelId: 'model_abc123',
  config: { pillars: ['privacy', 'toxicity'] }
});

// Wait for completion
const result = await client.evaluations.wait(evaluation.id);
console.log(`Score: ${result.overallScore}`);
```
