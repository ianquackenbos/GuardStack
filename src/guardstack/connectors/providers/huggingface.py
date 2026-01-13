"""
HuggingFace Connector

Connector for Hugging Face Inference API and Hub models.
"""

import time
from typing import Any, AsyncIterator

import httpx

from guardstack.connectors.base import LLMConnector, ModelInfo, ModelResponse, ModelSession
from guardstack.connectors.registry import ConnectorRegistry


@ConnectorRegistry.register("huggingface")
class HuggingFaceConnector(LLMConnector):
    """
    Connector for Hugging Face models.
    
    Supports both the Inference API and custom inference endpoints.
    """
    
    connector_type = "huggingface"
    supported_model_types = ["genai", "predictive"]
    
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.api_key = config["api_key"]
        self.model_id = config.get("model_id")
        self.endpoint = config.get("endpoint")
        self._client = None
    
    @classmethod
    def get_required_config_fields(cls) -> list[str]:
        return ["api_key"]
    
    @classmethod
    def get_optional_config_fields(cls) -> list[str]:
        return ["model_id", "endpoint"]
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create the HTTP client."""
        if self._client is None:
            self._client = httpx.AsyncClient(
                headers={"Authorization": f"Bearer {self.api_key}"},
                timeout=120,
            )
        return self._client
    
    def _get_inference_url(self, model_id: str) -> str:
        """Get the inference URL for a model."""
        if self.endpoint:
            return self.endpoint
        return f"https://api-inference.huggingface.co/models/{model_id}"
    
    async def list_models(self) -> list[ModelInfo]:
        """List popular models from Hugging Face."""
        # Return some popular models - in production, could query the HF API
        return [
            ModelInfo(
                id="meta-llama/Llama-2-70b-chat-hf",
                name="Llama 2 70B Chat",
                provider="huggingface",
                model_type="genai",
                context_window=4096,
                supports_streaming=False,
                supports_functions=False,
            ),
            ModelInfo(
                id="mistralai/Mistral-7B-Instruct-v0.2",
                name="Mistral 7B Instruct",
                provider="huggingface",
                model_type="genai",
                context_window=8192,
                supports_streaming=False,
                supports_functions=False,
            ),
            ModelInfo(
                id="microsoft/phi-2",
                name="Phi-2",
                provider="huggingface",
                model_type="genai",
                context_window=2048,
                supports_streaming=False,
                supports_functions=False,
            ),
            ModelInfo(
                id="google/gemma-7b-it",
                name="Gemma 7B Instruct",
                provider="huggingface",
                model_type="genai",
                context_window=8192,
                supports_streaming=False,
                supports_functions=False,
            ),
        ]
    
    async def create_session(self, model_id: str) -> ModelSession:
        """Create a session for the specified model."""
        return ModelSession(
            model_id=model_id,
            connector_type=self.connector_type,
            config={"model": model_id},
        )
    
    async def invoke(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> ModelResponse:
        """Send a prompt to the model via Inference API."""
        start_time = time.time()
        
        client = await self._get_client()
        url = self._get_inference_url(session.model_id)
        
        payload = {
            "inputs": prompt,
            "parameters": {
                "max_new_tokens": kwargs.get("max_tokens", 512),
                "temperature": kwargs.get("temperature", 0.7),
                "return_full_text": False,
            }
        }
        
        # Add optional parameters
        if "top_p" in kwargs:
            payload["parameters"]["top_p"] = kwargs["top_p"]
        if "repetition_penalty" in kwargs:
            payload["parameters"]["repetition_penalty"] = kwargs["repetition_penalty"]
        
        response = await client.post(url, json=payload)
        
        # Handle model loading
        if response.status_code == 503:
            data = response.json()
            if "estimated_time" in data:
                # Model is loading, wait and retry
                import asyncio
                wait_time = min(data["estimated_time"], 60)
                await asyncio.sleep(wait_time)
                response = await client.post(url, json=payload)
        
        response.raise_for_status()
        data = response.json()
        
        latency = int((time.time() - start_time) * 1000)
        
        # Handle different response formats
        if isinstance(data, list) and len(data) > 0:
            content = data[0].get("generated_text", "")
        elif isinstance(data, dict):
            content = data.get("generated_text", "")
        else:
            content = str(data)
        
        session.total_requests += 1
        
        return ModelResponse(
            content=content,
            model_id=session.model_id,
            latency_ms=latency,
            raw_response=data,
        )
    
    async def chat(
        self,
        session: ModelSession,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ModelResponse:
        """Send a chat conversation (formatted as prompt)."""
        # Format messages into a prompt
        prompt_parts = []
        for msg in messages:
            role = msg["role"]
            content = msg["content"]
            if role == "system":
                prompt_parts.append(f"System: {content}")
            elif role == "user":
                prompt_parts.append(f"User: {content}")
            elif role == "assistant":
                prompt_parts.append(f"Assistant: {content}")
        
        prompt_parts.append("Assistant:")
        prompt = "\n".join(prompt_parts)
        
        return await self.invoke(session, prompt, **kwargs)
    
    async def embed(
        self,
        session: ModelSession,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings using a HuggingFace embedding model."""
        client = await self._get_client()
        
        model = kwargs.get("embedding_model", "sentence-transformers/all-MiniLM-L6-v2")
        url = f"https://api-inference.huggingface.co/pipeline/feature-extraction/{model}"
        
        response = await client.post(url, json={"inputs": texts})
        response.raise_for_status()
        
        return response.json()
    
    async def health_check(self) -> dict[str, Any]:
        """Check HuggingFace API connectivity."""
        try:
            client = await self._get_client()
            start = time.time()
            
            # Check API status
            response = await client.get("https://huggingface.co/api/health")
            latency = int((time.time() - start) * 1000)
            
            return {
                "status": "healthy" if response.status_code == 200 else "degraded",
                "latency_ms": latency,
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    async def close(self) -> None:
        """Close the HTTP client."""
        if self._client:
            await self._client.aclose()
            self._client = None
