"""
OpenAI Connector

Connector for OpenAI GPT models.
"""

import time
from typing import Any, AsyncIterator

from guardstack.connectors.base import LLMConnector, ModelInfo, ModelResponse, ModelSession
from guardstack.connectors.registry import ConnectorRegistry


@ConnectorRegistry.register("openai")
class OpenAIConnector(LLMConnector):
    """
    Connector for OpenAI models (GPT-4, GPT-3.5, etc.).
    
    Uses the OpenAI Python SDK via LiteLLM for unified interface.
    """
    
    connector_type = "openai"
    supported_model_types = ["genai"]
    
    def __init__(self, config: dict[str, Any]) -> None:
        super().__init__(config)
        self.api_key = config["api_key"]
        self.organization = config.get("organization")
        self.base_url = config.get("base_url")
        self._client = None
    
    @classmethod
    def get_required_config_fields(cls) -> list[str]:
        return ["api_key"]
    
    @classmethod
    def get_optional_config_fields(cls) -> list[str]:
        return ["organization", "base_url"]
    
    async def _get_client(self) -> Any:
        """Get or create the OpenAI client."""
        if self._client is None:
            try:
                from openai import AsyncOpenAI
                
                self._client = AsyncOpenAI(
                    api_key=self.api_key,
                    organization=self.organization,
                    base_url=self.base_url,
                )
            except ImportError:
                # Fall back to LiteLLM
                pass
        return self._client
    
    async def list_models(self) -> list[ModelInfo]:
        """List available OpenAI models."""
        # OpenAI's model list is relatively static, return known models
        models = [
            ModelInfo(
                id="gpt-4-turbo",
                name="GPT-4 Turbo",
                provider="openai",
                model_type="genai",
                context_window=128000,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="gpt-4",
                name="GPT-4",
                provider="openai",
                model_type="genai",
                context_window=8192,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="gpt-4o",
                name="GPT-4o",
                provider="openai",
                model_type="genai",
                context_window=128000,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="gpt-4o-mini",
                name="GPT-4o Mini",
                provider="openai",
                model_type="genai",
                context_window=128000,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
            ModelInfo(
                id="gpt-3.5-turbo",
                name="GPT-3.5 Turbo",
                provider="openai",
                model_type="genai",
                context_window=16385,
                max_output_tokens=4096,
                supports_streaming=True,
                supports_functions=True,
            ),
        ]
        return models
    
    async def create_session(self, model_id: str) -> ModelSession:
        """Create a session for the specified model."""
        return ModelSession(
            model_id=model_id,
            connector_type=self.connector_type,
            config={"api_key": "***", "model": model_id},
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
        """Send a chat conversation to the model."""
        start_time = time.time()
        
        try:
            # Try using native OpenAI client
            client = await self._get_client()
            if client:
                response = await client.chat.completions.create(
                    model=session.model_id,
                    messages=messages,
                    temperature=kwargs.get("temperature", 0.7),
                    max_tokens=kwargs.get("max_tokens"),
                )
                
                latency = int((time.time() - start_time) * 1000)
                
                choice = response.choices[0]
                usage = response.usage
                
                # Update session stats
                session.total_input_tokens += usage.prompt_tokens
                session.total_output_tokens += usage.completion_tokens
                session.total_requests += 1
                
                return ModelResponse(
                    content=choice.message.content or "",
                    model_id=response.model,
                    input_tokens=usage.prompt_tokens,
                    output_tokens=usage.completion_tokens,
                    total_tokens=usage.total_tokens,
                    latency_ms=latency,
                    finish_reason=choice.finish_reason,
                    raw_response=response.model_dump(),
                )
        except ImportError:
            pass
        
        # Fall back to LiteLLM
        import litellm
        
        response = await litellm.acompletion(
            model=f"openai/{session.model_id}",
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
        """Chat with function calling."""
        start_time = time.time()
        
        client = await self._get_client()
        if not client:
            raise RuntimeError("OpenAI client not available")
        
        # Convert functions to tools format
        tools = [
            {"type": "function", "function": func}
            for func in functions
        ]
        
        response = await client.chat.completions.create(
            model=session.model_id,
            messages=messages,
            tools=tools,
            **kwargs,
        )
        
        latency = int((time.time() - start_time) * 1000)
        choice = response.choices[0]
        
        tool_calls = None
        if choice.message.tool_calls:
            tool_calls = [
                {
                    "id": tc.id,
                    "type": tc.type,
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    }
                }
                for tc in choice.message.tool_calls
            ]
        
        return ModelResponse(
            content=choice.message.content or "",
            model_id=response.model,
            input_tokens=response.usage.prompt_tokens,
            output_tokens=response.usage.completion_tokens,
            total_tokens=response.usage.total_tokens,
            latency_ms=latency,
            finish_reason=choice.finish_reason,
            tool_calls=tool_calls,
        )
    
    async def invoke_stream(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """Stream response from OpenAI."""
        client = await self._get_client()
        if not client:
            # Fall back to non-streaming
            response = await self.invoke(session, prompt, **kwargs)
            yield response.content
            return
        
        stream = await client.chat.completions.create(
            model=session.model_id,
            messages=[{"role": "user", "content": prompt}],
            stream=True,
            **kwargs,
        )
        
        async for chunk in stream:
            if chunk.choices[0].delta.content:
                yield chunk.choices[0].delta.content
    
    async def embed(
        self,
        session: ModelSession,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """Generate embeddings using OpenAI's embedding models."""
        client = await self._get_client()
        if not client:
            raise RuntimeError("OpenAI client not available")
        
        model = kwargs.get("embedding_model", "text-embedding-3-small")
        
        response = await client.embeddings.create(
            model=model,
            input=texts,
        )
        
        return [item.embedding for item in response.data]
    
    async def close(self) -> None:
        """Close the OpenAI client."""
        if self._client:
            await self._client.close()
            self._client = None
