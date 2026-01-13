"""
Cohere Connector

Connector for Cohere API.
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


class CohereConnector(BaseConnector):
    """
    Connector for Cohere API.
    
    Supports Command, Command R, Command R+, Embed, and Rerank models.
    """
    
    connector_type = ConnectorType.COHERE
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        self.model_name = config.model_name or "command-r-plus"
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        model = self.model_name.lower()
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling="command-r" in model,
            supports_vision=False,
            supports_embeddings="embed" in model,
            max_context_length=self._get_context_length(),
            supports_json_mode=True,
        )
    
    def _get_context_length(self) -> int:
        """Get max context length for the model."""
        model = self.model_name.lower()
        if "command-r-plus" in model:
            return 128000
        elif "command-r" in model:
            return 128000
        elif "command" in model:
            return 4096
        else:
            return 4096
    
    async def connect(self) -> None:
        """Initialize Cohere client."""
        try:
            import cohere
            
            self._client = cohere.AsyncClient(api_key=self.config.api_key)
            
            self._connected = True
            logger.info(f"Connected to Cohere: {self.model_name}")
            
        except ImportError:
            raise ImportError("cohere package required. Install with: pip install cohere")
        except Exception as e:
            logger.error(f"Failed to connect to Cohere: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Cohere client."""
        if self._client:
            await self._client.close()
        self._client = None
        self._connected = False
        logger.info("Disconnected from Cohere")
    
    def _format_messages(self, messages: list[Message]) -> tuple[Optional[str], list[dict], str]:
        """Format messages for Cohere API."""
        preamble = None
        chat_history = []
        message = ""
        
        for i, msg in enumerate(messages):
            if msg.role == "system":
                preamble = msg.content
            elif msg.role == "user":
                if i == len(messages) - 1:
                    # Last user message is the current message
                    message = msg.content
                else:
                    chat_history.append({
                        "role": "USER",
                        "message": msg.content,
                    })
            elif msg.role == "assistant":
                chat_history.append({
                    "role": "CHATBOT",
                    "message": msg.content,
                })
        
        return preamble, chat_history, message
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from Cohere."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        preamble, chat_history, message = self._format_messages(messages)
        
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "message": message,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
            "p": config.top_p,
        }
        
        if preamble:
            kwargs["preamble"] = preamble
        
        if chat_history:
            kwargs["chat_history"] = chat_history
        
        if config.stop_sequences:
            kwargs["stop_sequences"] = config.stop_sequences
        
        response = await self._client.chat(**kwargs)
        
        usage = None
        if hasattr(response, "meta") and response.meta and hasattr(response.meta, "tokens"):
            tokens = response.meta.tokens
            usage = TokenUsage(
                prompt_tokens=tokens.input_tokens if hasattr(tokens, "input_tokens") else 0,
                completion_tokens=tokens.output_tokens if hasattr(tokens, "output_tokens") else 0,
                total_tokens=(tokens.input_tokens if hasattr(tokens, "input_tokens") else 0) +
                            (tokens.output_tokens if hasattr(tokens, "output_tokens") else 0),
            )
        
        return GenerationResponse(
            content=response.text,
            role="assistant",
            finish_reason=response.finish_reason if hasattr(response, "finish_reason") else "COMPLETE",
            usage=usage,
            model=self.model_name,
            raw_response=response.__dict__ if hasattr(response, "__dict__") else {},
        )
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from Cohere."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        preamble, chat_history, message = self._format_messages(messages)
        
        kwargs: dict[str, Any] = {
            "model": self.model_name,
            "message": message,
            "max_tokens": config.max_tokens,
            "temperature": config.temperature,
        }
        
        if preamble:
            kwargs["preamble"] = preamble
        
        if chat_history:
            kwargs["chat_history"] = chat_history
        
        async for event in self._client.chat_stream(**kwargs):
            if hasattr(event, "text"):
                yield event.text
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings using Cohere."""
        if not self._connected:
            await self.connect()
        
        embedding_model = model or self.config.extra_config.get(
            "embedding_model", "embed-english-v3.0"
        )
        
        input_type = self.config.extra_config.get("input_type", "search_document")
        
        response = await self._client.embed(
            model=embedding_model,
            texts=texts,
            input_type=input_type,
        )
        
        return response.embeddings
    
    async def rerank(
        self,
        query: str,
        documents: list[str],
        model: Optional[str] = None,
        top_n: int = 10,
    ) -> list[dict[str, Any]]:
        """Rerank documents using Cohere Rerank."""
        if not self._connected:
            await self.connect()
        
        rerank_model = model or self.config.extra_config.get(
            "rerank_model", "rerank-english-v3.0"
        )
        
        response = await self._client.rerank(
            model=rerank_model,
            query=query,
            documents=documents,
            top_n=top_n,
        )
        
        return [
            {
                "index": result.index,
                "relevance_score": result.relevance_score,
                "document": documents[result.index],
            }
            for result in response.results
        ]
    
    async def health_check(self) -> bool:
        """Check Cohere connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # Simple generation test
            await self._client.chat(
                model=self.model_name,
                message="Hi",
                max_tokens=1,
            )
            return True
        except Exception as e:
            logger.error(f"Cohere health check failed: {e}")
            return False
