# src/agents/executor.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.schema import SystemMessage, HumanMessage
from src.core.config import settings
import os

class ExecutorAgent:
    def __init__(self):
        # Inicializa o Gemini com a chave do .env
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-pro",
            google_api_key=settings.google_api_key.get_secret_value(),
            temperature=0.2 # Baixa temperatura para código mais previsível
        )
        # Carrega as regras do cargo
        with open(".capataz/roles/developer.md", "r") as f:
            self.role_instruction = f.read()

    def execute_plan(self, plan: str, context: str):
        """
        Recebe o plano do Claude e o contexto (ACTLOG + Arquivos)
        """
        prompt = [
            SystemMessage(content=self.role_instruction),
            HumanMessage(content=f"PLANO DO TECH LEAD:\n{plan}\n\nCONTEXTO ATUAL:\n{context}\n\nExecute as tarefas agora.")
        ]
        
        response = self.llm.invoke(prompt)
        return response.content

    def write_to_disk(self, filename: str, content: str):
        """
        Função auxiliar para o orquestrador salvar o código gerado.
        Poderia ser expandida para ser uma 'Tool' que o próprio Gemini chama.
        """
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        with open(filename, "w") as f:
            f.write(content)
        print(f"🛠️ Capataz: Arquivo {filename} atualizado com sucesso.")

executor_agent = ExecutorAgent()