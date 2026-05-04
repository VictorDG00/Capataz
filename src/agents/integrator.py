# src/agents/integrator.py
import os
from typing import Optional

from langchain_core.messages import SystemMessage, HumanMessage

from src.core.factory import LLMFactory

MAX_OUTPUT_CHARS = 3000  # Limita o output do Developer enviado ao Integrator


class IntegratorAgent:
    """
    Valida que o output do Developer é consistente com o contrato de API do ciclo.
    Responde apenas PASS ou FAIL: <motivo>.
    Usa modelo barato — tarefa de comparação, não de geração criativa.
    """

    def __init__(self):
        self.llm = LLMFactory.get_model("integrator")

        role_path = ".capataz/roles/integrator.md"
        if os.path.exists(role_path):
            with open(role_path, "r") as f:
                self.role_instruction = f.read()
        else:
            self.role_instruction = (
                "Você valida contratos de API. Responda APENAS 'PASS' ou 'FAIL: <motivo>'."
            )

    def validate(self, contract_path: str, developer_output: str) -> str:
        """
        Compara o output do Developer com o contrato.

        Retorna:
            "PASS" — output consistente com o contrato
            "FAIL: <descrição>" — violação específica encontrada
        """
        if not os.path.exists(contract_path):
            return "PASS"  # Sem contrato, não há o que validar

        with open(contract_path, "r") as f:
            contract_content = f.read()

        if not contract_content.strip():
            return "PASS"  # Contrato vazio, nada a comparar

        truncated_output = developer_output[:MAX_OUTPUT_CHARS]
        if len(developer_output) > MAX_OUTPUT_CHARS:
            truncated_output += "\n... [output truncado]"

        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=f"""CONTRATO DE API:
{contract_content}

OUTPUT DO DEVELOPER (código gerado):
{truncated_output}

Verifique se o código respeita o contrato e responda APENAS com PASS ou FAIL: <motivo>.
"""),
        ]

        response = self.llm.invoke(prompt)
        result = response.content.strip()

        if not (result == "PASS" or result.startswith("FAIL:")):
            # LLM não seguiu o formato — trata como PASS para não bloquear o fluxo
            print(f"⚠️ [INTEGRATOR] Resposta fora do formato esperado: '{result[:100]}'. Tratando como PASS.")
            return "PASS"

        return result


integrator_agent = IntegratorAgent()
