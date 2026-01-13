"""
vLLM Connector

Connector for vLLM inference server.
"""

import logging
from typing import Any, AsyncIterator, Optional

from guardstack.connectors.base import (
    BaseConnector,
    ConnectorCapabilities,
    ConnectorConfig,
    ConnectorType,
    GenerationConfig,
    GenerationResponse,
    Message,
    TokenUsage,
)

logger = logging.getLogger(__name__)


class VLLMConnector(BaseConnector):
    """
    Connector for vLLM inference server.
    
    vLLM provides high-throughput LLM serving with PagedAttention.
    Compatible with OpenAI API format.
    """
    
    connector_type = ConnectorType.VLLM
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        
        # vLLM-specific configuration
        self.base_url = config.base_url or "http://localhost:8000/v1"
        self.model_name = config.model_name
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling=False,  # Depends on model
            supports_vision=False,
            supports_embeddings=True,
            max_context_length=self._get_context_length(),
            supports_json_mode=True,
        )
    
    def _get_context_length(self) -> int:
        """Get max context length from config or default."""
        return self.config.extra_config.get("max_context_length", 8192)
    
    async def connect(self) -> None:
        """Initialize vLLM client using OpenAI-compatible API."""
        try:
            from openai import AsyncOpenAI
            
            self._client = AsyncOpenAI(
                api_key=self.config.api_key or "EMPTY",  # vLLM often doesn't need a key
                base_url=self.base_url,
            )
            
            self._connected = True
            logger.info(f"Connected to vLLM: {self.base_url}")
            
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to connect to vLLM: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close vLLM client."""
        if self._client:
            await self._client.close()
        self._client = None
        self._connected = False
        logger.info("Disconnected from vLLM")
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from vLLM."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        # Convert messages to OpenAI format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }
        
        if config.stop_sequences:
            kwargs["stop"] = config.stop_sequences
        
        # vLLM-specific parameters
        extra_body = {}
        if "top_k" in self.config.extra_config:
            extra_body["top_k"] = self.config.extra_config["top_k"]
        if "repetition_penalty" in self.config.extra_config:
            extra_body["repetition_penalty"] = self.config.extra_config["repetition_penalty"]
        if extra_body:
            kwargs["extra_body"] = extra_body
        
        response = await self._client.chat.completions.create(**kwargs)
        
        return GenerationResponse(
            content=response.choices[0].message.content or "",
            role="assistant",
            finish_reason=response.choices[0].finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ) if response.usage else None,
            model=response.model,
            raw_response=response.model_dump(),
        )
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from vLLM."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }
        
        async for chunk in await self._client.chat.completions.create(**kwargs):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings using vLLM embedding endpoint."""
        if not self._connected:
            await self.connect()
        
        embedding_model = model or self.config.extra_config.get(
            "embedding_model", self.model_name
        )
        
        response = await self._client.embeddings.create(
            model=embedding_model,
            input=texts,
        )
        
        return [item.embedding for item in response.data]
    
    async def health_check(self) -> bool:
        """Check vLLM connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # Check models endpoint
            models = await self._client.models.list()
            return len(models.data) > 0
        except Exception as e:
            logger.error(f"vLLM health check failed: {e}")
            return False
    
    async def get_model_info(self) -> dict[str, Any]:
        """Get information about loaded models in vLLM."""
        if not self._connected:
            await self.connect()
        
        models = await self._client.models.list()
        return {
            "models": [
                {
                    "id": m.id,
                    "object": m.object,
                    "created": m.created,
                    "owned_by": m.owned_by,
                }
                for m in models.data
            ]
        }
