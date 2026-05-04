"""Testes de instrumentação de métricas nos agentes — Sprint 02 do Ciclo02."""
import os
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage


@pytest.fixture(autouse=True)
def fake_env(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".capataz" / "logs").mkdir(parents=True)


def _make_response(input_tok=100, output_tok=50):
    msg = AIMessage(content="código gerado")
    msg.response_metadata = {"token_usage": {"prompt_tokens": input_tok, "completion_tokens": output_tok}}
    return msg


# --- ArchitectAgent ---

def test_architect_sem_collector_nao_quebra():
    with patch("src.agents.architect.ChatAnthropic") as MockLLM:
        MockLLM.return_value.invoke.return_value = _make_response()
        MockLLM.return_value.invoke.return_value.content = "ciclo\n---CONTRACT---\ncontrato"
        MockLLM.return_value.model = "claude-test"

        from src.agents.architect import ArchitectAgent
        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = MockLLM.return_value
        agent.role_instruction = "role"
        agent.collector = None

        os.makedirs(".capataz/ciclos", exist_ok=True)
        agent.plan_cycle("tarefa")  # não deve levantar exceção


def test_architect_com_collector_registra_chamada(tmp_path):
    from src.core.metrics import MetricsCollector

    collector = MetricsCollector(task="test", thread_id="t1")
    collector.record_call = MagicMock()

    with patch("src.agents.architect.ChatAnthropic") as MockLLM:
        resp = _make_response()
        resp.content = "ciclo\n---CONTRACT---\ncontrato"
        MockLLM.return_value.invoke.return_value = resp
        MockLLM.return_value.model = "claude-test"

        from src.agents.architect import ArchitectAgent
        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = MockLLM.return_value
        agent.role_instruction = "role"
        agent.collector = collector

        os.makedirs(".capataz/ciclos", exist_ok=True)
        agent.plan_cycle("tarefa")

    collector.record_call.assert_called_once()
    args, kwargs = collector.record_call.call_args
    role = kwargs.get("role") or args[0]
    duration = kwargs.get("duration") or args[3]
    assert role == "architect"
    assert duration >= 0


# --- DeveloperAgent ---

def test_developer_sem_collector_nao_quebra():
    with patch("src.agents.developer.LLMFactory") as MockFactory:
        MockFactory.get_model.return_value.invoke.return_value = _make_response()
        MockFactory.get_model.return_value.model_name = "deepseek-chat"

        from src.agents.developer import DeveloperAgent
        agent = DeveloperAgent.__new__(DeveloperAgent)
        agent.llm = MockFactory.get_model.return_value
        agent.role_instruction = "role"
        agent.collector = None

        result = agent.execute_sprint("sprint text")
        assert result is not None


def test_developer_com_collector_registra_chamada(tmp_path):
    from src.core.metrics import MetricsCollector

    collector = MetricsCollector(task="test", thread_id="t2")
    collector.record_call = MagicMock()

    with patch("src.agents.developer.LLMFactory") as MockFactory:
        resp = _make_response()
        MockFactory.get_model.return_value.invoke.return_value = resp
        MockFactory.get_model.return_value.model_name = "deepseek-chat"

        from src.agents.developer import DeveloperAgent
        agent = DeveloperAgent.__new__(DeveloperAgent)
        agent.llm = MockFactory.get_model.return_value
        agent.role_instruction = "role"
        agent.collector = collector

        agent.execute_sprint("sprint text")

    collector.record_call.assert_called_once()
    call_args = collector.record_call.call_args
    role = call_args[1].get("role") or call_args[0][0]
    assert role == "developer"
