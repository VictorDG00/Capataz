"""Testes para IntegratorAgent e roteamento do grafo — Sprint 03 do Ciclo01."""
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage


# --- Testes do IntegratorAgent ---

@pytest.fixture
def integrator(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("src.agents.integrator.LLMFactory"):
        from src.agents.integrator import IntegratorAgent
        agent = IntegratorAgent.__new__(IntegratorAgent)
        agent.llm = MagicMock()
        agent.role_instruction = "role mock"
        yield agent, tmp_path


def test_pass_quando_contrato_ausente(integrator):
    agent, _ = integrator
    result = agent.validate("/nao/existe.md", "código qualquer")
    assert result == "PASS"


def test_pass_quando_contrato_vazio(integrator):
    agent, tmp_path = integrator
    contract = tmp_path / "contract.md"
    contract.write_text("")
    result = agent.validate(str(contract), "código qualquer")
    assert result == "PASS"


def test_retorna_pass_do_llm(integrator):
    agent, tmp_path = integrator
    contract = tmp_path / "contract.md"
    contract.write_text("## Endpoints\n| GET | /api/x | — | X |")
    agent.llm.invoke.return_value = AIMessage(content="PASS")

    result = agent.validate(str(contract), "código que respeita o contrato")
    assert result == "PASS"


def test_retorna_fail_do_llm(integrator):
    agent, tmp_path = integrator
    contract = tmp_path / "contract.md"
    contract.write_text("## Endpoints\n| GET | /api/x | — | X |")
    agent.llm.invoke.return_value = AIMessage(content="FAIL: Rota /api/y não existe no contrato")

    result = agent.validate(str(contract), "código que chama /api/y")
    assert result.startswith("FAIL:")
    assert "/api/y" in result


def test_formato_invalido_trata_como_pass(integrator, capsys):
    agent, tmp_path = integrator
    contract = tmp_path / "contract.md"
    contract.write_text("## Endpoints\n| GET | /api/x | — | X |")
    agent.llm.invoke.return_value = AIMessage(content="Parece que o código está ok.")

    result = agent.validate(str(contract), "código")
    assert result == "PASS"
    captured = capsys.readouterr()
    assert "fora do formato esperado" in captured.out


# --- Testes de roteamento do grafo ---

def test_route_after_integrator_pass():
    from src.agents.graph import route_after_integrator
    state = {"status": "pending", "integration_failures": 0}
    assert route_after_integrator(state) == "validator"


def test_route_after_integrator_contract_violation():
    from src.agents.graph import route_after_integrator
    state = {"status": "contract_violation", "integration_failures": 1}
    assert route_after_integrator(state) == "developer"


def test_route_after_integrator_escalada_arquiteto():
    from src.agents.graph import route_after_integrator
    state = {"status": "error", "integration_failures": 2}
    assert route_after_integrator(state) == "architect"


def test_node_integrator_incrementa_falhas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    contract = tmp_path / "contract.md"
    contract.write_text("## Endpoints\n| GET | /api/x | — | X |")

    with patch("src.agents.graph.integrator_agent") as mock_integrator:
        mock_integrator.validate.return_value = "FAIL: rota errada"
        from src.agents.graph import node_integrator

        state = {
            "contract_path": str(contract),
            "latest_output": "código gerado",
            "integration_failures": 0,
        }
        result = node_integrator(state)

    assert result["integration_failures"] == 1
    assert result["status"] == "contract_violation"


def test_node_integrator_escala_apos_max_falhas(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    contract = tmp_path / "contract.md"
    contract.write_text("## Endpoints\n| GET | /api/x | — | X |")

    with patch("src.agents.graph.integrator_agent") as mock_integrator:
        mock_integrator.validate.return_value = "FAIL: rota errada"
        from src.agents.graph import node_integrator

        state = {
            "contract_path": str(contract),
            "latest_output": "código gerado",
            "integration_failures": 1,  # já está na 1, próximo será o 2 (MAX)
        }
        result = node_integrator(state)

    assert result["status"] == "error"
    assert "ESCALANDO" in result["latest_output"] or "ESCALA" in result["latest_output"]
