# src/agents/graph.py
import re
import time
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.agents.architect import ArchitectAgent
from src.agents.developer import DeveloperAgent
from src.agents.integrator import IntegratorAgent, integrator_agent
from src.core.metrics import MetricsCollector
from src.core.security import security_manager

MAX_INTEGRATION_FAILURES = 2


# 1. Estado do grafo

class AgentState(TypedDict):
    task: str
    cycle_file: str
    contract_path: str
    current_sprint: str
    status: str                 # 'pending' | 'success' | 'error' | 'contract_violation'
    latest_output: str
    turn_count: int
    integration_failures: int


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


# 3. Roteamento (module-level — puro, sem dependência de collector)

def route_after_integrator(state: AgentState) -> str:
    """PASS → validator | violação → developer | escala → architect."""
    if state["status"] == "pending":
        return "validator"
    if state["status"] == "contract_violation":
        return "developer"
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


# 4. Nó do integrator (module-level para ser patchável nos testes)

def node_integrator(state: AgentState, collector: Optional[MetricsCollector] = None) -> dict:
    print("🔍 [CAPATAZ] Integrator validando consistência com o contrato...")
    contract_path = state.get("contract_path", "")
    result = integrator_agent.validate(contract_path, state["latest_output"])

    if result == "PASS":
        print("✅ [INTEGRATOR] Contrato respeitado.")
        return {"status": "pending", "integration_failures": 0}

    failures = state.get("integration_failures", 0) + 1
    print(f"❌ [INTEGRATOR] Violação ({failures}/{MAX_INTEGRATION_FAILURES}): {result}")

    if collector:
        collector.record_retry("integrator", result[:120])

    if failures >= MAX_INTEGRATION_FAILURES:
        print("🔁 [INTEGRATOR] Limite de violações — escalando para o Arquiteto.")
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


# 5. Construção do grafo com injeção de collector

def create_graph(collector: Optional[MetricsCollector] = None):
    """
    Constrói e compila o grafo de agentes do Capataz.

    Args:
        collector: MetricsCollector opcional. Quando fornecido, todos os nós
                   registram tokens, custo e tempo de execução. None desativa
                   métricas sem afetar o comportamento do grafo.
    """
    architect = ArchitectAgent(collector=collector)
    developer = DeveloperAgent(collector=collector)

    def _node_architect(state: AgentState) -> dict:
        print("🏛️ [CAPATAZ] Tech Lead analisando o projeto e gerando novo Ciclo...")
        cycle_file, contract_path = architect.plan_cycle(state["task"])

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

    def _node_developer(state: AgentState) -> dict:
        print("🏗️ [CAPATAZ] Developer executando a Sprint atual...")
        feedback = state["latest_output"] if state.get("status") in ("error", "contract_violation") else None

        if collector and state.get("status") in ("error", "contract_violation"):
            collector.record_retry("developer", state.get("latest_output", "")[:120])

        res = developer.execute_sprint(
            sprint_text=state["current_sprint"],
            contract_path=state.get("contract_path"),
            feedback=feedback,
        )
        return {
            "latest_output": res,
            "turn_count": state.get("turn_count", 0) + 1,
            "status": "pending",
        }

    def _node_integrator(state: AgentState) -> dict:
        return node_integrator(state, collector=collector)

    def _node_validator(state: AgentState) -> dict:
        print("🛡️ [CAPATAZ] Validando segurança e testes da Sprint...")
        start = time.perf_counter()
        scan_result = security_manager.run_security_scan()
        duration = time.perf_counter() - start

        if collector:
            collector.record_validator(duration, scan_result["status"])

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

    memory = MemorySaver()
    workflow = StateGraph(AgentState)

    workflow.add_node("architect", _node_architect)
    workflow.add_node("developer", _node_developer)
    workflow.add_node("integrator", _node_integrator)
    workflow.add_node("validator", _node_validator)

    workflow.set_entry_point("architect")
    workflow.add_edge("architect", "developer")
    workflow.add_edge("developer", "integrator")

    workflow.add_conditional_edges(
        "integrator",
        route_after_integrator,
        {"validator": "validator", "developer": "developer", "architect": "architect"},
    )
    workflow.add_conditional_edges(
        "validator",
        route_after_validator,
        {"developer": "developer", END: END},
    )

    return workflow.compile(checkpointer=memory)


capataz_engine = create_graph()
