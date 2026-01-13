"""
Base Connector Classes

Abstract base classes for model provider connections.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, AsyncIterator, Optional
from uuid import UUID, uuid4


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    provider: str
    model_type: str  # genai, predictive
    context_window: Optional[int] = None
    max_output_tokens: Optional[int] = None
    supports_streaming: bool = False
    supports_functions: bool = False
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class ModelSession:
    """A session for interacting with a model."""
    id: UUID = field(default_factory=uuid4)
    model_id: str = ""
    connector_type: str = ""
    config: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)
    
    # Usage tracking
    total_input_tokens: int = 0
    total_output_tokens: int = 0
    total_requests: int = 0


@dataclass
class ModelResponse:
    """Response from a model invocation."""
    content: str
    model_id: str
    
    # Token usage
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    
    # Timing
    latency_ms: int = 0
    
    # Metadata
    finish_reason: Optional[str] = None
    raw_response: Optional[dict[str, Any]] = None
    
    # For function calling
    function_call: Optional[dict[str, Any]] = None
    tool_calls: Optional[list[dict[str, Any]]] = None


class ModelConnector(ABC):
    """
    Abstract base class for model provider connections.
    
    All model connectors must implement these methods to provide
    a unified interface for model discovery and invocation.
    """
    
    connector_type: str = "base"
    supported_model_types: list[str] = []
    
    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize the connector with configuration."""
        self.config = config
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate the connector configuration."""
        required_fields = self.get_required_config_fields()
        missing = [f for f in required_fields if f not in self.config]
        if missing:
            raise ValueError(f"Missing required config fields: {missing}")
    
    @classmethod
    def get_required_config_fields(cls) -> list[str]:
        """Get list of required configuration fields."""
        return []
    
    @classmethod
    def get_optional_config_fields(cls) -> list[str]:
        """Get list of optional configuration fields."""
        return []
    
    @abstractmethod
    async def list_models(self) -> list[ModelInfo]:
        """
        Discover available models from the provider.
        
        Returns:
            List of ModelInfo objects describing available models.
        """
        ...
    
    @abstractmethod
    async def create_session(self, model_id: str) -> ModelSession:
        """
        Create an evaluation session with a specific model.
        
        Args:
            model_id: The ID of the model to use.
            
        Returns:
            A ModelSession object for subsequent invocations.
        """
        ...
    
    @abstractmethod
    async def invoke(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Send a prompt to the model and get a response.
        
        Args:
            session: The model session to use.
            prompt: The input prompt/text.
            **kwargs: Additional model-specific parameters.
            
        Returns:
            A ModelResponse with the model's output.
        """
        ...
    
    async def invoke_batch(
        self,
        session: ModelSession,
        prompts: list[str],
        **kwargs: Any,
    ) -> list[ModelResponse]:
        """
        Send multiple prompts to the model.
        
        Default implementation calls invoke() sequentially.
        Connectors can override for batch optimization.
        """
        responses = []
        for prompt in prompts:
            response = await self.invoke(session, prompt, **kwargs)
            responses.append(response)
        return responses
    
    async def invoke_stream(
        self,
        session: ModelSession,
        prompt: str,
        **kwargs: Any,
    ) -> AsyncIterator[str]:
        """
        Stream a response from the model.
        
        Default implementation yields the full response.
        Connectors can override for true streaming.
        """
        response = await self.invoke(session, prompt, **kwargs)
        yield response.content
    
    async def health_check(self) -> dict[str, Any]:
        """
        Check connector health and connectivity.
        
        Returns:
            Dict with status, latency, and any error messages.
        """
        import time
        
        try:
            start = time.time()
            models = await self.list_models()
            latency = int((time.time() - start) * 1000)
            
            return {
                "status": "healthy",
                "latency_ms": latency,
                "model_count": len(models),
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "error": str(e),
            }
    
    async def close(self) -> None:
        """Clean up connector resources."""
        pass


class PredictiveModelConnector(ModelConnector):
    """
    Base class for predictive ML model connectors.
    
    Extends ModelConnector with methods specific to
    traditional ML model inference.
    """
    
    supported_model_types = ["predictive"]
    
    @abstractmethod
    async def predict(
        self,
        session: ModelSession,
        features: Any,  # numpy array, pandas DataFrame, etc.
        **kwargs: Any,
    ) -> Any:
        """
        Get predictions from a predictive model.
        
        Args:
            session: The model session.
            features: Input features for prediction.
            
        Returns:
            Model predictions (format depends on model type).
        """
        ...
    
    @abstractmethod
    async def predict_proba(
        self,
        session: ModelSession,
        features: Any,
        **kwargs: Any,
    ) -> Any:
        """
        Get prediction probabilities (for classifiers).
        """
        ...
    
    async def get_feature_names(self, session: ModelSession) -> list[str]:
        """Get expected feature names for the model."""
        return []
    
    async def get_class_names(self, session: ModelSession) -> list[str]:
        """Get class names for classification models."""
        return []


class LLMConnector(ModelConnector):
    """
    Base class for LLM connectors.
    
    Extends ModelConnector with LLM-specific functionality
    like chat completions and function calling.
    """
    
    supported_model_types = ["genai"]
    
    @abstractmethod
    async def chat(
        self,
        session: ModelSession,
        messages: list[dict[str, str]],
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Send a chat conversation to the model.
        
        Args:
            session: The model session.
            messages: List of message dicts with 'role' and 'content'.
            
        Returns:
            ModelResponse with the assistant's reply.
        """
        ...
    
    async def chat_with_functions(
        self,
        session: ModelSession,
        messages: list[dict[str, str]],
        functions: list[dict[str, Any]],
        **kwargs: Any,
    ) -> ModelResponse:
        """
        Chat with function calling capability.
        
        Args:
            session: The model session.
            messages: Conversation messages.
            functions: Available function definitions.
            
        Returns:
            ModelResponse potentially containing function_call.
        """
        # Default: fall back to regular chat
        return await self.chat(session, messages, **kwargs)
    
    async def embed(
        self,
        session: ModelSession,
        texts: list[str],
        **kwargs: Any,
    ) -> list[list[float]]:
        """
        Generate embeddings for texts.
        
        Not all LLM connectors support embeddings.
        """
        raise NotImplementedError("This connector does not support embeddings")
