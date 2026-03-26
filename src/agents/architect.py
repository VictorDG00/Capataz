# src/agents/architect.py
from langchain_anthropic import ChatAnthropic
from langchain.schema import SystemMessage, HumanMessage
from src.core.config import settings

class ArchitectAgent:
    def __init__(self):
        # Inicializa o Claude 3.5 Sonnet
        self.llm = ChatAnthropic(
            model="claude-3-5-sonnet-20240620",
            anthropic_api_key=settings.anthropic_api_key.get_secret_value(),
            temperature=0.1 # Quase zero para máxima consistência arquitetural
        )
        
        # Carrega as regras do cargo (Tech Lead)
        with open(".capataz/roles/tech_lead.md", "r") as f:
            self.role_instruction = f.read()

    def plan_task(self, task: str, actlog: str):
        """
        Analisa a demanda e o log para criar ou ajustar o plano de execução.
        """
        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=f"""
                DEMANDA ORIGINAL: {task}
                
                HISTÓRICO ATUAL (ACTLOG):
                {actlog}
                
                Com base no estado atual, gere um PLANO DE EXECUÇÃO detalhado para o Developer (Gemini).
                Foque em segurança, separação de responsabilidades e critérios de aceite claros.
            """)
        ]
        
        response = self.llm.invoke(prompt)
        return response.content

architect_agent = ArchitectAgent()