"""
Connector Registry

Registry for managing and instantiating model connectors.
"""

from typing import Any, Type

from guardstack.connectors.base import ModelConnector


class ConnectorRegistry:
    """
    Registry for model connector classes.
    
    Provides a central place to register and instantiate
    connectors by type.
    """
    
    _connectors: dict[str, Type[ModelConnector]] = {}
    
    @classmethod
    def register(cls, connector_type: str) -> callable:
        """
        Decorator to register a connector class.
        
        Usage:
            @ConnectorRegistry.register("openai")
            class OpenAIConnector(LLMConnector):
                ...
        """
        def decorator(connector_class: Type[ModelConnector]) -> Type[ModelConnector]:
            cls._connectors[connector_type] = connector_class
            connector_class.connector_type = connector_type
            return connector_class
        return decorator
    
    @classmethod
    def get(cls, connector_type: str) -> Type[ModelConnector]:
        """
        Get a connector class by type.
        
        Args:
            connector_type: The type of connector (e.g., "openai", "ollama").
            
        Returns:
            The connector class.
            
        Raises:
            KeyError: If connector type is not registered.
        """
        if connector_type not in cls._connectors:
            raise KeyError(f"Unknown connector type: {connector_type}")
        return cls._connectors[connector_type]
    
    @classmethod
    def create(
        cls,
        connector_type: str,
        config: dict[str, Any],
    ) -> ModelConnector:
        """
        Create a connector instance.
        
        Args:
            connector_type: The type of connector.
            config: Configuration for the connector.
            
        Returns:
            An initialized connector instance.
        """
        connector_class = cls.get(connector_type)
        return connector_class(config)
    
    @classmethod
    def list_types(cls) -> list[str]:
        """Get list of registered connector types."""
        return list(cls._connectors.keys())
    
    @classmethod
    def get_info(cls, connector_type: str) -> dict[str, Any]:
        """Get information about a connector type."""
        connector_class = cls.get(connector_type)
        return {
            "type": connector_type,
            "class": connector_class.__name__,
            "supported_model_types": connector_class.supported_model_types,
            "required_config": connector_class.get_required_config_fields(),
            "optional_config": connector_class.get_optional_config_fields(),
        }


# Import providers to register them
def register_all_connectors() -> None:
    """Import all connector providers to register them."""
    from guardstack.connectors.providers import (
        openai,
        anthropic,
        ollama,
        huggingface,
        # azure,
        # aws_bedrock,
        # gcp_vertex,
    )
