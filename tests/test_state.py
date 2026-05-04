"""Testes para core.state — Sprint 01 do Ciclo03."""
import os
import pytest
from langgraph.checkpoint.sqlite import SqliteSaver


@pytest.fixture(autouse=True)
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def test_cria_diretorio_e_arquivo(tmp_path):
    from src.core.state import get_checkpointer
    cp = get_checkpointer(str(tmp_path / ".capataz" / "state.db"))
    assert os.path.exists(tmp_path / ".capataz" / "state.db")
    assert isinstance(cp, SqliteSaver)


def test_retorna_sqlite_saver():
    from src.core.state import get_checkpointer
    os.makedirs(".capataz", exist_ok=True)
    cp = get_checkpointer(".capataz/state.db")
    assert isinstance(cp, SqliteSaver)


def test_path_customizado(tmp_path):
    from src.core.state import get_checkpointer
    custom = str(tmp_path / "custom" / "my_state.db")
    cp = get_checkpointer(custom)
    assert os.path.exists(custom)
    assert isinstance(cp, SqliteSaver)


def test_create_graph_usa_sqlite_em_disco(tmp_path):
    from src.agents.graph import create_graph
    state_db = str(tmp_path / ".capataz" / "state.db")
    engine = create_graph(state_path=state_db)
    assert engine is not None
    assert os.path.exists(state_db)


def test_create_graph_sem_state_path_usa_memory():
    """Sem state_path, deve usar MemorySaver (sem criar arquivo)."""
    from langgraph.checkpoint.memory import MemorySaver
    from src.agents.graph import create_graph
    engine = create_graph(state_path=None)
    assert engine is not None
    # Não deve criar state.db no diretório atual
    assert not os.path.exists(".capataz/state.db")
