# src/agents/developer.py
from src.core.factory import LLMFactory
from langchain.schema import SystemMessage, HumanMessage
import os

class DeveloperAgent:
    def __init__(self):
        # Solicita o modelo designado para o papel de 'developer'
        self.llm = LLMFactory.get_model("developer")
        
        # Carrega as instruções do cargo
        role_path = ".capataz/roles/developer.md"
        if os.path.exists(role_path):
            with open(role_path, "r") as f:
                self.role_instruction = f.read()
        else:
            self.role_instruction = "# CARGO: DEVELOPER\nAtue como um engenheiro de software."

    def execute_plan(self, plan: str, actlog: str):
        """
        Executa as tarefas técnicas baseadas no plano do Arquiteto.
        """
        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=f"PLANO DE EXECUÇÃO:\n{plan}\n\nHISTÓRICO (ACTLOG):\n{actlog}\n\nEscreva o código necessário.")
        ]
        
        response = self.llm.invoke(prompt)
        return response.content

# Instância pronta para uso no graph.py
developer_agent = DeveloperAgent()