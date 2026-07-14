from pathlib import Path

import pytest

from paper_orchestration.config import ProviderProfile, Settings
from paper_orchestration.providers import (
    ProviderExtensionError,
    ProviderExtensionRegistry,
    assert_adapter_conformance,
    register_reference_adapter,
)
from paper_orchestration.providers.base import ModelCapabilities
from paper_orchestration.providers.factory import ModelFactory
from paper_orchestration.providers.first_class import build_first_class_adapter


def reference_profile() -> ProviderProfile:
    return ProviderProfile(name="reference", provider="reference", model="demo")


def reference_settings() -> Settings:
    return Settings(
        api_key=None,
        model="reference:demo",
        database_path=Path("outputs/test.db"),
        profile_name="reference",
        provider="reference",
        profiles={"reference": reference_profile()},
    )


def test_reference_extension_registers_and_is_selected_by_factory() -> None:
    registry = ProviderExtensionRegistry()
    register_reference_adapter(registry)

    resolved = ModelFactory(reference_settings(), extensions=registry).preflight("intake")

    assert resolved.provider == "reference"
    assert resolved.create_model()["reference"] is True
    assert_adapter_conformance(resolved.adapter)


def test_conformance_suite_accepts_first_class_adapter(monkeypatch) -> None:
    monkeypatch.setenv("OPENAI_API_KEY", "fake-key")
    adapter = build_first_class_adapter(
        "openai",
        "gpt-test",
        ProviderProfile(name="openai", provider="openai", model="gpt-test"),
    )

    assert_adapter_conformance(adapter)


def test_duplicate_names_fail_actionably() -> None:
    registry = ProviderExtensionRegistry()
    register_reference_adapter(registry)

    with pytest.raises(ProviderExtensionError, match="already registered"):
        register_reference_adapter(registry)


def test_conformance_rejects_missing_capabilities() -> None:
    class IncompleteAdapter:
        provider = "reference"
        model = "demo"

        def capabilities(self):
            return ModelCapabilities(structured_output=True, tool_calling=False)

        def create_model(self):
            return object()

    with pytest.raises(AssertionError, match="tool_calling"):
        assert_adapter_conformance(IncompleteAdapter())


def test_broken_entry_point_names_the_entry_point(monkeypatch) -> None:
    class BrokenPoint:
        name = "broken"

        def load(self):
            raise RuntimeError("boom")

    monkeypatch.setattr(
        "paper_orchestration.providers.extensions.entry_points",
        lambda: type("Points", (), {"select": lambda self, group: [BrokenPoint()]})(),
    )

    with pytest.raises(ProviderExtensionError, match="'broken'.*boom"):
        ProviderExtensionRegistry().load_entry_points()
