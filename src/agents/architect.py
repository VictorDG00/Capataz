# src/agents/architect.py
import os
import glob
import time
from typing import Optional

from langchain_anthropic import ChatAnthropic
from langchain_core.messages import SystemMessage, HumanMessage

from src.core.config import settings
from src.core.metrics import MetricsCollector

CONTRACT_DELIMITER = "---CONTRACT---"


def _get_model_name(llm) -> str:
    return getattr(llm, "model_name", None) or getattr(llm, "model", "unknown")


class ArchitectAgent:
    def __init__(self, collector: Optional[MetricsCollector] = None):
        """
        Args:
            collector: MetricsCollector injetado pelo grafo. None desativa métricas.
        """
        self.collector = collector
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            anthropic_api_key=settings.anthropic_api_key.get_secret_value(),
            temperature=0.1,
        )

        role_path = ".capataz/roles/tech_lead.md"
        if os.path.exists(role_path):
            with open(role_path, "r") as f:
                self.role_instruction = f.read()
        else:
            self.role_instruction = "Você é o arquiteto responsável por traçar o plano de execução do projeto."

    def _get_next_cycle_number(self) -> str:
        """Retorna o próximo número de ciclo formatado (ex: '04')."""
        files = glob.glob(".capataz/ciclos/Ciclo*.md")
        if not files:
            return "01"

        max_num = 0
        for f in files:
            basename = os.path.basename(f)
            num_part = basename.replace("Ciclo", "").replace(".md", "")
            try:
                num = int(num_part)
                if num > max_num:
                    max_num = num
            except ValueError:
                pass

        return f"{max_num + 1:02d}"

    def _split_response(self, content: str) -> tuple[str, str]:
        """
        Divide o output do LLM em (ciclo_md, contract_md) usando o delimitador fixo.
        Se o delimitador não estiver presente, retorna o conteúdo completo como ciclo
        e um contrato vazio para não quebrar o fluxo.
        """
        if CONTRACT_DELIMITER in content:
            parts = content.split(CONTRACT_DELIMITER, 1)
            return parts[0].strip(), parts[1].strip()
        return content.strip(), ""

    def plan_cycle(self, task: str) -> tuple[str, str]:
        """
        Lê projeto.md e sprints.md e gera em uma única chamada LLM:
        - CicloNN.md: plano de sprints
        - CicloNN_contract.md: contrato de API (endpoints, tipos, env vars)

        Retorna (cycle_filename, contract_filename).
        """
        projeto_content = ""
        if os.path.exists("projeto.md"):
            with open("projeto.md", "r") as f:
                projeto_content = f.read()

        sprints_content = ""
        if os.path.exists("sprints.md"):
            with open("sprints.md", "r") as f:
                sprints_content = f.read()

        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=f"""
Você é o arquiteto responsável por traçar o plano de execução do projeto.
Sua tarefa é criar um novo ciclo E o contrato de API correspondente.

DEMANDA ATUAL: {task}

Fontes de Verdade:
1. projeto.md:
{projeto_content}

2. sprints.md:
{sprints_content}

INSTRUÇÕES DE RESPOSTA:
Sua resposta deve conter DUAS seções separadas pelo delimitador exato `{CONTRACT_DELIMITER}`.

SEÇÃO 1 — Plano do Ciclo (antes do delimitador):
- Cabeçalho com objetivo geral do ciclo.
- Lista de Sprints em formato checklist (`- [ ] **Sprint X: ...**`).
- Para cada Sprint: Objetivo, Módulos Afetados, Regra de Validação.
- Ordem cronológica lógica, sem dependências cruzadas não declaradas.

{CONTRACT_DELIMITER}

SEÇÃO 2 — Contrato de API (após o delimitador, MÁXIMO 60 linhas):
Use exatamente esta estrutura:

## Endpoints
| Método | Rota | Request Body | Response |
|--------|------|--------------|----------|
| ...    | ...  | ...          | ...      |

## Tipos Compartilhados
```typescript
// interfaces TypeScript ou dataclasses Python compartilhadas entre front e back
```

## Variáveis de Ambiente
| Variável | Usado em | Descrição |
|----------|----------|-----------|
| ...      | ...      | ...       |

Responda APENAS com o conteúdo das duas seções. Sem introduções ou explicações externas.
"""),
        ]

        start = time.perf_counter()
        response = self.llm.invoke(prompt)
        duration = time.perf_counter() - start

        if self.collector:
            self.collector.record_call("architect", _get_model_name(self.llm), response, duration)

        cycle_content, contract_content = self._split_response(response.content)

        cycle_num = self._get_next_cycle_number()
        os.makedirs(".capataz/ciclos", exist_ok=True)

        cycle_filename = f".capataz/ciclos/Ciclo{cycle_num}.md"
        with open(cycle_filename, "w") as f:
            f.write(cycle_content)

        contract_filename = f".capataz/ciclos/Ciclo{cycle_num}_contract.md"
        with open(contract_filename, "w") as f:
            f.write(contract_content)

        print(f"🏛️ [CAPATAZ] Ciclo gerado: {cycle_filename}")
        print(f"📋 [CAPATAZ] Contrato gerado: {contract_filename}")
        return cycle_filename, contract_filename


architect_agent = ArchitectAgent()
