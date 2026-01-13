"""
AWS Bedrock Connector

Connector for AWS Bedrock managed models.
"""

import json
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


class AWSBedrockConnector(BaseConnector):
    """
    Connector for AWS Bedrock.
    
    Supports Claude, Llama, Mistral, and other Bedrock models.
    """
    
    connector_type = ConnectorType.AWS_BEDROCK
    
    def __init__(self, config: ConnectorConfig):
        super().__init__(config)
        self._client: Optional[Any] = None
        self._runtime_client: Optional[Any] = None
        
        # AWS-specific configuration
        self.region = config.extra_config.get("region", "us-east-1")
        self.model_id = config.model_name
    
    @property
    def capabilities(self) -> ConnectorCapabilities:
        return ConnectorCapabilities(
            supports_streaming=True,
            supports_function_calling="claude" in self.model_id.lower(),
            supports_vision="claude-3" in self.model_id.lower(),
            supports_embeddings="embed" in self.model_id.lower() or "titan" in self.model_id.lower(),
            max_context_length=self._get_context_length(),
            supports_json_mode=True,
        )
    
    def _get_context_length(self) -> int:
        """Get max context length for the model."""
        model = self.model_id.lower()
        if "claude-3" in model:
            return 200000
        elif "claude-2" in model:
            return 100000
        elif "llama-3" in model:
            return 8192
        elif "mistral-large" in model:
            return 32768
        else:
            return 4096
    
    async def connect(self) -> None:
        """Initialize AWS Bedrock client."""
        try:
            import boto3
            from botocore.config import Config
            
            boto_config = Config(
                region_name=self.region,
                retries={"max_attempts": 3, "mode": "adaptive"},
            )
            
            # Use credentials from config or environment
            session_kwargs = {}
            if self.config.api_key:
                # Parse as access_key:secret_key format
                if ":" in self.config.api_key:
                    access_key, secret_key = self.config.api_key.split(":", 1)
                    session_kwargs["aws_access_key_id"] = access_key
                    session_kwargs["aws_secret_access_key"] = secret_key
            
            session = boto3.Session(**session_kwargs)
            
            self._client = session.client("bedrock", config=boto_config)
            self._runtime_client = session.client("bedrock-runtime", config=boto_config)
            
            self._connected = True
            logger.info(f"Connected to AWS Bedrock: {self.model_id}")
            
        except ImportError:
            raise ImportError("boto3 package required. Install with: pip install boto3")
        except Exception as e:
            logger.error(f"Failed to connect to AWS Bedrock: {e}")
            raise
    
    async def disconnect(self) -> None:
        """Close AWS Bedrock client."""
        self._client = None
        self._runtime_client = None
        self._connected = False
        logger.info("Disconnected from AWS Bedrock")
    
    def _format_messages(self, messages: list[Message]) -> dict[str, Any]:
        """Format messages for Bedrock API based on model type."""
        model = self.model_id.lower()
        
        if "claude" in model:
            # Anthropic Claude format
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
            
            body = {"messages": api_messages}
            if system_message:
                body["system"] = system_message
            
            return body
        
        elif "llama" in model:
            # Meta Llama format
            prompt = ""
            for msg in messages:
                if msg.role == "system":
                    prompt += f"<|begin_of_text|><|start_header_id|>system<|end_header_id|>\n\n{msg.content}<|eot_id|>"
                elif msg.role == "user":
                    prompt += f"<|start_header_id|>user<|end_header_id|>\n\n{msg.content}<|eot_id|>"
                elif msg.role == "assistant":
                    prompt += f"<|start_header_id|>assistant<|end_header_id|>\n\n{msg.content}<|eot_id|>"
            
            prompt += "<|start_header_id|>assistant<|end_header_id|>\n\n"
            return {"prompt": prompt}
        
        elif "mistral" in model:
            # Mistral format
            prompt = ""
            for msg in messages:
                if msg.role == "user":
                    prompt += f"[INST] {msg.content} [/INST]"
                elif msg.role == "assistant":
                    prompt += f"{msg.content}"
            
            return {"prompt": prompt}
        
        else:
            # Generic format
            prompt = "\n".join([f"{msg.role}: {msg.content}" for msg in messages])
            return {"inputText": prompt}
    
    async def generate(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> GenerationResponse:
        """Generate a response from AWS Bedrock."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        body = self._format_messages(messages)
        
        # Add generation parameters based on model
        model = self.model_id.lower()
        if "claude" in model:
            body["max_tokens"] = config.max_tokens
            body["temperature"] = config.temperature
            body["top_p"] = config.top_p
            if config.stop_sequences:
                body["stop_sequences"] = config.stop_sequences
        else:
            body["max_gen_len"] = config.max_tokens
            body["temperature"] = config.temperature
            body["top_p"] = config.top_p
        
        response = self._runtime_client.invoke_model(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        
        result = json.loads(response["body"].read())
        
        # Parse response based on model type
        if "claude" in model:
            content = result.get("content", [{}])[0].get("text", "")
            usage = TokenUsage(
                prompt_tokens=result.get("usage", {}).get("input_tokens", 0),
                completion_tokens=result.get("usage", {}).get("output_tokens", 0),
                total_tokens=result.get("usage", {}).get("input_tokens", 0) + 
                            result.get("usage", {}).get("output_tokens", 0),
            )
            finish_reason = result.get("stop_reason", "end_turn")
        elif "llama" in model:
            content = result.get("generation", "")
            usage = TokenUsage(
                prompt_tokens=result.get("prompt_token_count", 0),
                completion_tokens=result.get("generation_token_count", 0),
                total_tokens=result.get("prompt_token_count", 0) +
                            result.get("generation_token_count", 0),
            )
            finish_reason = result.get("stop_reason", "stop")
        else:
            content = result.get("results", [{}])[0].get("outputText", "")
            usage = None
            finish_reason = "stop"
        
        return GenerationResponse(
            content=content,
            role="assistant",
            finish_reason=finish_reason,
            usage=usage,
            model=self.model_id,
            raw_response=result,
        )
    
    async def generate_stream(
        self,
        messages: list[Message],
        config: Optional[GenerationConfig] = None,
    ) -> AsyncIterator[str]:
        """Stream a response from AWS Bedrock."""
        if not self._connected:
            await self.connect()
        
        config = config or GenerationConfig()
        
        body = self._format_messages(messages)
        
        model = self.model_id.lower()
        if "claude" in model:
            body["max_tokens"] = config.max_tokens
            body["temperature"] = config.temperature
        
        response = self._runtime_client.invoke_model_with_response_stream(
            modelId=self.model_id,
            body=json.dumps(body),
            contentType="application/json",
            accept="application/json",
        )
        
        for event in response["body"]:
            chunk = json.loads(event["chunk"]["bytes"])
            
            if "claude" in model:
                if chunk.get("type") == "content_block_delta":
                    text = chunk.get("delta", {}).get("text", "")
                    if text:
                        yield text
            else:
                text = chunk.get("generation", chunk.get("outputText", ""))
                if text:
                    yield text
    
    async def embed(
        self,
        texts: list[str],
        model: Optional[str] = None,
    ) -> list[list[float]]:
        """Generate embeddings using AWS Bedrock."""
        if not self._connected:
            await self.connect()
        
        embedding_model = model or self.config.extra_config.get(
            "embedding_model", "amazon.titan-embed-text-v1"
        )
        
        embeddings = []
        for text in texts:
            body = {"inputText": text}
            
            response = self._runtime_client.invoke_model(
                modelId=embedding_model,
                body=json.dumps(body),
                contentType="application/json",
                accept="application/json",
            )
            
            result = json.loads(response["body"].read())
            embeddings.append(result["embedding"])
        
        return embeddings
    
    async def health_check(self) -> bool:
        """Check AWS Bedrock connectivity."""
        try:
            if not self._connected:
                await self.connect()
            
            # List foundation models to verify connection
            self._client.list_foundation_models(byProvider="anthropic")
            return True
        except Exception as e:
            logger.error(f"AWS Bedrock health check failed: {e}")
            return False
