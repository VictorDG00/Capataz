# src/core/llm_factory.py
from openai import OpenAI
from src.core.config import settings

class LLMFactory:
    def __init__(self):
        self.client = OpenAI(
            api_key=settings.deepseek_api_key.get_secret_value(),
            base_url="https://api.deepseek.com"
        )

    def ask_agent(self, role_file: str, prompt: str):
        # Lê as regras do cargo (tech_lead.md, developer.md, etc)
        with open(role_file, "r") as f:
            system_instruction = f.read()

        response = self.client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ],
            stream=False
        )
        return response.choices[0].message.content

llm_forge = LLMFactory()