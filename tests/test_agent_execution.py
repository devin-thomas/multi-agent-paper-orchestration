from types import SimpleNamespace

from paper_orchestration.agents.intake import IntakeAgent, IntakeResult


class FakeFrameworkAgent:
    def __init__(self, output: IntakeResult) -> None:
        self.output = output
        self.prompts: list[str] = []
        self.tools: list[object] = []

    def tool(self, function: object) -> object:
        self.tools.append(function)
        return function

    def run_sync(self, prompt: str) -> SimpleNamespace:
        self.prompts.append(prompt)
        return SimpleNamespace(output=self.output)


def test_intake_agent_registers_tools_and_executes_framework_run(monkeypatch) -> None:
    framework_agent = FakeFrameworkAgent(
        IntakeResult(
            request_date="2025-01-01",
            requested_delivery_date="2025-01-15",
            firm_order=False,
            items=[],
        )
    )

    monkeypatch.setattr(
        "paper_orchestration.agents.intake.make_framework_agent",
        lambda name, prompt, output_type: framework_agent,
    )

    agent = IntakeAgent()
    result = agent.run_intake("Please quote 100 sheets of A4 paper.", "2025-01-01")

    assert result is framework_agent.output
    assert len(framework_agent.tools) == 4
    assert len(framework_agent.prompts) == 1

    parse_delivery_date = framework_agent.tools[0]
    assert callable(parse_delivery_date)
    assert (
        parse_delivery_date(None, "Delivery on January 10, 2025.", "2025-01-01") == "2025-01-10"
    )
    assert agent.tool_audit[0].format() == (
        "IntakeAgent.parse_delivery_date: request_date=2025-01-01"
    )
