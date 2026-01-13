"""
LM Studio Connector

Connector for LM Studio local inference server.
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


class LMStudioConnector(BaseConnector):
    """
    Connector for LM Studio local inference.
    
    LM Studio provides a local API server compatible with OpenAI API format.
    """
    
    connector_type = ConnectorType.LMSTUDIO
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        
        # LM Studio-specific configuration
        self.base_url = config.base_url or "http://localhost:1234/v1"
        self.model_name = config.model_name or "local-model"
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling=True,  # LM Studio supports function calling
            supports_vision=self.config.extra_config.get("supports_vision", False),
            supports_embeddings=True,
            max_context_length=self.config.extra_config.get("max_context_length", 4096),
            supports_json_mode=True,
        )
    
    async def connect(self) -> None:
        """Initialize LM Studio client."""
        try:
            from openai import AsyncOpenAI
            
            self._client = AsyncOpenAI(
                api_key="lm-studio",  # LM Studio doesn't require a real key
                base_url=self.base_url,
            )
            
            self._connected = True
            logger.info(f"Connected to LM Studio: {self.base_url}")
            
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to connect to LM Studio: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close LM Studio client."""
        if self._client:
            await self._client.close()
        self._client = None
        self._connected = False
        logger.info("Disconnected from LM Studio")
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from LM Studio."""
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
        
        if config.response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self._client.chat.completions.create(**kwargs)
        
        return GenerationResponse(
            content=response.choices[0].message.content or "",
            role="assistant",
            finish_reason=response.choices[0].finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens if response.usage else 0,
                completion_tokens=response.usage.completion_tokens if response.usage else 0,
                total_tokens=response.usage.total_tokens if response.usage else 0,
            ),
            model=response.model,
            raw_response=response.model_dump(),
        )
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from LM Studio."""
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
        """Generate embeddings using LM Studio."""
        if not self._connected:
            await self.connect()
        
        # LM Studio embedding model (if available)
        embedding_model = model or self.config.extra_config.get(
            "embedding_model", "nomic-embed-text-v1.5"
        )
        
        response = await self._client.embeddings.create(
            model=embedding_model,
            input=texts,
        )
        
        return [item.embedding for item in response.data]
    
    async def health_check(self) -> bool:
        """Check LM Studio connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # Check models endpoint
            models = await self._client.models.list()
            return True
        except Exception as e:
            logger.error(f"LM Studio health check failed: {e}")
            return False
    
    async def get_loaded_model(self) -> Optional[str]:
        """Get the currently loaded model in LM Studio."""
        if not self._connected:
            await self.connect()
        
        try:
            models = await self._client.models.list()
            if models.data:
                return models.data[0].id
            return None
        except Exception:
            return None
