"""Testes para DeveloperAgent — Sprint 02 do Ciclo01."""
import os
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage

from src.agents.developer import _extract_affected_modules, _read_bounded, MAX_LINES_PER_FILE


# --- Testes de _extract_affected_modules ---

def test_extrai_modulos_simples():
    sprint = """- [ ] **Sprint 1: Algo**
  - **Objetivo:** Fazer algo
  - **Módulos Afetados:** src/core/config.py, src/agents/developer.py
  - **Regra de Validação:** pytest"""
    result = _extract_affected_modules(sprint)
    assert "src/core/config.py" in result
    assert "src/agents/developer.py" in result


def test_extrai_modulos_com_backticks():
    sprint = "**Módulos Afetados:** `src/foo.py`, `src/bar.py`"
    result = _extract_affected_modules(sprint)
    assert "src/foo.py" in result
    assert "src/bar.py" in result


def test_sem_modulos_retorna_lista_vazia():
    sprint = "**Objetivo:** Fazer algo sem módulos afetados declarados."
    assert _extract_affected_modules(sprint) == []


def test_limita_a_tres_arquivos():
    sprint = "**Módulos Afetados:** a.py, b.py, c.py, d.py, e.py"
    result = _extract_affected_modules(sprint)
    assert len(result) <= 3


# --- Testes de _read_bounded ---

def test_read_bounded_trunca(tmp_path):
    f = tmp_path / "big.py"
    f.write_text("\n".join([f"linha {i}" for i in range(MAX_LINES_PER_FILE + 50)]))
    content = _read_bounded(str(f))
    assert f"[truncado em {MAX_LINES_PER_FILE} linhas]" in content
    assert content.count("\n") <= MAX_LINES_PER_FILE + 5


def test_read_bounded_arquivo_inexistente(tmp_path):
    assert _read_bounded(str(tmp_path / "nao_existe.py")) == ""


# --- Testes de DeveloperAgent.execute_sprint ---

@pytest.fixture
def developer(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    with patch("src.agents.developer.LLMFactory") as mock_factory:
        from src.agents.developer import DeveloperAgent
        agent = DeveloperAgent.__new__(DeveloperAgent)
        agent.llm = MagicMock()
        agent.llm.invoke.return_value = AIMessage(content="código gerado")
        agent.role_instruction = "role mock"
        agent.collector = None
        yield agent


def test_injeta_contrato_no_prompt(developer, tmp_path):
    contract = tmp_path / "contract.md"
    contract.write_text("## Endpoints\n| GET | /api/x | — | X |")

    developer.execute_sprint("sprint text", contract_path=str(contract))

    call_args = developer.llm.invoke.call_args[0][0]
    prompt_content = call_args[1].content
    assert "CONTRATO DE API" in prompt_content
    assert "## Endpoints" in prompt_content


def test_contrato_inexistente_levanta_erro(developer, tmp_path):
    with pytest.raises(FileNotFoundError, match="Contrato não encontrado"):
        developer.execute_sprint("sprint text", contract_path="/nao/existe.md")


def test_sem_contrato_nao_quebra(developer):
    result = developer.execute_sprint("sprint text")
    assert result == "código gerado"


def test_injeta_arquivo_existente(developer, tmp_path):
    src = tmp_path / "src"
    src.mkdir()
    (src / "foo.py").write_text("def foo(): pass")

    sprint = f"**Módulos Afetados:** src/foo.py\n**Objetivo:** Atualizar foo"
    developer.execute_sprint(sprint)

    call_args = developer.llm.invoke.call_args[0][0]
    prompt_content = call_args[1].content
    assert "src/foo.py" in prompt_content
    assert "def foo(): pass" in prompt_content


def test_arquivo_afetado_inexistente_nao_quebra(developer):
    sprint = "**Módulos Afetados:** nao/existe.py\n**Objetivo:** Algo"
    result = developer.execute_sprint(sprint)
    assert result == "código gerado"


def test_injeta_feedback_de_erro(developer):
    developer.execute_sprint("sprint text", feedback="erro de lint na linha 42")

    call_args = developer.llm.invoke.call_args[0][0]
    prompt_content = call_args[1].content
    assert "erro de lint na linha 42" in prompt_content
