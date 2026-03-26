# main.py
import uuid
from src.agents.graph import capataz_engine

def run_capataz(task_description: str, thread_id: str = None):
    # Se não houver thread_id, criamos uma nova "obra"
    if not thread_id:
        thread_id = str(uuid.uuid4())
    
    config = {"configurable": {"thread_id": thread_id}}
    
    # Estado inicial
    initial_state = {
        "task": task_description,
        "plan": "",
        "actlog": "--- INÍCIO DA FORJA ---",
        "turn_count": 0,
        "status": "pending",
        "latest_output": ""
    }

    print(f"🏗️ [CAPATAZ] Iniciando Turno. ID da Obra: {thread_id}")
    
    # O loop do LangGraph começa aqui
    for event in capataz_engine.stream(initial_state, config):
        for node, state in event.items():
            print(f"📍 Nó finalizado: {node}")
            # Aqui você poderia salvar o state['actlog'] no arquivo físico ACTLOG.md
            with open(".capataz/ACTLOG.md", "a") as f:
                f.write(f"\n\nTurno finalizado no nó: {node}\n")

if __name__ == "__main__":
    print("🛠️ Bem-vindo à Forja de Códigos - O Capataz está pronto.")
    user_task = input("O que vamos construir hoje? ")
    run_capataz(user_task)