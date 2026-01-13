"""
Azure OpenAI Connector

Connector for Azure-hosted OpenAI models.
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


class AzureOpenAIConnector(BaseConnector):
    """
    Connector for Azure OpenAI Service.
    
    Supports GPT-4, GPT-3.5-turbo, and embedding models deployed on Azure.
    """
    
    connector_type = ConnectorType.AZURE_OPENAI
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        self._async_client: Optional[Any] = None
        
        # Azure-specific configuration
        self.api_version = config.extra_config.get("api_version", "2024-02-01")
        self.deployment_name = config.extra_config.get("deployment_name", config.model_name)
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision="vision" in self.config.model_name.lower(),
            supports_embeddings="embedding" in self.config.model_name.lower(),
            max_context_length=self._get_context_length(),
            supports_json_mode=True,
        )
    
    def _get_context_length(self) -> int:
        """Get max context length for the model."""
        model = self.config.model_name.lower()
        if "gpt-4-turbo" in model or "gpt-4o" in model:
            return 128000
        elif "gpt-4-32k" in model:
            return 32768
        elif "gpt-4" in model:
            return 8192
        elif "gpt-35-turbo-16k" in model or "gpt-3.5-turbo-16k" in model:
            return 16384
        else:
            return 4096
    
    async def connect(self) -> None:
        """Initialize Azure OpenAI client."""
        try:
            from openai import AsyncAzureOpenAI, AzureOpenAI
            
            self._client = AzureOpenAI(
                api_key=self.config.api_key,
                api_version=self.api_version,
                azure_endpoint=self.config.base_url,
            )
            
            self._async_client = AsyncAzureOpenAI(
                api_key=self.config.api_key,
                api_version=self.api_version,
                azure_endpoint=self.config.base_url,
            )
            
            self._connected = True
            logger.info(f"Connected to Azure OpenAI: {self.deployment_name}")
            
        except ImportError:
            raise ImportError("openai package required. Install with: pip install openai")
        except Exception as e:
            logger.error(f"Failed to connect to Azure OpenAI: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Azure OpenAI client."""
        if self._async_client:
            await self._async_client.close()
        self._client = None
        self._async_client = None
        self._connected = False
        logger.info("Disconnected from Azure OpenAI")
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from Azure OpenAI."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        # Convert messages to OpenAI format
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        kwargs: dict[str, Any] = {
            "model": self.deployment_name,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
        }
        
        if config.stop_sequences:
            kwargs["stop"] = config.stop_sequences
        
        if config.response_format == "json":
            kwargs["response_format"] = {"type": "json_object"}
        
        response = await self._async_client.chat.completions.create(**kwargs)
        
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
        """Stream a response from Azure OpenAI."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        api_messages = [
            {"role": msg.role, "content": msg.content}
            for msg in messages
        ]
        
        kwargs: dict[str, Any] = {
            "model": self.deployment_name,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "stream": True,
        }
        
        async for chunk in await self._async_client.chat.completions.create(**kwargs):
            if chunk.choices and chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings using Azure OpenAI."""
        if not self._connected:
            await self.connect()
        
        embedding_model = model or self.config.extra_config.get(
            "embedding_deployment", "text-embedding-ada-002"
        )
        
        response = await self._async_client.embeddings.create(
            model=embedding_model,
            input=texts,
        )
        
        return [item.embedding for item in response.data]
    
    async def health_check(self) -> bool:
        """Check Azure OpenAI connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # Simple completion test
            await self._async_client.chat.completions.create(
                model=self.deployment_name,
                messages=[{"role": "user", "content": "test"}],
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.error(f"Azure OpenAI health check failed: {e}")
            return False
