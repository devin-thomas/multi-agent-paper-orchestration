# Provider Extensions

The four profiles in `model-providers.toml` are first-class, verified adapters. Additional
providers can be added without editing `paper_orchestration.providers.factory` by publishing a
Python entry point in the `paper_orchestration.providers` group:

```toml
[project.entry-points."paper_orchestration.providers"]
acme = "acme_paper_provider:build_adapter"
```

The builder receives `(model, profile)` and returns an object implementing `ProviderAdapter`:
it must expose matching `provider` and `model` strings, return `ModelCapabilities` from
`capabilities()`, and return the Pydantic AI model from `create_model()`. Extension providers are
trusted Python code: installing one grants it the same process and credential access as the app.

Use `ProviderExtensionRegistry` for tests or applications that need explicit registration. The
`register_reference_adapter` helper adds an offline `reference` provider, and
`assert_adapter_conformance(adapter)` is a reusable test assertion for third-party adapters.
Duplicate names, broken entry points, mismatched adapter identity, and missing required
capabilities fail with actionable errors. Extensions are reported as compatible providers; they
are not included in the verified first-class provider set.
