"""Provider adapter contracts and the project model factory."""

from .base import ModelCapabilities, ModelCompatibilityError, ProviderAdapter
from .extensions import (
    ProviderExtensionError,
    ProviderExtensionRegistry,
    ReferenceProviderAdapter,
    assert_adapter_conformance,
    build_reference_adapter,
    load_extension_registry,
    register_reference_adapter,
)
from .factory import ModelFactory, ResolvedModel, build_model_factory
from .first_class import ProviderConfigurationError

__all__ = [
    "ModelCapabilities",
    "ModelCompatibilityError",
    "ModelFactory",
    "ProviderAdapter",
    "ResolvedModel",
    "build_model_factory",
    "ProviderConfigurationError",
    "ProviderExtensionError",
    "ProviderExtensionRegistry",
    "ReferenceProviderAdapter",
    "assert_adapter_conformance",
    "build_reference_adapter",
    "load_extension_registry",
    "register_reference_adapter",
]
