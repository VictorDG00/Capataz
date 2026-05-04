# src/agents/graph.py
import re
import time
from typing import Optional, TypedDict

from langgraph.graph import StateGraph, END

from src.agents.architect import ArchitectAgent
from src.agents.developer import DeveloperAgent
from src.agents.integrator import IntegratorAgent, integrator_agent
from src.core.config import settings
from src.core.event_bus import EventBus
from src.core.git import git_ops
from src.core.metrics import MetricsCollector
from src.core.runner import test_runner
from src.core.security import security_manager
from src.core.state import get_checkpointer
from src.core.writer import file_writer

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
    files_written: list


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
    if state["status"] == "success":
        # Se há arquivos gravados e git habilitado, abre PR antes de continuar
        if state.get("files_written") and bool(settings.github_token):
            return "git"
        if state.get("current_sprint"):
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

def create_graph(
    collector: Optional[MetricsCollector] = None,
    state_path: Optional[str] = None,
    event_bus: Optional[EventBus] = None,
):
    """
    Constrói e compila o grafo de agentes do Capataz.

    Args:
        collector: MetricsCollector opcional. Quando fornecido, todos os nós
                   registram tokens, custo e tempo de execução. None desativa
                   métricas sem afetar o comportamento do grafo.
        state_path: Caminho do arquivo SQLite de checkpoint. None usa MemorySaver
                    (útil em testes). Qualquer string usa SqliteSaver em disco.
        event_bus: EventBus opcional. Quando fornecido, publica eventos de status
                   em tempo real no Redis para a UI web consumir via SSE.
    """
    architect = ArchitectAgent(collector=collector)
    developer = DeveloperAgent(collector=collector)

    def _node_architect(state: AgentState) -> dict:
        print("🏛️ [CAPATAZ] Tech Lead analisando o projeto e gerando novo Ciclo...")
        if event_bus:
            event_bus.publish("node_start", node="architect", message="Tech Lead planejando o ciclo...")
        cycle_file, contract_path = architect.plan_cycle(state["task"])

        next_sprint = parse_next_sprint(cycle_file)
        if not next_sprint:
            print("⚠️ Nenhuma sprint pendente encontrada no ciclo.")
            return {"status": "error", "cycle_file": cycle_file, "contract_path": contract_path}

        if event_bus:
            event_bus.publish("node_end", node="architect", message="Ciclo e contrato gerados.")
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
        sprint_name = state.get("current_sprint", "").split("\n")[0][:80]
        if event_bus:
            event_bus.publish("node_start", node="developer", sprint_name=sprint_name,
                              message=f"Developer implementando: {sprint_name}")
        feedback = state["latest_output"] if state.get("status") in ("error", "contract_violation") else None

        if collector and state.get("status") in ("error", "contract_violation"):
            collector.record_retry("developer", state.get("latest_output", "")[:120])

        res = developer.execute_sprint(
            sprint_text=state["current_sprint"],
            contract_path=state.get("contract_path"),
            feedback=feedback,
        )

        written = file_writer.write_from_output(res)
        if written:
            print(f"📁 [DEVELOPER] {len(written)} arquivo(s) gravado(s): {written}")

        if event_bus:
            event_bus.publish("node_end", node="developer", sprint_name=sprint_name,
                              message=f"{len(written)} arquivo(s) gravado(s)")
        return {
            "latest_output": res,
            "files_written": written,
            "turn_count": state.get("turn_count", 0) + 1,
            "status": "pending",
        }

    def _node_integrator(state: AgentState) -> dict:
        if event_bus:
            event_bus.publish("node_start", node="integrator", message="Integrator validando contrato...")
        result = node_integrator(state, collector=collector)
        status_msg = "Contrato válido ✅" if result.get("status") == "pending" else f"Violação detectada ❌"
        if event_bus:
            event_bus.publish("node_end", node="integrator", message=status_msg)
        return result

    def _node_validator(state: AgentState) -> dict:
        print("🛡️ [CAPATAZ] Validando testes e segurança da Sprint...")
        if event_bus:
            event_bus.publish("node_start", node="validator", message="Executando testes e SAST...")

        # 1. Executa testes (pytest ou jest) se houver arquivos gravados
        if state.get("files_written"):
            print("🧪 [VALIDATOR] Executando suite de testes...")
            test_result = test_runner.run(runner="pytest", path="tests/")
            if test_result["status"] != "passed":
                print(f"❌ [VALIDATOR] Testes falharam: {test_result['summary']}")
                if collector:
                    collector.record_validator(test_result["duration_seconds"], "failed")
                return {
                    "status": "error",
                    "latest_output": (
                        f"[TESTES FALHARAM]\n{test_result['full_output']}"
                    ),
                }
            print(f"✅ [VALIDATOR] Testes passaram: {test_result['passed']} passed.")
            if collector:
                collector.record_validator(test_result["duration_seconds"], "passed")

        # 2. SAST (Bandit)
        start = time.perf_counter()
        scan_result = security_manager.run_security_scan()
        duration = time.perf_counter() - start

        if collector:
            collector.record_validator(duration, scan_result["status"])

        if scan_result["status"] == "failed":
            print("❌ [CAPATAZ] Falha na validação de segurança (SAST).")
            return {"status": "error", "latest_output": scan_result["stderr"]}

        print("✅ [CAPATAZ] Sprint validada com sucesso! Marcando como concluída.")
        mark_sprint_done(state["cycle_file"], state["current_sprint"])

        if event_bus:
            sprint_name = state.get("current_sprint", "").split("\n")[0][:80]
            event_bus.publish("sprint_done", node="validator", sprint_name=sprint_name,
                              message=f"Sprint concluída ✅")

        next_sprint = parse_next_sprint(state["cycle_file"])
        if next_sprint:
            return {"status": "success", "current_sprint": next_sprint, "integration_failures": 0, "files_written": []}

        print("🎉 [CAPATAZ] Todas as sprints deste ciclo foram concluídas!")
        if event_bus:
            event_bus.publish("cycle_done", node="validator", message="🎉 Ciclo concluído com sucesso!")
        return {"status": "success", "current_sprint": "", "files_written": []}

    # node_git só é adicionado se GITHUB_TOKEN estiver configurado
    git_enabled = bool(settings.github_token)

    def _node_git(state: AgentState) -> dict:
        print("🔀 [GIT] Criando branch, commitando e abrindo PR...")
        sprint_text = state.get("current_sprint", "")
        sprint_name = re.sub(r".*Sprint\s+\d+:\s*\*?\*?", "", sprint_text.split("\n")[0]).strip("* ") or "update"
        sprint_number_match = re.search(r"Sprint\s+(\d+)", sprint_text)
        sprint_num = sprint_number_match.group(1) if sprint_number_match else "?"

        try:
            pr_url = git_ops.run_full_flow(
                sprint_name=sprint_name,
                sprint_number=sprint_num,
                files_written=state.get("files_written", []),
                cycle_file=state.get("cycle_file", ""),
            )
            if pr_url:
                print(f"✅ [GIT] PR aberto: {pr_url}")
        except Exception as e:
            print(f"⚠️ [GIT] Falha ao abrir PR (modo degradado): {e}")

        return {}

    if state_path is not None:
        memory = get_checkpointer(state_path)
    else:
        from langgraph.checkpoint.memory import MemorySaver
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

    if git_enabled:
        workflow.add_node("git", _node_git)
        workflow.add_conditional_edges(
            "validator",
            route_after_validator,
            {"developer": "developer", "git": "git", END: END},
        )
        workflow.add_edge("git", END)
    else:
        workflow.add_conditional_edges(
            "validator",
            route_after_validator,
            {"developer": "developer", END: END},
        )

    return workflow.compile(checkpointer=memory)


capataz_engine = create_graph()
