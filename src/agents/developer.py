# src/agents/developer.py
import os
import re
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage

from src.core.factory import LLMFactory

MAX_LINES_PER_FILE = 200
MAX_FILES_INJECTED = 3


def _extract_affected_modules(sprint_text: str) -> list[str]:
    """Extrai caminhos de arquivo da seção 'Módulos Afetados' da sprint."""
    match = re.search(r"\*\*Módulos Afetados:\*\*\s*(.+?)(?:\n\*\*|\Z)", sprint_text, re.DOTALL)
    if not match:
        return []

    raw = match.group(1).strip()
    # Aceita formatos: `src/foo.py`, src/foo.py, foo, separados por vírgula ou newline
    tokens = re.split(r"[,\n]+", raw)
    paths = []
    for token in tokens:
        token = token.strip().strip("`").strip()
        if token and not token.startswith("#"):
            paths.append(token)
    return paths[:MAX_FILES_INJECTED]


def _read_bounded(path: str) -> str:
    """Lê um arquivo limitando a MAX_LINES_PER_FILE linhas."""
    if not os.path.exists(path):
        return ""
    with open(path, "r", encoding="utf-8", errors="replace") as f:
        lines = f.readlines()
    if len(lines) > MAX_LINES_PER_FILE:
        lines = lines[:MAX_LINES_PER_FILE]
        lines.append(f"\n# [truncado em {MAX_LINES_PER_FILE} linhas]\n")
    return "".join(lines)


class DeveloperAgent:
    def __init__(self):
        self.llm = LLMFactory.get_model("developer")

        role_path = ".capataz/roles/developer.md"
        if os.path.exists(role_path):
            with open(role_path, "r") as f:
                self.role_instruction = f.read()
        else:
            self.role_instruction = "# CARGO: DEVELOPER\nAtue como um engenheiro de software focado em segurança e testes."

    def execute_sprint(
        self,
        sprint_text: str,
        contract_path: Optional[str] = None,
        feedback: Optional[str] = None,
    ) -> str:
        """
        Executa as tarefas técnicas de uma sprint.

        Injeta no prompt:
        - Regras de sprints.md
        - Contrato de API do ciclo (contract_path), se existir
        - Conteúdo atual dos arquivos listados em 'Módulos Afetados' (bounded a
          MAX_LINES_PER_FILE linhas por arquivo, máx. MAX_FILES_INJECTED arquivos)
        - Feedback de erro da validação anterior, se houver
        """
        sprints_rules = ""
        if os.path.exists("sprints.md"):
            with open("sprints.md", "r") as f:
                sprints_rules = f.read()

        contract_block = ""
        if contract_path:
            if not os.path.exists(contract_path):
                raise FileNotFoundError(
                    f"Contrato não encontrado: {contract_path}. "
                    "Execute o Arquiteto antes do Developer."
                )
            with open(contract_path, "r") as f:
                contract_block = f.read()

        affected_files = _extract_affected_modules(sprint_text)
        existing_files_block = ""
        for path in affected_files:
            content = _read_bounded(path)
            if content:
                existing_files_block += f"\n### {path}\n```\n{content}\n```\n"

        prompt_text = f"""Você recebeu uma nova Sprint para executar.

REGRAS OBRIGATÓRIAS DE ENTREGA (de sprints.md):
{sprints_rules}

DADOS DA SPRINT ATUAL:
{sprint_text}
"""

        if contract_block:
            prompt_text += f"""
CONTRATO DE API (fonte de verdade — não viole):
{contract_block}
"""

        if existing_files_block:
            prompt_text += f"""
CÓDIGO ATUAL DOS MÓDULOS AFETADOS (leia antes de escrever):
{existing_files_block}
"""

        if feedback:
            prompt_text += f"""
ATENÇÃO: A tentativa anterior falhou na validação.
MENSAGEM DE ERRO / FEEDBACK DA VALIDAÇÃO:
{feedback}

Por favor, corrija o código para resolver este erro.
"""

        prompt_text += """
Com base no objetivo da sprint, regra de validação e módulos afetados, escreva/atualize o código necessário.
Sua resposta deve conter os artefatos de código, testes (mockados) e documentação in-code exigidos.
Explique brevemente as modificações realizadas.
"""

        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=prompt_text),
        ]

        response = self.llm.invoke(prompt)
        return response.content


developer_agent = DeveloperAgent()
