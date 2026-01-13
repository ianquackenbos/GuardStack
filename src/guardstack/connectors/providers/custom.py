"""
Custom/Generic Connector

Flexible connector for custom API endpoints.
"""

import logging
from typing import Any, AsyncIterator, Optional

import httpx

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


class CustomConnector(BaseConnector):
    """
    Generic connector for custom API endpoints.
    
    Supports OpenAI-compatible APIs and custom formats.
    Can be configured for various API styles via extra_config.
    """
    
    connector_type = ConnectorType.CUSTOM
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[httpx.AsyncClient] = None
        
        # Custom configuration
        self.api_format = config.extra_config.get("api_format", "openai")  # openai, anthropic, custom
        self.chat_endpoint = config.extra_config.get("chat_endpoint", "/v1/chat/completions")
        self.embed_endpoint = config.extra_config.get("embed_endpoint", "/v1/embeddings")
        self.health_endpoint = config.extra_config.get("health_endpoint", "/health")
        self.request_template = config.extra_config.get("request_template", {})
        self.response_mapping = config.extra_config.get("response_mapping", {})
        self.headers = config.extra_config.get("headers", {})
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_streaming=self.config.extra_config.get("supports_streaming", True),
            supports_function_calling=self.config.extra_config.get("supports_function_calling", False),
            supports_vision=self.config.extra_config.get("supports_vision", False),
            supports_embeddings=self.config.extra_config.get("supports_embeddings", True),
            max_context_length=self.config.extra_config.get("max_context_length", 4096),
            supports_json_mode=self.config.extra_config.get("supports_json_mode", False),
        )
    
    async def connect(self) -> None:
        """Initialize HTTP client."""
        try:
            # Build headers
            request_headers = {
                "Content-Type": "application/json",
                **self.headers,
            }
            
            # Add authorization if provided
            if self.config.api_key:
                auth_header = self.config.extra_config.get("auth_header", "Authorization")
                auth_prefix = self.config.extra_config.get("auth_prefix", "Bearer")
                request_headers[auth_header] = f"{auth_prefix} {self.config.api_key}"
            
            self._client = httpx.AsyncClient(
                base_url=self.config.base_url,
                headers=request_headers,
                timeout=httpx.Timeout(
                    self.config.timeout,
                    read=self.config.extra_config.get("read_timeout", 120.0),
                ),
            )
            
            self._connected = True
            logger.info(f"Connected to custom endpoint: {self.config.base_url}")
            
        except Exception as e:
            logger.error(f"Failed to connect to custom endpoint: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close HTTP client."""
        if self._client:
            await self._client.aclose()
        self._client = None
        self._connected = False
        logger.info("Disconnected from custom endpoint")
    
    def _build_request(
        self,
        messages: list[Message],
        config: GenerationConfig,
    ) -> dict[str, Any]:
        """Build request body based on API format."""
        if self.api_format == "openai":
            return self._build_openai_request(messages, config)
        elif self.api_format == "anthropic":
            return self._build_anthropic_request(messages, config)
        else:
            return self._build_custom_request(messages, config)
    
    def _build_openai_request(
        self,
        messages: list[Message],
        config: GenerationConfig,
    ) -> dict[str, Any]:
        """Build OpenAI-format request."""
        return {
            "model": self.config.model_name,
            "messages": [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ],
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stop": config.stop_sequences or None,
            **self.request_template,
        }
    
    def _build_anthropic_request(
        self,
        messages: list[Message],
        config: GenerationConfig,
    ) -> dict[str, Any]:
        """Build Anthropic-format request."""
        system_message = None
        api_messages = []
        
        for msg in messages:
            if msg.role == "system":
                system_message = msg.content
            else:
                api_messages.append({
                    "role": msg.role,
                    "content": msg.content,
                })
        
        request = {
            "model": self.config.model_name,
            "messages": api_messages,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            **self.request_template,
        }
        
        if system_message:
            request["system"] = system_message
        
        return request
    
    def _build_custom_request(
        self,
        messages: list[Message],
        config: GenerationConfig,
    ) -> dict[str, Any]:
        """Build custom-format request using template."""
        # Start with template
        request = dict(self.request_template)
        
        # Apply message formatting
        message_key = self.config.extra_config.get("message_key", "messages")
        message_format = self.config.extra_config.get("message_format", "list")
        
        if message_format == "list":
            request[message_key] = [
                {"role": msg.role, "content": msg.content}
                for msg in messages
            ]
        elif message_format == "string":
            request[message_key] = "\n".join([
                f"{msg.role}: {msg.content}"
                for msg in messages
            ])
        elif message_format == "last":
            request[message_key] = messages[-1].content if messages else ""
        
        # Apply generation config
        param_mapping = self.config.extra_config.get("param_mapping", {})
        
        max_tokens_key = param_mapping.get("max_tokens", "max_tokens")
        temperature_key = param_mapping.get("temperature", "temperature")
        
        request[max_tokens_key] = config.max_tokens
        request[temperature_key] = config.temperature
        
        return request
    
    def _parse_response(self, response_data: dict[str, Any]) -> GenerationResponse:
        """Parse response based on API format."""
        if self.api_format == "openai":
            return self._parse_openai_response(response_data)
        elif self.api_format == "anthropic":
            return self._parse_anthropic_response(response_data)
        else:
            return self._parse_custom_response(response_data)
    
    def _parse_openai_response(self, data: dict[str, Any]) -> GenerationResponse:
        """Parse OpenAI-format response."""
        choice = data.get("choices", [{}])[0]
        message = choice.get("message", {})
        usage_data = data.get("usage", {})
        
        return GenerationResponse(
            content=message.get("content", ""),
            role="assistant",
            finish_reason=choice.get("finish_reason", "stop"),
            usage=TokenUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ) if usage_data else None,
            model=data.get("model", self.config.model_name),
            raw_response=data,
        )
    
    def _parse_anthropic_response(self, data: dict[str, Any]) -> GenerationResponse:
        """Parse Anthropic-format response."""
        content = data.get("content", [{}])[0].get("text", "")
        usage_data = data.get("usage", {})
        
        return GenerationResponse(
            content=content,
            role="assistant",
            finish_reason=data.get("stop_reason", "end_turn"),
            usage=TokenUsage(
                prompt_tokens=usage_data.get("input_tokens", 0),
                completion_tokens=usage_data.get("output_tokens", 0),
                total_tokens=usage_data.get("input_tokens", 0) + usage_data.get("output_tokens", 0),
            ) if usage_data else None,
            model=data.get("model", self.config.model_name),
            raw_response=data,
        )
    
    def _parse_custom_response(self, data: dict[str, Any]) -> GenerationResponse:
        """Parse custom-format response using mapping."""
        mapping = self.response_mapping
        
        # Extract content
        content_path = mapping.get("content", "response")
        content = self._extract_path(data, content_path)
        
        # Extract optional fields
        usage = None
        if "usage" in mapping:
            usage_path = mapping["usage"]
            usage_data = self._extract_path(data, usage_path)
            if usage_data:
                usage = TokenUsage(
                    prompt_tokens=usage_data.get("prompt_tokens", 0),
                    completion_tokens=usage_data.get("completion_tokens", 0),
                    total_tokens=usage_data.get("total_tokens", 0),
                )
        
        return GenerationResponse(
            content=str(content) if content else "",
            role="assistant",
            finish_reason=self._extract_path(data, mapping.get("finish_reason", "")) or "stop",
            usage=usage,
            model=self.config.model_name,
            raw_response=data,
        )
    
    def _extract_path(self, data: dict[str, Any], path: str) -> Any:
        """Extract value from nested dict using dot-notation path."""
        if not path:
            return None
        
        parts = path.split(".")
        current = data
        
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list) and part.isdigit():
                idx = int(part)
                current = current[idx] if idx < len(current) else None
            else:
                return None
        
        return current
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from custom endpoint."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        request_body = self._build_request(messages, config)
        
        response = await self._client.post(
            self.chat_endpoint,
            json=request_body,
        )
        response.raise_for_status()
        
        return self._parse_response(response.json())
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from custom endpoint."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        request_body = self._build_request(messages, config)
        request_body["stream"] = True
        
        async with self._client.stream(
            "POST",
            self.chat_endpoint,
            json=request_body,
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]
                    if data == "[DONE]":
                        break
                    
                    try:
                        import json
                        chunk = json.loads(data)
                        
                        # Extract content based on format
                        if self.api_format == "openai":
                            content = chunk.get("choices", [{}])[0].get("delta", {}).get("content", "")
                        elif self.api_format == "anthropic":
                            if chunk.get("type") == "content_block_delta":
                                content = chunk.get("delta", {}).get("text", "")
                            else:
                                content = ""
                        else:
                            stream_content_path = self.config.extra_config.get("stream_content_path", "content")
                            content = self._extract_path(chunk, stream_content_path) or ""
                        
                        if content:
                            yield content
                    except Exception:
                        continue
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings from custom endpoint."""
        if not self._connected:
            await self.connect()
        
        embedding_model = model or self.config.extra_config.get(
            "embedding_model", self.config.model_name
        )
        
        # Build embedding request
        if self.api_format in ["openai", "custom"]:
            request_body = {
                "model": embedding_model,
                "input": texts,
            }
        else:
            request_body = {
                "model": embedding_model,
                "texts": texts,
            }
        
        response = await self._client.post(
            self.embed_endpoint,
            json=request_body,
        )
        response.raise_for_status()
        
        data = response.json()
        
        # Extract embeddings
        embedding_path = self.config.extra_config.get("embedding_path", "data")
        embeddings_data = self._extract_path(data, embedding_path)
        
        if isinstance(embeddings_data, list):
            if embeddings_data and isinstance(embeddings_data[0], dict):
                return [item.get("embedding", []) for item in embeddings_data]
            return embeddings_data
        
        return []
    
    async def health_check(self) -> bool:
        """Check custom endpoint connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            response = await self._client.get(self.health_endpoint)
            return response.status_code in [200, 204]
        except Exception as e:
            logger.error(f"Custom endpoint health check failed: {e}")
            return False
