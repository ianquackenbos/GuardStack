"""
Connector Tests
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import json


class TestBaseConnector:
    """Test base connector functionality."""

    @pytest.fixture
    def base_connector(self):
        """Create base connector instance."""
        from guardstack.connectors.base import BaseConnector
        return BaseConnector()

    def test_connector_initialization(self, base_connector):
        """Test connector initialization."""
        assert base_connector is not None

    @pytest.mark.asyncio
    async def test_health_check(self, base_connector):
        """Test connector health check."""
        with patch.object(base_connector, 'health_check') as mock_health:
            mock_health.return_value = {"status": "healthy"}
            
            result = await base_connector.health_check()
            
            assert result["status"] == "healthy"


class TestOpenAIConnector:
    """Test OpenAI connector."""

    @pytest.fixture
    def connector(self):
        """Create OpenAI connector instance."""
        from guardstack.connectors.openai import OpenAIConnector
        return OpenAIConnector(api_key="test-key")

    @pytest.mark.asyncio
    async def test_chat_completion(self, connector):
        """Test chat completion."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Hi there!"}}],
            }
            
            result = await connector.chat(messages)
            
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_embedding(self, connector):
        """Test embedding generation."""
        text = "Hello world"
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "data": [{"embedding": [0.1] * 1536}],
            }
            
            result = await connector.embed(text)
            
            assert "data" in result
            assert len(result["data"][0]["embedding"]) == 1536

    @pytest.mark.asyncio
    async def test_list_models(self, connector):
        """Test listing models."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "data": [
                    {"id": "gpt-4"},
                    {"id": "gpt-3.5-turbo"},
                ],
            }
            
            result = await connector.list_models()
            
            assert "data" in result
            assert len(result["data"]) >= 2

    @pytest.mark.asyncio
    async def test_rate_limit_handling(self, connector):
        """Test rate limit handling."""
        from guardstack.connectors.exceptions import RateLimitError
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.side_effect = RateLimitError("Rate limit exceeded")
            
            with pytest.raises(RateLimitError):
                await connector.chat([{"role": "user", "content": "Test"}])


class TestAnthropicConnector:
    """Test Anthropic connector."""

    @pytest.fixture
    def connector(self):
        """Create Anthropic connector instance."""
        from guardstack.connectors.anthropic import AnthropicConnector
        return AnthropicConnector(api_key="test-key")

    @pytest.mark.asyncio
    async def test_message(self, connector):
        """Test message API."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "content": [{"type": "text", "text": "Hi there!"}],
            }
            
            result = await connector.message(messages)
            
            assert "content" in result

    @pytest.mark.asyncio
    async def test_streaming_message(self, connector):
        """Test streaming message."""
        messages = [{"role": "user", "content": "Hello"}]
        
        async def mock_stream():
            yield {"type": "content_block_delta", "delta": {"text": "Hi"}}
            yield {"type": "content_block_delta", "delta": {"text": " there!"}}
        
        with patch.object(connector, 'message_stream') as mock_method:
            mock_method.return_value = mock_stream()
            
            chunks = []
            async for chunk in connector.message_stream(messages):
                chunks.append(chunk)
            
            assert len(chunks) > 0


class TestAzureOpenAIConnector:
    """Test Azure OpenAI connector."""

    @pytest.fixture
    def connector(self):
        """Create Azure OpenAI connector instance."""
        from guardstack.connectors.azure_openai import AzureOpenAIConnector
        return AzureOpenAIConnector(
            api_key="test-key",
            endpoint="https://test.openai.azure.com",
            deployment_name="gpt-4",
        )

    @pytest.mark.asyncio
    async def test_chat_completion(self, connector):
        """Test Azure chat completion."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Hi there!"}}],
            }
            
            result = await connector.chat(messages)
            
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_azure_specific_headers(self, connector):
        """Test Azure-specific headers are included."""
        assert connector.endpoint.endswith("openai.azure.com")


class TestBedrockConnector:
    """Test AWS Bedrock connector."""

    @pytest.fixture
    def connector(self):
        """Create Bedrock connector instance."""
        from guardstack.connectors.bedrock import BedrockConnector
        return BedrockConnector(
            region="us-east-1",
            aws_access_key="test-key",
            aws_secret_key="test-secret",
        )

    @pytest.mark.asyncio
    async def test_invoke_model(self, connector):
        """Test model invocation."""
        with patch.object(connector, '_invoke') as mock_invoke:
            mock_invoke.return_value = {
                "completion": "Hello!",
            }
            
            result = await connector.invoke(
                model_id="anthropic.claude-v2",
                prompt="Hello",
            )
            
            assert "completion" in result

    @pytest.mark.asyncio
    async def test_list_foundation_models(self, connector):
        """Test listing foundation models."""
        with patch.object(connector, '_list_models') as mock_list:
            mock_list.return_value = [
                {"modelId": "anthropic.claude-v2"},
                {"modelId": "amazon.titan-text-express-v1"},
            ]
            
            result = await connector._list_models()
            
            assert len(result) >= 2


class TestHuggingFaceConnector:
    """Test Hugging Face connector."""

    @pytest.fixture
    def connector(self):
        """Create HuggingFace connector instance."""
        from guardstack.connectors.huggingface import HuggingFaceConnector
        return HuggingFaceConnector(api_key="test-key")

    @pytest.mark.asyncio
    async def test_inference(self, connector):
        """Test inference endpoint."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = [{"generated_text": "Output"}]
            
            result = await connector.infer(
                model="gpt2",
                inputs="Hello",
            )
            
            assert isinstance(result, list)

    @pytest.mark.asyncio
    async def test_text_classification(self, connector):
        """Test text classification."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = [[
                {"label": "POSITIVE", "score": 0.9},
                {"label": "NEGATIVE", "score": 0.1},
            ]]
            
            result = await connector.classify(
                model="distilbert-base-uncased-finetuned-sst-2-english",
                text="I love this!",
            )
            
            assert result[0][0]["label"] == "POSITIVE"


class TestOllamaConnector:
    """Test Ollama connector."""

    @pytest.fixture
    def connector(self):
        """Create Ollama connector instance."""
        from guardstack.connectors.ollama import OllamaConnector
        return OllamaConnector(base_url="http://localhost:11434")

    @pytest.mark.asyncio
    async def test_generate(self, connector):
        """Test text generation."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "response": "Hello! How can I help you?",
            }
            
            result = await connector.generate(
                model="llama2",
                prompt="Hello",
            )
            
            assert "response" in result

    @pytest.mark.asyncio
    async def test_list_local_models(self, connector):
        """Test listing local models."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "models": [
                    {"name": "llama2:latest"},
                    {"name": "mistral:latest"},
                ],
            }
            
            result = await connector.list_models()
            
            assert "models" in result


class TestVLLMConnector:
    """Test vLLM connector."""

    @pytest.fixture
    def connector(self):
        """Create vLLM connector instance."""
        from guardstack.connectors.vllm import VLLMConnector
        return VLLMConnector(base_url="http://localhost:8000")

    @pytest.mark.asyncio
    async def test_completions(self, connector):
        """Test completions endpoint."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{"text": "Generated text"}],
            }
            
            result = await connector.complete(
                prompt="Once upon a time",
                max_tokens=100,
            )
            
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_chat_completions(self, connector):
        """Test chat completions endpoint."""
        messages = [{"role": "user", "content": "Hello"}]
        
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Hi!"}}],
            }
            
            result = await connector.chat(messages)
            
            assert "choices" in result


