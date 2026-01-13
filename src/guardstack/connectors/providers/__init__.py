"""
GuardStack Connector Providers

All available LLM connector implementations.
"""

from guardstack.connectors.providers.anthropic import AnthropicConnector
from guardstack.connectors.providers.aws_bedrock import AWSBedrockConnector
from guardstack.connectors.providers.azure import AzureOpenAIConnector
from guardstack.connectors.providers.cohere import CohereConnector
from guardstack.connectors.providers.custom import CustomConnector
from guardstack.connectors.providers.gcp_vertex import GCPVertexConnector
from guardstack.connectors.providers.huggingface import HuggingFaceConnector
from guardstack.connectors.providers.lmstudio import LMStudioConnector
from guardstack.connectors.providers.mistral import MistralConnector
from guardstack.connectors.providers.ollama import OllamaConnector
from guardstack.connectors.providers.openai import OpenAIConnector
from guardstack.connectors.providers.vllm import VLLMConnector

__all__ = [
    # Cloud Providers
    "OpenAIConnector",
    "AzureOpenAIConnector",
    "AnthropicConnector",
    "AWSBedrockConnector",
    "GCPVertexConnector",
    "MistralConnector",
    "CohereConnector",
    # Open Source / Local
    "HuggingFaceConnector",
    "OllamaConnector",
    "VLLMConnector",
    "LMStudioConnector",
    # Custom
    "CustomConnector",
]

# Provider mapping for registry
PROVIDER_MAP = {
    "openai": OpenAIConnector,
    "azure": AzureOpenAIConnector,
    "azure_openai": AzureOpenAIConnector,
    "anthropic": AnthropicConnector,
    "aws_bedrock": AWSBedrockConnector,
    "bedrock": AWSBedrockConnector,
    "gcp_vertex": GCPVertexConnector,
    "vertex": GCPVertexConnector,
    "google": GCPVertexConnector,
    "mistral": MistralConnector,
    "cohere": CohereConnector,
    "huggingface": HuggingFaceConnector,
    "hf": HuggingFaceConnector,
    "ollama": OllamaConnector,
    "vllm": VLLMConnector,
    "lmstudio": LMStudioConnector,
    "lm_studio": LMStudioConnector,
    "custom": CustomConnector,
}


def get_connector_class(provider: str):
    """Get connector class by provider name."""
    provider_lower = provider.lower()
    if provider_lower not in PROVIDER_MAP:
        raise ValueError(f"Unknown provider: {provider}. Available: {list(PROVIDER_MAP.keys())}")
    return PROVIDER_MAP[provider_lower]
