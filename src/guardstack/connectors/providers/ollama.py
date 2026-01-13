"""
Ollama Connector

Connector for locally running Ollama instances.
"""

import time
from typing import Any, AsyncIterator

import httpx

from guardstack.connectors.base import LLMConnector, ModelInfo, ModelResponse, ModelSession
from guardstack.connectors.registry import ConnectorRegistry


@ConnectorRegistry.register("ollama")
class OllamaConnector(LLMConnector):
    """
    Connector for Ollama local inference.
    
    Ollama provides a simple way to run LLMs locally.
    """
    
    connector_type = "ollama"
    supported_model_types = ["genai"]
    
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.endpoint = config["endpoint"].rstrip("/")
        self.timeout = config.get("timeout", 120)
        self._client = None
    
    @classmethod
    def get_required_config_fields(cls) -> list[str]:
        return ["endpoint"]
    
    @classmethod
    def get_optional_config_fields(cls) -> list[str]:
        return ["timeout"]
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                base_url=self.endpoint,
                timeout=self.timeout,
            )
        return self._client
    
    async def list_models(self) -> list[ModelInfo]:
        """List models available in the Ollama instance."""
        client = await self._get_client()
        
        try:
            response = await client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            
            models = []
            for model in data.get("models", []):
                models.append(ModelInfo(
                    id=model["name"],
                    name=model["name"],
                    provider="ollama",
                    model_type="genai",
                    context_window=model.get("details", {}).get("context_length"),
                    supports_streaming=True,
                    supports_functions=False,  # Ollama doesn't support function calling yet
                    metadata={
                        "size": model.get("size"),
                        "modified_at": model.get("modified_at"),
                        "digest": model.get("digest"),
                    }
                ))
            
            return models
        except httpx.HTTPError as e:
            raise ConnectionError(f"Failed to connect to Ollama: {e}")
    
    async def create_session(self, model_id: str) -> ModelSession:
        """Create a session for the specified model."""
        return ModelSession(
            model_id=model_id,
            connector_type=self.connector_type,
            config={"endpoint": self.endpoint, "model": model_id},
        )
    
    async def invoke(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> ModelResponse:
        """Send a prompt to Ollama."""
        start_time = time.time()
        
        client = await self._get_client()
        
        payload = {
            "model": session.model_id,
            "prompt": prompt,
            "stream": False,
        }
        
        if "temperature" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = kwargs["temperature"]
        
        if "system" in kwargs:
            payload["system"] = kwargs["system"]
        
        response = await client.post("/api/generate", json=payload)
        response.raise_for_status()
        data = response.json()
        
        latency = int((time.time() - start_time) * 1000)
        
        # Update session stats
        session.total_requests += 1
        if "prompt_eval_count" in data:
            session.total_input_tokens += data["prompt_eval_count"]
        if "eval_count" in data:
            session.total_output_tokens += data["eval_count"]
        
        return ModelResponse(
            content=data.get("response", ""),
            model_id=session.model_id,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            latency_ms=latency,
            finish_reason="stop" if data.get("done") else None,
            raw_response=data,
        )
    
    async def chat(
        self,
        session: ModelSession,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ModelResponse:
        """Send a chat conversation to Ollama."""
        start_time = time.time()
        
        client = await self._get_client()
        
        payload = {
            "model": session.model_id,
            "messages": messages,
            "stream": False,
        }
        
        if "temperature" in kwargs:
            payload["options"] = payload.get("options", {})
            payload["options"]["temperature"] = kwargs["temperature"]
        
        response = await client.post("/api/chat", json=payload)
        response.raise_for_status()
        data = response.json()
        
        latency = int((time.time() - start_time) * 1000)
        
        message = data.get("message", {})
        
        return ModelResponse(
            content=message.get("content", ""),
            model_id=session.model_id,
            input_tokens=data.get("prompt_eval_count", 0),
            output_tokens=data.get("eval_count", 0),
            total_tokens=data.get("prompt_eval_count", 0) + data.get("eval_count", 0),
            latency_ms=latency,
            finish_reason="stop" if data.get("done") else None,
            raw_response=data,
        )
    
    async def invoke_stream(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response from Ollama."""
        client = await self._get_client()
        
        payload = {
            "model": session.model_id,
            "prompt": prompt,
            "stream": True,
        }
        
        async with client.stream("POST", "/api/generate", json=payload) as response:
            async for line in response.aiter_lines():
                if line:
                    import json
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
    
    async def embed(
        self,
        session: ModelSession,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings using Ollama."""
        client = await self._get_client()
        
        model = kwargs.get("embedding_model", session.model_id)
        embeddings = []
        
        for text in texts:
            response = await client.post(
                "/api/embeddings",
                json={"model": model, "prompt": text}
            )
            response.raise_for_status()
            data = response.json()
            embeddings.append(data["embedding"])
        
        return embeddings
    
    async def pull_model(self, model_name: str) -> dict[str, Any]:
        """Pull a model from the Ollama library."""
        client = await self._get_client()
        
        response = await client.post(
            "/api/pull",
            json={"name": model_name},
            timeout=600,  # Model pulls can take a long time
        )
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> dict[str, Any]:
        """Check Ollama connectivity."""
        import time
        
        try:
            client = await self._get_client()
            start = time.time()
            response = await client.get("/api/tags")
            response.raise_for_status()
            latency = int((time.time() - start) * 1000)
            
            data = response.json()
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "model_count": len(data.get("models", [])),
                "endpoint": self.endpoint,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
                "endpoint": self.endpoint,
            }
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
