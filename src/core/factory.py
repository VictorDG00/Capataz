# src/core/factory.py
from langchain_openai import ChatOpenAI
from langchain_anthropic import ChatAnthropic
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings

class LLMFactory:
    """
    Fábrica responsável por instanciar o provedor de IA correto 
    baseado nas configurações dinâmicas do ambiente.
    """
    
    @staticmethod
    def get_model(role: str):
        # Busca qual provedor está designado para este cargo no config (via helper)
        provider = settings.get_provider_for(role)
        
        if provider == "deepseek":
            return ChatOpenAI(
                model="deepseek-chat",
                api_key=settings.deepseek_api_key.get_secret_value() if settings.deepseek_api_key else None,
                base_url=settings.deepseek_base_url
            )
        
        elif provider == "claude":
            return ChatAnthropic(
                model="claude-3-5-sonnet-20240620",
                api_key=settings.anthropic_api_key.get_secret_value() if settings.anthropic_api_key else None
            )
            
        elif provider == "gemini":
            return ChatGoogleGenerativeAI(
                model="gemini-1.5-pro",
                google_api_key=settings.google_api_key.get_secret_value() if settings.google_api_key else None
            )

        elif provider == "openai":
            return ChatOpenAI(
                model="gpt-4o",
                api_key=settings.openai_api_key.get_secret_value() if settings.openai_api_key else None
            )
        
        raise ValueError(f"Provedor '{provider}' não configurado ou suportado para o cargo '{role}'.")