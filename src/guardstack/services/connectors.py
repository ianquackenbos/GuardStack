"""
Connector Service

Service for testing and interacting with model provider connectors.
"""

import asyncio
import logging
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Optional

import httpx

logger = logging.getLogger(__name__)


@dataclass
class ConnectorTestResult:
    """Result of testing a connector."""
    success: bool
    message: str
    latency_ms: Optional[int]
    available_models: list[str]
    error: Optional[str] = None


@dataclass
class ConnectorHealthStatus:
    """Health status of a connector."""
    type: str
    status: str  # healthy, degraded, unhealthy
    latency_ms: Optional[int]
    last_checked: str
    message: Optional[str] = None


class BaseConnector(ABC):
    """Base class for model connectors."""
    
    def __init__(self, config: dict[str, Any]):
        self.config = config
    
    @abstractmethod
    async def test_connection(self) -> ConnectorTestResult:
        """Test the connection to the provider."""
        pass
    
    @abstractmethod
    async def list_models(self) -> list[dict[str, Any]]:
        """List available models from the provider."""
        pass
    
    @abstractmethod
    async def health_check(self) -> ConnectorHealthStatus:
        """Check health of the connector."""
        pass


class OpenAIConnector(BaseConnector):
    """Connector for OpenAI API."""
    
    async def test_connection(self) -> ConnectorTestResult:
        api_key = self.config.get("api_key")
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        
        if not api_key:
            return ConnectorTestResult(
                success=False,
                message="Missing API key",
                latency_ms=None,
                available_models=[],
                error="api_key is required",
            )
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    f"{base_url}/models",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    models = [m["id"] for m in data.get("data", []) 
                             if "gpt" in m["id"].lower() or "text" in m["id"].lower()]
                    return ConnectorTestResult(
                        success=True,
                        message="Connection successful",
                        latency_ms=latency_ms,
                        available_models=models[:10],  # Limit to 10
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid API key",
                        latency_ms=latency_ms,
                        available_models=[],
                        error="Authentication failed",
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"API error: {response.status_code}",
                        latency_ms=latency_ms,
                        available_models=[],
                        error=response.text,
                    )
        except httpx.TimeoutException:
            return ConnectorTestResult(
                success=False,
                message="Connection timeout",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error="Request timed out",
            )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message="Connection failed",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error=str(e),
            )
    
    async def list_models(self) -> list[dict[str, Any]]:
        api_key = self.config.get("api_key")
        base_url = self.config.get("base_url", "https://api.openai.com/v1")
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.get(
                f"{base_url}/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            
            if response.status_code == 200:
                data = response.json()
                models = []
                for m in data.get("data", []):
                    if "gpt" in m["id"].lower():
                        models.append({
                            "id": m["id"],
                            "name": m["id"].replace("-", " ").title(),
                            "context_window": self._get_context_window(m["id"]),
                            "created": m.get("created"),
                        })
                return models
            return []
    
    def _get_context_window(self, model_id: str) -> int:
        """Get context window size for a model."""
        if "gpt-4-turbo" in model_id or "gpt-4o" in model_id:
            return 128000
        elif "gpt-4-32k" in model_id:
            return 32768
        elif "gpt-4" in model_id:
            return 8192
        elif "gpt-3.5-turbo-16k" in model_id:
            return 16385
        elif "gpt-3.5" in model_id:
            return 4096
        return 4096
    
    async def health_check(self) -> ConnectorHealthStatus:
        from datetime import datetime
        result = await self.test_connection()
        
        status = "healthy" if result.success else "unhealthy"
        if result.success and result.latency_ms and result.latency_ms > 2000:
            status = "degraded"
        
        return ConnectorHealthStatus(
            type="openai",
            status=status,
            latency_ms=result.latency_ms,
            last_checked=datetime.utcnow().isoformat() + "Z",
            message=result.message if not result.success else None,
        )


class AnthropicConnector(BaseConnector):
    """Connector for Anthropic API."""
    
    async def test_connection(self) -> ConnectorTestResult:
        api_key = self.config.get("api_key")
        base_url = self.config.get("base_url", "https://api.anthropic.com")
        
        if not api_key:
            return ConnectorTestResult(
                success=False,
                message="Missing API key",
                latency_ms=None,
                available_models=[],
                error="api_key is required",
            )
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                # Anthropic doesn't have a /models endpoint, so we test with a minimal completion
                response = await client.post(
                    f"{base_url}/v1/messages",
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-3-haiku-20240307",
                        "max_tokens": 1,
                        "messages": [{"role": "user", "content": "hi"}],
                    },
                )
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code in [200, 201]:
                    return ConnectorTestResult(
                        success=True,
                        message="Connection successful",
                        latency_ms=latency_ms,
                        available_models=[
                            "claude-3-opus-20240229",
                            "claude-3-sonnet-20240229",
                            "claude-3-haiku-20240307",
                            "claude-3-5-sonnet-20241022",
                        ],
                    )
                elif response.status_code == 401:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid API key",
                        latency_ms=latency_ms,
                        available_models=[],
                        error="Authentication failed",
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"API error: {response.status_code}",
                        latency_ms=latency_ms,
                        available_models=[],
                        error=response.text,
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message="Connection failed",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error=str(e),
            )
    
    async def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "claude-3-opus-20240229", "name": "Claude 3 Opus", "context_window": 200000},
            {"id": "claude-3-sonnet-20240229", "name": "Claude 3 Sonnet", "context_window": 200000},
            {"id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku", "context_window": 200000},
            {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet", "context_window": 200000},
        ]
    
    async def health_check(self) -> ConnectorHealthStatus:
        from datetime import datetime
        result = await self.test_connection()
        
        status = "healthy" if result.success else "unhealthy"
        if result.success and result.latency_ms and result.latency_ms > 2000:
            status = "degraded"
        
        return ConnectorHealthStatus(
            type="anthropic",
            status=status,
            latency_ms=result.latency_ms,
            last_checked=datetime.utcnow().isoformat() + "Z",
            message=result.message if not result.success else None,
        )


