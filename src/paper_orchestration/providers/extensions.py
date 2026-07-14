"""Extension-provider registration and reusable adapter conformance checks."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import EntryPoint, entry_points
from typing import Any, Protocol

from ..config import ProviderProfile
from .base import ModelCapabilities, ProviderAdapter

ENTRY_POINT_GROUP = "paper_orchestration.providers"
AdapterBuilder = Callable[[str, ProviderProfile], ProviderAdapter]


class ProviderExtensionError(RuntimeError):
    """Raised when an extension registration cannot be loaded or used."""


class AdapterRegistration(Protocol):
    def __call__(self, model: str, profile: ProviderProfile) -> ProviderAdapter:
        """Build an adapter for the resolved model and profile."""


@dataclass(frozen=True)
class ProviderExtension:
    name: str
    builder: AdapterRegistration
    verified: bool = False


class ProviderExtensionRegistry:
    """In-memory registry populated by applications or Python entry points."""

    def __init__(self) -> None:
        self._extensions: dict[str, ProviderExtension] = {}

    def register(
        self,
        name: str,
        builder: AdapterRegistration,
        *,
        verified: bool = False,
    ) -> None:
        if not name or not name.replace("-", "").replace("_", "").isalnum():
            raise ProviderExtensionError(
                f"Provider extension name {name!r} must contain only letters, numbers, '-' or '_'."
            )
        if name in self._extensions:
            raise ProviderExtensionError(f"Provider extension {name!r} is already registered.")
        self._extensions[name] = ProviderExtension(name, builder, verified)

    def get(self, name: str) -> ProviderExtension | None:
        return self._extensions.get(name)

    def names(self) -> tuple[str, ...]:
        return tuple(sorted(self._extensions))

    def build(self, provider: str, model: str, profile: ProviderProfile) -> ProviderAdapter:
        extension = self.get(provider)
        if extension is None:
            raise ProviderExtensionError(
                f"No adapter is registered for extension provider {provider!r}. "
                f"Available extensions: {', '.join(self.names()) or 'none'}."
            )
        try:
            adapter = extension.builder(model, profile)
        except ProviderExtensionError:
            raise
        except Exception as exc:
            raise ProviderExtensionError(
                f"Extension provider {provider!r} failed while building model {model!r}: {exc}"
            ) from exc
        if (
            getattr(adapter, "provider", None) != provider
            or getattr(adapter, "model", None) != model
        ):
            raise ProviderExtensionError(
                f"Extension provider {provider!r} returned an adapter with mismatched "
                "provider/model."
            )
        return adapter

    def load_entry_points(self, group: str = ENTRY_POINT_GROUP) -> None:
        """Load trusted package entry points and fail with the entry point name on errors."""
        discovered = entry_points()
        candidates = (
            discovered.select(group=group)
            if hasattr(discovered, "select")
            else discovered.get(group, ())
        )
        for point in candidates:
            if not isinstance(point, EntryPoint):
                name = getattr(point, "name", repr(point))
            else:
                name = point.name
            try:
                loaded = point.load()
                if callable(loaded):
                    builder = loaded
                elif hasattr(loaded, "build_adapter") and callable(loaded.build_adapter):
                    builder = loaded.build_adapter
                else:
                    raise TypeError("entry point must resolve to a builder or expose build_adapter")
                self.register(name, builder, verified=False)
            except ProviderExtensionError:
                raise
            except Exception as exc:
                raise ProviderExtensionError(
                    f"Could not load provider extension entry point {name!r}: {exc}"
                ) from exc


def load_extension_registry(*, include_entry_points: bool = True) -> ProviderExtensionRegistry:
    registry = ProviderExtensionRegistry()
    if include_entry_points:
        registry.load_entry_points()
    return registry


@dataclass(frozen=True)
class ReferenceProviderAdapter:
    """Offline adapter used by extension authors as a minimal working example."""

    provider: str
    model: str
    profile: ProviderProfile

    def capabilities(self) -> ModelCapabilities:
        return ModelCapabilities(structured_output=True, tool_calling=True)

    def create_model(self) -> Any:
        return {"provider": self.provider, "model": self.model, "reference": True}


def build_reference_adapter(model: str, profile: ProviderProfile) -> ReferenceProviderAdapter:
    return ReferenceProviderAdapter(profile.provider, model, profile)


def register_reference_adapter(registry: ProviderExtensionRegistry) -> None:
    registry.register("reference", build_reference_adapter)


def assert_adapter_conformance(adapter: ProviderAdapter) -> None:
    """Assert the shared contract for an adapter; useful in third-party test suites."""
    provider = getattr(adapter, "provider", None)
    model = getattr(adapter, "model", None)
    if not isinstance(provider, str) or not provider:
        raise AssertionError("adapter.provider must be a non-empty string")
    if not isinstance(model, str) or not model:
        raise AssertionError("adapter.model must be a non-empty string")
    capabilities = adapter.capabilities()
    if not isinstance(capabilities, ModelCapabilities):
        raise AssertionError("adapter.capabilities() must return ModelCapabilities")
    missing = capabilities.missing_required()
    if missing:
        raise AssertionError(f"adapter is missing required capabilities: {', '.join(missing)}")
    if adapter.create_model() is None:
        raise AssertionError("adapter.create_model() must return a model")
