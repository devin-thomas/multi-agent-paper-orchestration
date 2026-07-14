from pathlib import Path

LEGACY_ENTRYPOINT = Path("legacy/project_starter_passing.py")


def test_legacy_entrypoint_uses_standard_openai_configuration() -> None:
    source = LEGACY_ENTRYPOINT.read_text()

    assert "UDACITY_OPENAI_API_KEY" not in source
    assert "openai.vocareum.com" not in source
    assert 'os.getenv("OPENAI_API_KEY")' in source
    assert '"OPENAI_MODEL"' in source
    assert '"BEAVERS_CHOICE_AGENT_MODEL"' in source
