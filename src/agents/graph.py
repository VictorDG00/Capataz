import operator
from typing import Annotated, List, TypedDict, Union

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.sqlite import SqliteSaver

# Importamos nossos agentes e segurança
from src.agents.architect import architect_agent # Assumindo que criamos o wrapper do Claude
from src.agents.developer import developer_agent 
from src.core.security import security_manager

# 1. Definição do Estado (O que "viaja" entre as IAs)
class AgentState(TypedDict):
    task: str                   # A Issue original
    plan: str                   # O plano gerado pelo Tech Lead
    actlog: str                 # O conteúdo do arquivo ACTLOG.md
    turn_count: int             # Contador para compactação
    status: str                 # 'success', 'error', 'pending'
    latest_output: str          # Último código ou resposta gerada

# 2. Funções dos Nós (Nodes)
def node_architect(state: AgentState):
    print("🏛️ [CAPATAZ] Tech Lead analisando o estado...")
    # Aqui o Claude lê o ACTLOG e a Task para gerar/atualizar o Plan
    res = architect_agent.plan_task(state["task"], state["actlog"])
    return {
        "plan": res, 
        "turn_count": state["turn_count"] + 1,
        "status": "pending"
    }

def node_developer(state: AgentState):
    print("🏗️ [CAPATAZ] Developer executando o plano...")
    # O Gemini recebe o plano e o contexto e gera o código/relatório
    res = developer_agent.execute_plan(state["plan"], state["actlog"])
    return {
        "latest_output": res,
        "turn_count": state["turn_count"] + 1
    }

def node_validator(state: AgentState):
    print("🛡️ [CAPATAZ] Validando segurança e testes...")
    # Roda Bandit/Ruff via SecurityManager
    scan_result = security_manager.run_security_scan()
    
    if scan_result["status"] == "failed":
        return {"status": "error", "actlog": scan_result["stderr"]}
    return {"status": "success"}

# 3. Lógica de Roteamento (As "Arestas" condicionais)
def should_continue(state: AgentState):
    if state["status"] == "error":
        return "architect" # Volta para o chefe corrigir a vulnerabilidade
    if state["turn_count"] >= 5:
        return "consolidate" # O nó que resumiria o ACTLOG (conforme discutido)
    return END

# 4. Construção do Grafo
def create_graph():
    # Setup da Persistência (Checkpoint)
    memory = SqliteSaver.from_conn_string(":memory:") # Use um path real para persistir após fechar
    
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
            "architect": "architect",
            "consolidate": "architect", # Simplificando: o próprio arch resume
            "end": END
        }
    )

    return workflow.compile(checkpointer=memory)

capataz_engine = create_graph()