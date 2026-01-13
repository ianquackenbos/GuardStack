"""
Mistral AI Connector

Connector for Mistral AI API.
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


class MistralConnector(BaseConnector):
    """
    Connector for Mistral AI API.
    
    Supports Mistral Large, Medium, Small, and embedding models.
    """
    
    connector_type = ConnectorType.MISTRAL
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        self.model_name = config.model_name or "mistral-large-latest"
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        model = self.model_name.lower()
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling="large" in model or "medium" in model,
            supports_vision=False,  # Pixtral coming soon
            supports_embeddings="embed" in model,
            max_context_length=self._get_context_length(),
            supports_json_mode=True,
        )
    
    def _get_context_length(self) -> int:
        """Get max context length for the model."""
        model = self.model_name.lower()
        if "large" in model:
            return 128000
        elif "medium" in model:
            return 32768
        elif "small" in model:
            return 32768
        elif "codestral" in model:
            return 32768
        else:
            return 8192
    
    async def connect(self) -> None:
        """Initialize Mistral AI client."""
        try:
            from mistralai import Mistral
            
            self._client = Mistral(api_key=self.config.api_key)
            
            self._connected = True
            logger.info(f"Connected to Mistral AI: {self.model_name}")
            
        except ImportError:
            raise ImportError(
                "mistralai package required. Install with: pip install mistralai"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Mistral AI: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Mistral AI client."""
        self._client = None
        self._connected = False
        logger.info("Disconnected from Mistral AI")
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from Mistral AI."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        # Convert messages to Mistral format
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
        
        if config.response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self._client.chat.complete_async(**kwargs)
        
        choice = response.choices[0]
        
        return GenerationResponse(
            content=choice.message.content or "",
            role="assistant",
            finish_reason=choice.finish_reason,
            usage=TokenUsage(
                prompt_tokens=response.usage.prompt_tokens,
                completion_tokens=response.usage.completion_tokens,
                total_tokens=response.usage.total_tokens,
            ) if response.usage else None,
            model=response.model,
            raw_response=response.model_dump() if hasattr(response, "model_dump") else {},
        )
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from Mistral AI."""
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
        }
        
        async for chunk in self._client.chat.stream_async(**kwargs):
            if chunk.data.choices and chunk.data.choices[0].delta.content:
                yield chunk.data.choices[0].delta.content
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings using Mistral AI."""
        if not self._connected:
            await self.connect()
        
        embedding_model = model or self.config.extra_config.get(
            "embedding_model", "mistral-embed"
        )
        
        response = await self._client.embeddings.create_async(
            model=embedding_model,
            inputs=texts,
        )
        
        return [item.embedding for item in response.data]
    
    async def health_check(self) -> bool:
        """Check Mistral AI connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # List models to verify connection
            models = await self._client.models.list_async()
            return len(models.data) > 0
        except Exception as e:
            logger.error(f"Mistral AI health check failed: {e}")
            return False
