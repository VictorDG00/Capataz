# src/agents/architect.py
import os
import glob
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
        role_path = ".capataz/roles/tech_lead.md"
        if os.path.exists(role_path):
            with open(role_path, "r") as f:
                self.role_instruction = f.read()
        else:
            self.role_instruction = "Você é o arquiteto responsável por traçar o plano de execução do projeto."

    def _get_next_cycle_number(self):
        """Retorna o próximo número de ciclo formatado (ex: '01')."""
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

    def plan_cycle(self, task: str):
        """
        Lê projeto.md e sprints.md para gerar o arquivo CicloNN.md contendo o checklist de Sprints.
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
                Você é o arquiteto responsável por traçar o plano de execução do projeto. Sua tarefa é criar um novo ciclo.
                
                DEMANDA ATUAL: {task}
                
                Fontes de Verdade:
                1. projeto.md:
                {projeto_content}

                2. sprints.md:
                {sprints_content}

                Como Estruturar a sua resposta (ela será salva como o arquivo markdown do ciclo):
                - Crie um cabeçalho com o objetivo geral deste Ciclo.
                - Liste todas as Sprints necessárias para alcançar o objetivo. Não há limite de sprints, mas elas devem ser curtas e focadas.
                - Para cada Sprint, defina **exatamente** no formato de checklist (use "[ ] " literal):
                  - [ ] **Sprint X: [Nome da Sprint]**
                  - **Objetivo:** [O que será construído]
                  - **Regra de Validação:** [Como os testes atuarão aqui]
                  - **Módulos Afetados:** [Quais áreas do monolito serão tocadas]

                Atenção: O plano deve seguir uma ordem cronológica lógica, garantindo que nenhuma sprint quebre o desacoplamento do sistema.
                Responda APENAS com o conteúdo Markdown final que será salvo no arquivo, sem introduções ou explicações fora do Markdown.
            """)
        ]
        
        response = self.llm.invoke(prompt)

        cycle_num = self._get_next_cycle_number()
        cycle_filename = f".capataz/ciclos/Ciclo{cycle_num}.md"

        # Garante que o diretório existe
        os.makedirs(".capataz/ciclos", exist_ok=True)

        with open(cycle_filename, "w") as f:
            f.write(response.content)

        print(f"🏛️ [CAPATAZ] Ciclo gerado com sucesso: {cycle_filename}")
        return cycle_filename

architect_agent = ArchitectAgent()
