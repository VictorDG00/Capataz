# src/agents/graph.py
import re
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.architect import architect_agent
from src.agents.developer import developer_agent
from src.agents.integrator import integrator_agent
from src.core.security import security_manager

MAX_INTEGRATION_FAILURES = 2  # FAILs consecutivos antes de escalar para o Arquiteto


# 1. Estado do grafo

class AgentState(TypedDict):
    task: str
    cycle_file: str
    contract_path: str          # Caminho do CicloNN_contract.md gerado pelo Arquiteto
    current_sprint: str
    status: str                 # 'pending' | 'success' | 'error' | 'contract_violation'
    latest_output: str
    turn_count: int
    integration_failures: int   # Contador de FAILs consecutivos do Integrator


# 2. Helpers de ciclo

def parse_next_sprint(cycle_path: str) -> Optional[str]:
    """Lê o CicloNN.md e extrai a próxima sprint pendente [ ]."""
    try:
        with open(cycle_path, "r") as f:
            content = f.read()
        sprints = re.split(r'(?=\n\s*-\s*\[\s*[ xX]\s*\].+)', content)
        for block in sprints:
            if re.search(r'-\s*\[\s*\]', block):
                return block.strip()
    except Exception as e:
        print(f"Erro ao ler arquivo de ciclo: {e}")
    return None


def mark_sprint_done(cycle_path: str, sprint_text: str):
    """Marca a sprint atual como [x] no arquivo de ciclo."""
    try:
        with open(cycle_path, "r") as f:
            content = f.read()
        first_line = sprint_text.split('\n')[0].strip()
        new_content = content.replace(first_line, first_line.replace("[ ]", "[x]"))
        with open(cycle_path, "w") as f:
            f.write(new_content)
    except Exception as e:
        print(f"Erro ao atualizar arquivo de ciclo: {e}")


# 3. Nós do grafo

def node_architect(state: AgentState) -> dict:
    print("🏛️ [CAPATAZ] Tech Lead analisando o projeto e gerando novo Ciclo...")
    cycle_file, contract_path = architect_agent.plan_cycle(state["task"])

    next_sprint = parse_next_sprint(cycle_file)
    if not next_sprint:
        print("⚠️ Nenhuma sprint pendente encontrada no ciclo.")
        return {"status": "error", "cycle_file": cycle_file, "contract_path": contract_path}

    return {
        "cycle_file": cycle_file,
        "contract_path": contract_path,
        "current_sprint": next_sprint,
        "turn_count": state.get("turn_count", 0) + 1,
        "integration_failures": 0,
        "status": "pending",
    }


def node_developer(state: AgentState) -> dict:
    print("🏗️ [CAPATAZ] Developer executando a Sprint atual...")

    feedback = state["latest_output"] if state.get("status") in ("error", "contract_violation") else None

    res = developer_agent.execute_sprint(
        sprint_text=state["current_sprint"],
        contract_path=state.get("contract_path"),
        feedback=feedback,
    )
    return {
        "latest_output": res,
        "turn_count": state.get("turn_count", 0) + 1,
        "status": "pending",
    }


def node_integrator(state: AgentState) -> dict:
    print("🔍 [CAPATAZ] Integrator validando consistência com o contrato...")
    contract_path = state.get("contract_path", "")
    result = integrator_agent.validate(contract_path, state["latest_output"])

    if result == "PASS":
        print("✅ [INTEGRATOR] Contrato respeitado.")
        return {"status": "pending", "integration_failures": 0}

    failures = state.get("integration_failures", 0) + 1
    print(f"❌ [INTEGRATOR] Violação ({failures}/{MAX_INTEGRATION_FAILURES}): {result}")

    if failures >= MAX_INTEGRATION_FAILURES:
        print("🔁 [INTEGRATOR] Limite de violações atingido — escalando para o Arquiteto.")
        return {
            "status": "error",
            "latest_output": f"[INTEGRATOR ESCALA PARA ARQUITETO]\n{result}",
            "integration_failures": failures,
        }

    return {
        "status": "contract_violation",
        "latest_output": result,
        "integration_failures": failures,
    }


def node_validator(state: AgentState) -> dict:
    print("🛡️ [CAPATAZ] Validando segurança e testes da Sprint...")
    scan_result = security_manager.run_security_scan()

    if scan_result["status"] == "failed":
        print("❌ [CAPATAZ] Falha na validação de segurança/testes.")
        return {"status": "error", "latest_output": scan_result["stderr"]}

    print("✅ [CAPATAZ] Sprint validada com sucesso! Marcando como concluída.")
    mark_sprint_done(state["cycle_file"], state["current_sprint"])

    next_sprint = parse_next_sprint(state["cycle_file"])
    if next_sprint:
        return {"status": "success", "current_sprint": next_sprint, "integration_failures": 0}

    print("🎉 [CAPATAZ] Todas as sprints deste ciclo foram concluídas!")
    return {"status": "success", "current_sprint": ""}


# 4. Roteamento

def route_after_integrator(state: AgentState) -> str:
    """PASS → validator | violação → developer | escala → architect."""
    if state["status"] == "pending":
        return "validator"
    if state["status"] == "contract_violation":
        return "developer"
    # status == "error" com integration_failures >= MAX → Arquiteto revisa
    return "architect"


def route_after_validator(state: AgentState) -> str:
    if state.get("turn_count", 0) >= 15:
        print("⚠️ [CAPATAZ] Limite de turn_count atingido.")
        return END

    if state["status"] == "error":
        return "developer"

    if state["status"] == "success" and state.get("current_sprint"):
        return "developer"

    return END


# 5. Construção do grafo

def create_graph():
    memory = MemorySaver()
    workflow = StateGraph(AgentState)

    workflow.add_node("architect", node_architect)
    workflow.add_node("developer", node_developer)
    workflow.add_node("integrator", node_integrator)
    workflow.add_node("validator", node_validator)

    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "integrator")

    workflow.add_conditional_edges(
        "integrator",
        route_after_integrator,
        {
            "validator": "validator",
            "developer": "developer",
            "architect": "architect",
        },
    )

    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {
            "developer": "developer",
            END: END,
        },
    )

    return workflow.compile(checkpointer=memory)


capataz_engine = create_graph()
