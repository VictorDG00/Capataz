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
            self.role_instruction = "# CARGO: DEVELOPER\nAtue como um engenheiro de software focado em segurança e testes."

    def execute_sprint(self, sprint_text: str, feedback: str = None):
        """
        Executa as tarefas técnicas baseadas em um item de Sprint extraído do ciclo.
        Garante que as regras de sprint.md sejam cumpridas.
        Se feedback for fornecido, tenta corrigir o erro relatado.
        """
        sprints_rules = ""
        if os.path.exists("sprints.md"):
            with open("sprints.md", "r") as f:
                sprints_rules = f.read()

        prompt_text = f"""
            Você recebeu uma nova Sprint para executar.

            REGRAS OBRIGATÓRIAS DE ENTREGA (de sprints.md):
            {sprints_rules}

            DADOS DA SPRINT ATUAL:
            {sprint_text}
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
            Sua resposta deve conter os artefatos de código, testes (mockados) e documentação in-code (Docstrings/JSDoc) exigidos.
            Explique brevemente as modificações que fez para cumprir as regras.
        """

        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=prompt_text)
        ]
        
        response = self.llm.invoke(prompt)
        return response.content

developer_agent = DeveloperAgent()
