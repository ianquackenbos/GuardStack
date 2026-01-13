"""
Anthropic Connector

Connector for Anthropic Claude models.
"""

import time
from typing import Any, AsyncIterator

from guardstack.connectors.base import LLMConnector, ModelInfo, ModelResponse, ModelSession
from guardstack.connectors.registry import ConnectorRegistry


@ConnectorRegistry.register("anthropic")
class AnthropicConnector(LLMConnector):
    """
    Connector for Anthropic Claude models.
    """
    
    connector_type = "anthropic"
    supported_model_types = ["genai"]
    
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.api_key = config["api_key"]
        self.base_url = config.get("base_url")
        self._client = None
    
    @classmethod
    def get_required_config_fields(cls) -> list[str]:
        return ["api_key"]
    
    @classmethod
    def get_optional_config_fields(cls) -> list[str]:
        return ["base_url"]
    
    async def _get_client(self) -> Any:
        """Get or create the Anthropic client."""
        if self._client is None:
            try:
                from anthropic import AsyncAnthropic
                
                kwargs = {"api_key": self.api_key}
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                
                self._client = AsyncAnthropic(**kwargs)
            except ImportError:
                pass
        return self._client
    
    async def list_models(self) -> list[ModelInfo]:
        """List available Anthropic models."""
        return [
            ModelInfo(
                id="claude-3-5-sonnet-20241022",
                name="Claude 3.5 Sonnet",
                provider="anthropic",
                model_type="genai",
                context_window=200000,
                max_output_tokens=8192,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="claude-3-opus-20240229",
                name="Claude 3 Opus",
                provider="anthropic",
                model_type="genai",
                context_window=200000,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="claude-3-sonnet-20240229",
                name="Claude 3 Sonnet",
                provider="anthropic",
                model_type="genai",
                context_window=200000,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="claude-3-haiku-20240307",
                name="Claude 3 Haiku",
                provider="anthropic",
                model_type="genai",
                context_window=200000,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
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
        """Send a single prompt to the model."""
        messages = [{"role": "user", "content": prompt}]
        return await self.chat(session, messages, **kwargs)
    
    async def chat(
        self,
        session: ModelSession,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ModelResponse:
        """Send a chat conversation to Claude."""
        start_time = time.time()
        
        # Extract system message if present
        system = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)
        
        try:
            client = await self._get_client()
            if client:
                create_kwargs = {
                    "model": session.model_id,
                    "messages": chat_messages,
                    "max_tokens": kwargs.get("max_tokens", 4096),
                }
                if system:
                    create_kwargs["system"] = system
                if "temperature" in kwargs:
                    create_kwargs["temperature"] = kwargs["temperature"]
                
                response = await client.messages.create(**create_kwargs)
                
                latency = int((time.time() - start_time) * 1000)
                
                content = ""
                for block in response.content:
                    if hasattr(block, "text"):
                        content += block.text
                
                # Update session stats
                session.total_input_tokens += response.usage.input_tokens
                session.total_output_tokens += response.usage.output_tokens
                session.total_requests += 1
                
                return ModelResponse(
                    content=content,
                    model_id=response.model,
                    input_tokens=response.usage.input_tokens,
                    output_tokens=response.usage.output_tokens,
                    total_tokens=response.usage.input_tokens + response.usage.output_tokens,
                    latency_ms=latency,
                    finish_reason=response.stop_reason,
                )
        except ImportError:
            pass
        
        # Fall back to LiteLLM
        import litellm
        
        response = await litellm.acompletion(
            model=f"anthropic/{session.model_id}",
            messages=messages,
            api_key=self.api_key,
            **kwargs,
        )
        
        latency = int((time.time() - start_time) * 1000)
        
        return ModelResponse(
            content=response.choices[0].message.content or "",
            model_id=response.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            latency_ms=latency,
            finish_reason=response.choices[0].finish_reason,
        )
    
    async def chat_with_functions(
        self,
        session: ModelSession,
        messages: list[dict[str, str]],
        functions: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ModelResponse:
        """Chat with tool use (Anthropic's function calling)."""
        start_time = time.time()
        
        client = await self._get_client()
        if not client:
            raise RuntimeError("Anthropic client not available")
        
        # Convert functions to Anthropic tool format
        tools = []
        for func in functions:
            tools.append({
                "name": func["name"],
                "description": func.get("description", ""),
                "input_schema": func.get("parameters", {}),
            })
        
        # Extract system message
        system = None
        chat_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system = msg["content"]
            else:
                chat_messages.append(msg)
        
        create_kwargs = {
            "model": session.model_id,
            "messages": chat_messages,
            "tools": tools,
            "max_tokens": kwargs.get("max_tokens", 4096),
        }
        if system:
            create_kwargs["system"] = system
        
        response = await client.messages.create(**create_kwargs)
        
        latency = int((time.time() - start_time) * 1000)
        
        content = ""
        tool_calls = []
        for block in response.content:
            if hasattr(block, "text"):
                content += block.text
            elif hasattr(block, "name"):
                # Tool use block
                tool_calls.append({
                    "id": block.id,
                    "type": "function",
                    "function": {
                        "name": block.name,
                        "arguments": block.input,
                    }
                })
        
        return ModelResponse(
            content=content,
            model_id=response.model,
            input_tokens=response.usage.input_tokens,
            output_tokens=response.usage.output_tokens,
            total_tokens=response.usage.input_tokens + response.usage.output_tokens,
            latency_ms=latency,
            finish_reason=response.stop_reason,
            tool_calls=tool_calls if tool_calls else None,
        )
    
    async def invoke_stream(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response from Claude."""
        client = await self._get_client()
        if not client:
            response = await self.invoke(session, prompt, **kwargs)
            yield response.content
            return
        
        async with client.messages.stream(
            model=session.model_id,
            messages=[{"role": "user", "content": prompt}],
            max_tokens=kwargs.get("max_tokens", 4096),
        ) as stream:
            async for text in stream.text_stream:
                yield text
    
    async def close(self) -> None:
        """Close the Anthropic client."""
        if self._client:
            await self._client.close()
            self._client = None
