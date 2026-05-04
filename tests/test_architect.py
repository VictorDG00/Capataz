"""Testes para ArchitectAgent — Sprint 01 do Ciclo01."""
import os
import pytest
from unittest.mock import MagicMock, patch
from langchain_core.messages import AIMessage


MOCK_RESPONSE = """# Ciclo Teste

- [ ] **Sprint 1: Criar módulo X**
  - **Objetivo:** Criar o módulo X
  - **Módulos Afetados:** core.x
  - **Regra de Validação:** pytest tests/test_x.py

---CONTRACT---

## Endpoints
| Método | Rota     | Request Body | Response     |
|--------|----------|--------------|--------------|
| GET    | /api/x   | —            | { id, name } |

## Tipos Compartilhados
```typescript
interface X { id: string; name: string }
```

## Variáveis de Ambiente
| Variável | Usado em | Descrição    |
|----------|----------|--------------|
| X_URL    | backend  | URL do serviço X |
"""

MOCK_RESPONSE_NO_DELIMITER = """# Ciclo Sem Contrato

- [ ] **Sprint 1: Algo**
  - **Objetivo:** Fazer algo
"""


@pytest.fixture
def architect(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".capataz" / "ciclos").mkdir(parents=True)

    with patch("src.agents.architect.ChatAnthropic"), \
         patch("src.agents.architect.settings"):
        from src.agents.architect import ArchitectAgent
        agent = ArchitectAgent.__new__(ArchitectAgent)
        agent.llm = MagicMock()
        agent.role_instruction = "role mock"
        yield agent


def test_plan_cycle_gera_dois_arquivos(architect, tmp_path):
    architect.llm.invoke.return_value = AIMessage(content=MOCK_RESPONSE)

    cycle_file, contract_file = architect.plan_cycle("tarefa teste")

    assert os.path.exists(cycle_file), "CicloNN.md não foi criado"
    assert os.path.exists(contract_file), "CicloNN_contract.md não foi criado"


def test_ciclo_contem_plano_sem_delimitador(architect, tmp_path):
    architect.llm.invoke.return_value = AIMessage(content=MOCK_RESPONSE)

    cycle_file, _ = architect.plan_cycle("tarefa teste")

    content = open(cycle_file).read()
    assert "---CONTRACT---" not in content, "Delimitador não deve aparecer no ciclo"
    assert "Sprint 1" in content


def test_contract_contem_endpoints(architect, tmp_path):
    architect.llm.invoke.return_value = AIMessage(content=MOCK_RESPONSE)

    _, contract_file = architect.plan_cycle("tarefa teste")

    content = open(contract_file).read()
    assert "Endpoints" in content
    assert "Tipos Compartilhados" in content
    assert "Variáveis de Ambiente" in content


def test_sem_delimitador_nao_quebra(architect, tmp_path):
    """LLM que não usa o delimitador: ciclo gravado, contrato vazio mas arquivo criado."""
    architect.llm.invoke.return_value = AIMessage(content=MOCK_RESPONSE_NO_DELIMITER)

    cycle_file, contract_file = architect.plan_cycle("tarefa sem contrato")

    assert os.path.exists(cycle_file)
    assert os.path.exists(contract_file)
    assert open(contract_file).read() == ""


def test_numeracao_progressiva(architect, tmp_path):
    """Segundo ciclo deve ser Ciclo02, não sobrescrever Ciclo01."""
    architect.llm.invoke.return_value = AIMessage(content=MOCK_RESPONSE)

    cycle1, _ = architect.plan_cycle("primeira tarefa")
    cycle2, _ = architect.plan_cycle("segunda tarefa")

    assert "Ciclo01" in cycle1
    assert "Ciclo02" in cycle2
    assert cycle1 != cycle2