class OllamaConnector(BaseConnector):
    """Connector for local Ollama instance."""
    
    async def test_connection(self) -> ConnectorTestResult:
        endpoint = self.config.get("endpoint", "http://localhost:11434")
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(f"{endpoint}/api/tags")
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    data = response.json()
                    models = [m["name"] for m in data.get("models", [])]
                    return ConnectorTestResult(
                        success=True,
                        message="Connection successful",
                        latency_ms=latency_ms,
                        available_models=models,
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"API error: {response.status_code}",
                        latency_ms=latency_ms,
                        available_models=[],
                        error=response.text,
                    )
        except httpx.ConnectError:
            return ConnectorTestResult(
                success=False,
                message="Cannot connect to Ollama",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error="Ollama server is not running or not accessible",
            )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message="Connection failed",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error=str(e),
            )
    
    async def list_models(self) -> list[dict[str, Any]]:
        endpoint = self.config.get("endpoint", "http://localhost:11434")
        
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{endpoint}/api/tags")
            
            if response.status_code == 200:
                data = response.json()
                return [
                    {
                        "id": m["name"],
                        "name": m["name"].split(":")[0].title(),
                        "context_window": 4096,  # Default for most Ollama models
                        "size": m.get("size"),
                        "modified": m.get("modified_at"),
                    }
                    for m in data.get("models", [])
                ]
            return []
    
    async def health_check(self) -> ConnectorHealthStatus:
        from datetime import datetime
        result = await self.test_connection()
        
        status = "healthy" if result.success else "unhealthy"
        
        return ConnectorHealthStatus(
            type="ollama",
            status=status,
            latency_ms=result.latency_ms,
            last_checked=datetime.utcnow().isoformat() + "Z",
            message=result.message if not result.success else None,
        )