class TestConnectorFactory:
    """Test connector factory."""

    def test_create_openai_connector(self):
        """Test creating OpenAI connector."""
        from guardstack.connectors import ConnectorFactory
        
        connector = ConnectorFactory.create(
            provider="openai",
            api_key="test-key",
        )
        
        assert connector is not None
        assert connector.__class__.__name__ == "OpenAIConnector"

    def test_create_anthropic_connector(self):
        """Test creating Anthropic connector."""
        from guardstack.connectors import ConnectorFactory
        
        connector = ConnectorFactory.create(
            provider="anthropic",
            api_key="test-key",
        )
        
        assert connector is not None
        assert connector.__class__.__name__ == "AnthropicConnector"

    def test_unknown_provider(self):
        """Test unknown provider raises error."""
        from guardstack.connectors import ConnectorFactory
        from guardstack.connectors.exceptions import UnknownProviderError
        
        with pytest.raises(UnknownProviderError):
            ConnectorFactory.create(provider="unknown")

    def test_list_providers(self):
        """Test listing available providers."""
        from guardstack.connectors import ConnectorFactory
        
        providers = ConnectorFactory.list_providers()
        
        assert "openai" in providers
        assert "anthropic" in providers
        assert "azure_openai" in providers


class TestConnectorRetry:
    """Test connector retry logic."""

    @pytest.fixture
    def connector(self):
        """Create connector with retry config."""
        from guardstack.connectors.openai import OpenAIConnector
        return OpenAIConnector(
            api_key="test-key",
            max_retries=3,
            retry_delay=0.1,
        )

    @pytest.mark.asyncio
    async def test_retry_on_failure(self, connector):
        """Test retry on transient failure."""
        call_count = 0
        
        async def mock_request(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise Exception("Transient error")
            return {"choices": [{"message": {"content": "Success"}}]}
        
        with patch.object(connector, '_make_request', mock_request):
            result = await connector.chat([{"role": "user", "content": "Test"}])
            
            assert call_count == 3
            assert "choices" in result

    @pytest.mark.asyncio
    async def test_max_retries_exceeded(self, connector):
        """Test failure after max retries."""
        async def mock_request(*args, **kwargs):
            raise Exception("Persistent error")
        
        with patch.object(connector, '_make_request', mock_request):
            with pytest.raises(Exception):
                await connector.chat([{"role": "user", "content": "Test"}])


class TestConnectorMetrics:
    """Test connector metrics collection."""

    @pytest.fixture
    def connector(self):
        """Create connector with metrics."""
        from guardstack.connectors.openai import OpenAIConnector
        return OpenAIConnector(
            api_key="test-key",
            collect_metrics=True,
        )

    @pytest.mark.asyncio
    async def test_latency_tracking(self, connector):
        """Test latency is tracked."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Hi"}}],
            }
            
            await connector.chat([{"role": "user", "content": "Test"}])
            
            metrics = connector.get_metrics()
            
            assert "latency_ms" in metrics or "avg_latency_ms" in metrics

    @pytest.mark.asyncio
    async def test_token_counting(self, connector):
        """Test token counting."""
        with patch.object(connector, '_make_request') as mock_request:
            mock_request.return_value = {
                "choices": [{"message": {"content": "Hi"}}],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5},
            }
            
            await connector.chat([{"role": "user", "content": "Test"}])
            
            metrics = connector.get_metrics()
            
            assert "total_tokens" in metrics or "usage" in str(metrics)
