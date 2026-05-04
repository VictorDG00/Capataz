# src/core/state.py
import os
import sqlite3

from langgraph.checkpoint.sqlite import SqliteSaver

_DEFAULT_STATE_PATH = ".capataz/state.db"


def get_checkpointer(state_path: str = _DEFAULT_STATE_PATH) -> SqliteSaver:
    """
    Retorna um SqliteSaver com checkpoint persistente em disco.

    Usa conexão sqlite3 direta (não context manager) para que o checkpointer
    viva durante toda a sessão do processo sem precisar de um bloco `with`.
    O diretório é criado automaticamente se não existir.

    Usar disco em vez de :memory: garante que o grafo retome de onde parou
    após qualquer reinicialização do processo.

    Args:
        state_path: Caminho para o arquivo SQLite. Padrão: .capataz/state.db

    Returns:
        SqliteSaver configurado para persistência em disco.
    """
    os.makedirs(os.path.dirname(state_path), exist_ok=True)
    conn = sqlite3.connect(state_path, check_same_thread=False)
    checkpointer = SqliteSaver(conn=conn)
    checkpointer.setup()
    return checkpointer
