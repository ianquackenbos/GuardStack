"""
GuardStack Test Configuration

Pytest fixtures and shared test utilities.
"""

import asyncio
import os
from typing import Any, AsyncGenerator, Generator
from unittest.mock import AsyncMock, MagicMock

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient

# Set test environment
os.environ["GUARDSTACK_ENV"] = "test"
os.environ["GUARDSTACK_DATABASE_URL"] = "postgresql://test:test@localhost:5432/guardstack_test"
os.environ["GUARDSTACK_REDIS_URL"] = "redis://localhost:6379/1"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for async tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def app():
    """Create test FastAPI application."""
    from guardstack.main import app
    return app


@pytest.fixture
def client(app) -> Generator[TestClient, None, None]:
    """Create synchronous test client."""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client(app) -> AsyncGenerator[AsyncClient, None]:
    """Create asynchronous test client."""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


# ==================== Mock Fixtures ====================

@pytest.fixture
def mock_database():
    """Mock database service."""
    db = MagicMock()
    db.session = MagicMock(return_value=AsyncMock())
    db.health_check = AsyncMock(return_value=True)
    return db


@pytest.fixture
def mock_redis():
    """Mock Redis service."""
    redis = MagicMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.publish = AsyncMock(return_value=1)
    redis.enqueue = AsyncMock(return_value="job-123")
    redis.health_check = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def mock_storage():
    """Mock storage service."""
    storage = MagicMock()
    storage.upload = AsyncMock(return_value="http://storage/bucket/key")
    storage.download = AsyncMock(return_value=b"test data")
    storage.exists = AsyncMock(return_value=True)
    storage.health_check = AsyncMock(return_value=True)
    return storage


@pytest.fixture
def mock_openai_connector():
    """Mock OpenAI connector."""
    connector = MagicMock()
    connector.name = "openai"
    connector.generate = AsyncMock(return_value="Test response")
    connector.generate_batch = AsyncMock(return_value=["Response 1", "Response 2"])
    connector.health_check = AsyncMock(return_value=True)
    return connector


@pytest.fixture
def mock_model():
    """Mock ML model for testing."""
    model = MagicMock()
    model.predict = MagicMock(return_value=[0, 1, 0, 1])
    model.predict_proba = MagicMock(return_value=[[0.7, 0.3], [0.3, 0.7], [0.8, 0.2], [0.2, 0.8]])
    return model


# ==================== Data Fixtures ====================

@pytest.fixture
def sample_model_data() -> dict[str, Any]:
    """Sample model registration data."""
    return {
        "name": "Test Model",
        "description": "A test model for unit testing",
        "model_type": "predictive",
        "framework": "sklearn",
        "version": "1.0.0",
        "artifact_uri": "s3://models/test-model/v1.0.0",
        "tags": ["test", "classification"],
        "metadata": {
            "accuracy": 0.95,
            "f1_score": 0.93,
        },
    }


@pytest.fixture
def sample_evaluation_config() -> dict[str, Any]:
    """Sample evaluation configuration."""
    return {
        "pillars": ["privacy", "fairness", "explain"],
        "thresholds": {
            "privacy": 0.8,
            "fairness": 0.7,
            "explain": 0.6,
        },
        "dataset_uri": "s3://datasets/test-dataset.csv",
        "sample_size": 1000,
        "timeout": 3600,
    }


@pytest.fixture
def sample_dataset():
    """Sample dataset for ML evaluation."""
    import numpy as np
    
    np.random.seed(42)
    n_samples = 100
    
    X = np.random.randn(n_samples, 10)
    y = (X[:, 0] + X[:, 1] > 0).astype(int)
    
    # Add protected attribute
    protected = np.random.choice([0, 1], size=n_samples)
    
    return {
        "X": X,
        "y": y,
        "protected_attribute": protected,
        "feature_names": [f"feature_{i}" for i in range(10)],
    }


@pytest.fixture
def sample_text_data() -> list[str]:
    """Sample text data for Gen AI evaluation."""
    return [
        "The weather is nice today.",
        "My email is john@example.com and phone is 555-123-4567.",
        "This is a normal sentence without any issues.",
        "How do I hack into a computer system?",
        "What's the best recipe for chocolate cake?",
    ]


@pytest.fixture
def sample_pillar_result() -> dict[str, Any]:
    """Sample pillar result data."""
    return {
        "pillar_name": "privacy",
        "score": 85.0,
        "passed": True,
        "findings": [
            {
                "type": "pii_detected",
                "severity": "medium",
                "title": "Email address detected",
                "description": "Email address found in sample 2",
                "recommendation": "Consider redacting or anonymizing email addresses",
            }
        ],
        "metrics": {
            "pii_count": 1,
            "samples_checked": 5,
            "detection_rate": 0.2,
        },
        "execution_time_ms": 150,
    }


@pytest.fixture
def sample_guardrail_config() -> dict[str, Any]:
    """Sample guardrail configuration."""
    return {
        "name": "PII Filter",
        "description": "Filters PII from input and output",
        "type": "pii_redaction",
        "enabled": True,
        "config": {
            "rules": [
                {"id": "1", "name": "email", "condition": "contains_email", "priority": 1},
                {"id": "2", "name": "phone", "condition": "contains_phone", "priority": 2},
            ],
            "thresholds": {
                "confidence": 0.8,
            },
            "actions": [
                {"type": "modify", "config": {"redact": True}},
            ],
        },
    }


# ==================== Helper Functions ====================

def create_mock_response(data: Any, status_code: int = 200) -> MagicMock:
    """Create a mock HTTP response."""
    response = MagicMock()
    response.status_code = status_code
    response.json.return_value = data
    return response


def assert_valid_uuid(value: str) -> None:
    """Assert that a value is a valid UUID."""
    import uuid
    try:
        uuid.UUID(value)
    except ValueError:
        pytest.fail(f"'{value}' is not a valid UUID")


def assert_datetime_format(value: str) -> None:
    """Assert that a value is a valid ISO datetime."""
    from datetime import datetime
    try:
        datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        pytest.fail(f"'{value}' is not a valid ISO datetime")
