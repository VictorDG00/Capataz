import re
import operator
from typing import Annotated, List, TypedDict, Union, Optional

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Importamos nossos agentes e segurança
from src.agents.architect import architect_agent
from src.agents.developer import developer_agent 
from src.core.security import security_manager

# 1. Definição do Estado
class AgentState(TypedDict):
    task: str                   # A demanda principal
    cycle_file: str             # O caminho do arquivo CicloNN.md gerado pelo Architect
    current_sprint: str         # O conteúdo da sprint atual sendo trabalhada
    status: str                 # 'success', 'error', 'pending'
    latest_output: str          # Último código ou resposta gerada
    turn_count: int             # Contador

def parse_next_sprint(cycle_path: str) -> Optional[str]:
    """Lê o CicloNN.md e extrai a próxima sprint pendente [ ]."""
    try:
        with open(cycle_path, "r") as f:
            content = f.read()

        # Procura por linhas começando com "- [ ] Sprint" ou similar
        # e pega o bloco até a próxima sprint ou fim do arquivo
        sprints = re.split(r'(?=\n\s*-\s*\[\s*[ xX]\s*\].+)', content)

        for block in sprints:
            if re.search(r'-\s*\[\s*\]', block):
                return block.strip()
    except Exception as e:
        print(f"Erro ao ler arquivo de ciclo: {e}")
    return None

def mark_sprint_done(cycle_path: str, sprint_text: str):
    """Atualiza o arquivo de ciclo marcando a sprint atual como [x]."""
    try:
        with open(cycle_path, "r") as f:
            content = f.read()

        # Extrai a primeira linha da sprint (ex: "- [ ] Sprint 1: ...")
        first_line = sprint_text.split('\n')[0].strip()
        # Vamos fazer um replace simples no arquivo
        new_line = first_line.replace("[ ]", "[x]")

        new_content = content.replace(first_line, new_line)

        with open(cycle_path, "w") as f:
            f.write(new_content)
    except Exception as e:
        print(f"Erro ao atualizar arquivo de ciclo: {e}")

# 2. Funções dos Nós (Nodes)
def node_architect(state: AgentState):
    print("🏛️ [CAPATAZ] Tech Lead analisando o projeto e gerando novo Ciclo...")
    # O Claude lê projeto.md e sprints.md e gera o CicloNN.md
    cycle_file = architect_agent.plan_cycle(state["task"])

    # Extrai a primeira sprint pendente
    next_sprint = parse_next_sprint(cycle_file)
    if not next_sprint:
        print("⚠️ Nenhuma sprint pendente encontrada no ciclo.")
        return {"status": "error", "cycle_file": cycle_file}

    return {
        "cycle_file": cycle_file,
        "current_sprint": next_sprint,
        "turn_count": state.get("turn_count", 0) + 1,
        "status": "pending"
    }

def node_developer(state: AgentState):
    print("🏗️ [CAPATAZ] Developer executando a Sprint atual...")

    # Se viemos de um erro, passamos o feedback para correção
    feedback = state["latest_output"] if state.get("status") == "error" else None

    # O Gemini recebe a sprint atual e escreve o código
    res = developer_agent.execute_sprint(state["current_sprint"], feedback=feedback)
    return {
        "latest_output": res,
        "turn_count": state.get("turn_count", 0) + 1,
        "status": "pending" # Reseta o status para pending após execução
    }

def node_validator(state: AgentState):
    print("🛡️ [CAPATAZ] Validando segurança e testes da Sprint...")
    # Roda Bandit/Ruff via SecurityManager
    scan_result = security_manager.run_security_scan()
    
    if scan_result["status"] == "failed":
        print("❌ [CAPATAZ] Falha na validação de segurança/testes.")
        # Retorna o erro para que o developer possa tentar consertar
        return {"status": "error", "latest_output": scan_result["stderr"]}

    print("✅ [CAPATAZ] Sprint validada com sucesso! Marcando como concluída.")
    mark_sprint_done(state["cycle_file"], state["current_sprint"])

    # Prepara a próxima sprint se houver
    next_sprint = parse_next_sprint(state["cycle_file"])

    if next_sprint:
         return {"status": "success", "current_sprint": next_sprint}
    else:
         print("🎉 [CAPATAZ] Todas as sprints deste ciclo foram concluídas!")
         return {"status": "success", "current_sprint": ""}

# 3. Lógica de Roteamento (As "Arestas" condicionais)
def should_continue(state: AgentState):
    if state.get("turn_count", 0) >= 15:
        print("⚠️ [CAPATAZ] Limite de tentativas (turn count) excedido. Interrompendo para evitar loop infinito.")
        return END

    if state["status"] == "error":
        # Se houve erro na validação, volta pro developer tentar arrumar o código
        return "developer"

    if state["status"] == "success" and state.get("current_sprint"):
        # Se validou com sucesso e tem mais sprint, continua no developer
        return "developer"

    # Se validou e não tem mais sprint, acaba
    return END

# 4. Construção do Grafo
def create_graph():
    # Setup da Persistência (Checkpoint)
    memory = SqliteSaver.from_conn_string(":memory:")
    
    workflow = StateGraph(AgentState)

    # Adiciona os nós
    workflow.add_node("architect", node_architect)
    workflow.add_node("developer", node_developer)
    workflow.add_node("validator", node_validator)

    # Define o fluxo
    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "validator")
    
    # Define a decisão de loop
    workflow.add_conditional_edges(
        "validator",
        should_continue,
        {
            "developer": "developer",
            "end": END
        }
    )

    return workflow.compile(checkpointer=memory)

capataz_engine = create_graph()