class HuggingFaceConnector(BaseConnector):
    """Connector for Hugging Face Inference API."""
    
    async def test_connection(self) -> ConnectorTestResult:
        api_key = self.config.get("api_key")
        
        if not api_key:
            return ConnectorTestResult(
                success=False,
                message="Missing API key",
                latency_ms=None,
                available_models=[],
                error="api_key is required",
            )
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(
                    "https://huggingface.co/api/whoami",
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code == 200:
                    return ConnectorTestResult(
                        success=True,
                        message="Connection successful",
                        latency_ms=latency_ms,
                        available_models=[
                            "meta-llama/Llama-2-7b-chat-hf",
                            "mistralai/Mistral-7B-Instruct-v0.2",
                            "google/flan-t5-xxl",
                        ],
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message="Invalid API key",
                        latency_ms=latency_ms,
                        available_models=[],
                        error="Authentication failed",
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message="Connection failed",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error=str(e),
            )
    
    async def list_models(self) -> list[dict[str, Any]]:
        return [
            {"id": "meta-llama/Llama-2-7b-chat-hf", "name": "Llama 2 7B Chat", "context_window": 4096},
            {"id": "meta-llama/Llama-2-13b-chat-hf", "name": "Llama 2 13B Chat", "context_window": 4096},
            {"id": "mistralai/Mistral-7B-Instruct-v0.2", "name": "Mistral 7B Instruct", "context_window": 8192},
            {"id": "google/flan-t5-xxl", "name": "Flan T5 XXL", "context_window": 2048},
        ]
    
    async def health_check(self) -> ConnectorHealthStatus:
        from datetime import datetime
        result = await self.test_connection()
        
        status = "healthy" if result.success else "unhealthy"
        
        return ConnectorHealthStatus(
            type="huggingface",
            status=status,
            latency_ms=result.latency_ms,
            last_checked=datetime.utcnow().isoformat() + "Z",
            message=result.message if not result.success else None,
        )


class CustomConnector(BaseConnector):
    """Generic connector for custom REST APIs."""
    
    async def test_connection(self) -> ConnectorTestResult:
        endpoint = self.config.get("endpoint")
        headers = self.config.get("headers", {})
        api_key = self.config.get("api_key")
        
        if not endpoint:
            return ConnectorTestResult(
                success=False,
                message="Missing endpoint",
                latency_ms=None,
                available_models=[],
                error="endpoint is required",
            )
        
        if api_key:
            headers["Authorization"] = f"Bearer {api_key}"
        
        start_time = time.time()
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(endpoint, headers=headers)
                latency_ms = int((time.time() - start_time) * 1000)
                
                if response.status_code < 400:
                    return ConnectorTestResult(
                        success=True,
                        message="Connection successful",
                        latency_ms=latency_ms,
                        available_models=["custom-model"],
                    )
                else:
                    return ConnectorTestResult(
                        success=False,
                        message=f"API error: {response.status_code}",
                        latency_ms=latency_ms,
                        available_models=[],
                        error=response.text[:500],
                    )
        except Exception as e:
            return ConnectorTestResult(
                success=False,
                message="Connection failed",
                latency_ms=int((time.time() - start_time) * 1000),
                available_models=[],
                error=str(e),
            )
    
    async def list_models(self) -> list[dict[str, Any]]:
        return [{"id": "custom-model", "name": "Custom Model", "context_window": 4096}]
    
    async def health_check(self) -> ConnectorHealthStatus:
        from datetime import datetime
        result = await self.test_connection()
        
        return ConnectorHealthStatus(
            type="custom",
            status="healthy" if result.success else "unhealthy",
            latency_ms=result.latency_ms,
            last_checked=datetime.utcnow().isoformat() + "Z",
            message=result.message if not result.success else None,
        )


# Connector registry
CONNECTOR_CLASSES: dict[str, type[BaseConnector]] = {
    "openai": OpenAIConnector,
    "anthropic": AnthropicConnector,
    "ollama": OllamaConnector,
    "huggingface": HuggingFaceConnector,
    "custom": CustomConnector,
}


class ConnectorService:
    """Service for managing model connectors."""
    
    def __init__(self):
        self._configured_connectors: dict[str, dict[str, Any]] = {}
    
    def get_connector(self, connector_type: str, config: dict[str, Any]) -> BaseConnector:
        """Get a connector instance for the given type and config."""
        connector_class = CONNECTOR_CLASSES.get(connector_type)
        if not connector_class:
            # Fall back to custom connector for unknown types
            connector_class = CustomConnector
        return connector_class(config)
    
    async def test_connector(
        self,
        connector_type: str,
        config: dict[str, Any],
    ) -> ConnectorTestResult:
        """Test a connector configuration."""
        connector = self.get_connector(connector_type, config)
        return await connector.test_connection()
    
    async def list_models(
        self,
        connector_type: str,
        config: dict[str, Any],
    ) -> list[dict[str, Any]]:
        """List available models from a connector."""
        connector = self.get_connector(connector_type, config)
        return await connector.list_models()
    
    async def check_health(
        self,
        connector_type: str,
        config: dict[str, Any],
    ) -> ConnectorHealthStatus:
        """Check health of a connector."""
        connector = self.get_connector(connector_type, config)
        return await connector.health_check()
    
    async def check_all_health(
        self,
        connectors: list[tuple[str, dict[str, Any]]],
    ) -> list[ConnectorHealthStatus]:
        """Check health of multiple connectors in parallel."""
        tasks = [
            self.check_health(conn_type, config) 
            for conn_type, config in connectors
        ]
        return await asyncio.gather(*tasks)
    
    def register_connector(
        self,
        name: str,
        connector_type: str,
        config: dict[str, Any],
    ) -> None:
        """Register a configured connector."""
        self._configured_connectors[name] = {
            "type": connector_type,
            "config": config,
        }
    
    def get_configured_connector(self, name: str) -> Optional[BaseConnector]:
        """Get a previously configured connector."""
        if name not in self._configured_connectors:
            return None
        data = self._configured_connectors[name]
        return self.get_connector(data["type"], data["config"])


# Global service instance
_connector_service: Optional[ConnectorService] = None


def get_connector_service() -> ConnectorService:
    """Get the global connector service."""
    global _connector_service
    if _connector_service is None:
        _connector_service = ConnectorService()
    return _connector_service
