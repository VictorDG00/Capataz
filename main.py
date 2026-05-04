# main.py
import uuid

from src.agents.graph import create_graph
from src.core.metrics import MetricsCollector


def run_capataz(task_description: str, thread_id: str = None) -> None:
    if not thread_id:
        thread_id = str(uuid.uuid4())

    collector = MetricsCollector(task=task_description, thread_id=thread_id)
    engine = create_graph(collector=collector)

    config = {"configurable": {"thread_id": thread_id}}
    initial_state = {
        "task": task_description,
        "cycle_file": "",
        "contract_path": "",
        "current_sprint": "",
        "latest_output": "",
        "turn_count": 0,
        "integration_failures": 0,
        "status": "pending",
    }

    print(f"🏗️ [CAPATAZ] Iniciando sessão. Thread ID: {thread_id}")

    try:
        for event in engine.stream(initial_state, config):
            for node, state in event.items():
                print(f"📍 Nó finalizado: {node}")
                if node == "architect" and state.get("cycle_file"):
                    collector.cycle_file = state["cycle_file"]
    finally:
        collector.close_session()
        print("📊 [CAPATAZ] Métricas da sessão gravadas em .capataz/logs/")


if __name__ == "__main__":
    print("🛠️ Bem-vindo à Forja de Códigos — O Capataz está pronto.")
    user_task = input("O que vamos construir hoje? ")
    run_capataz(user_task)
