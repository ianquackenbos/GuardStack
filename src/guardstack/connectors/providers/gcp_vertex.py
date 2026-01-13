"""
Google Cloud Vertex AI Connector

Connector for GCP Vertex AI models.
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


class GCPVertexConnector(BaseConnector):
    """
    Connector for Google Cloud Vertex AI.
    
    Supports Gemini, PaLM, and other Vertex AI models.
    """
    
    connector_type = ConnectorType.GCP_VERTEX
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        self._model: Optional[Any] = None
        
        # GCP-specific configuration
        self.project_id = config.extra_config.get("project_id")
        self.location = config.extra_config.get("location", "us-central1")
        self.model_name = config.model_name
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling="gemini" in self.model_name.lower(),
            supports_vision="gemini" in self.model_name.lower() or "vision" in self.model_name.lower(),
            supports_embeddings="embedding" in self.model_name.lower() or "gecko" in self.model_name.lower(),
            max_context_length=self._get_context_length(),
            supports_json_mode=True,
        )
    
    def _get_context_length(self) -> int:
        """Get max context length for the model."""
        model = self.model_name.lower()
        if "gemini-1.5-pro" in model:
            return 1000000  # 1M tokens
        elif "gemini-1.5-flash" in model:
            return 1000000
        elif "gemini-1.0-pro" in model or "gemini-pro" in model:
            return 32768
        elif "palm" in model or "text-bison" in model:
            return 8192
        else:
            return 8192
    
    async def connect(self) -> None:
        """Initialize Vertex AI client."""
        try:
            import vertexai
            from vertexai.generative_models import GenerativeModel
            
            # Initialize Vertex AI
            vertexai.init(
                project=self.project_id,
                location=self.location,
            )
            
            # Load the model
            self._model = GenerativeModel(self.model_name)
            
            self._connected = True
            logger.info(f"Connected to Vertex AI: {self.model_name}")
            
        except ImportError:
            raise ImportError(
                "google-cloud-aiplatform package required. "
                "Install with: pip install google-cloud-aiplatform"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Vertex AI: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close Vertex AI client."""
        self._model = None
        self._connected = False
        logger.info("Disconnected from Vertex AI")
    
    def _format_messages(self, messages: list[Message]) -> tuple[Optional[str], list[Any]]:
        """Format messages for Vertex AI API."""
        from vertexai.generative_models import Content, Part
        
        system_instruction = None
        contents = []
        
        for msg in messages:
            if msg.role == "system":
                system_instruction = msg.content
            elif msg.role == "user":
                contents.append(Content(
                    role="user",
                    parts=[Part.from_text(msg.content)],
                ))
            elif msg.role == "assistant":
                contents.append(Content(
                    role="model",
                    parts=[Part.from_text(msg.content)],
                ))
        
        return system_instruction, contents
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from Vertex AI."""
        if not self._connected:
            await self.connect()
        
        from vertexai.generative_models import GenerationConfig as VertexGenConfig
        
        config = config or GenerationConfig()
        
        system_instruction, contents = self._format_messages(messages)
        
        # Configure generation parameters
        generation_config = VertexGenConfig(
            max_output_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
            stop_sequences=config.stop_sequences or [],
        )
        
        # Create model with system instruction if provided
        model = self._model
        if system_instruction:
            from vertexai.generative_models import GenerativeModel
            model = GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
            )
        
        response = await model.generate_content_async(
            contents,
            generation_config=generation_config,
        )
        
        # Extract usage metadata
        usage = None
        if response.usage_metadata:
            usage = TokenUsage(
                prompt_tokens=response.usage_metadata.prompt_token_count,
                completion_tokens=response.usage_metadata.candidates_token_count,
                total_tokens=response.usage_metadata.total_token_count,
            )
        
        return GenerationResponse(
            content=response.text,
            role="assistant",
            finish_reason=response.candidates[0].finish_reason.name if response.candidates else "STOP",
            usage=usage,
            model=self.model_name,
            raw_response=response.to_dict(),
        )
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from Vertex AI."""
        if not self._connected:
            await self.connect()
        
        from vertexai.generative_models import GenerationConfig as VertexGenConfig
        
        config = config or GenerationConfig()
        
        system_instruction, contents = self._format_messages(messages)
        
        generation_config = VertexGenConfig(
            max_output_tokens=config.max_tokens,
            temperature=config.temperature,
            top_p=config.top_p,
        )
        
        model = self._model
        if system_instruction:
            from vertexai.generative_models import GenerativeModel
            model = GenerativeModel(
                self.model_name,
                system_instruction=system_instruction,
            )
        
        response = await model.generate_content_async(
            contents,
            generation_config=generation_config,
            stream=True,
        )
        
        async for chunk in response:
            if chunk.text:
                yield chunk.text
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings using Vertex AI."""
        if not self._connected:
            await self.connect()
        
        from vertexai.language_models import TextEmbeddingModel
        
        embedding_model_name = model or self.config.extra_config.get(
            "embedding_model", "text-embedding-004"
        )
        
        embedding_model = TextEmbeddingModel.from_pretrained(embedding_model_name)
        
        embeddings = []
        # Batch texts (max 250 per batch for Vertex AI)
        batch_size = 250
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = embedding_model.get_embeddings(batch)
            embeddings.extend([e.values for e in batch_embeddings])
        
        return embeddings
    
    async def health_check(self) -> bool:
        """Check Vertex AI connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # Simple generation test
            from vertexai.generative_models import Content, Part
            
            test_content = Content(
                role="user",
                parts=[Part.from_text("Hi")],
            )
            
            await self._model.generate_content_async(
                [test_content],
                generation_config={"max_output_tokens": 1},
            )
            return True
        except Exception as e:
            logger.error(f"Vertex AI health check failed: {e}")
            return False
