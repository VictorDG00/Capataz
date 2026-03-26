# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr, Field
from typing import Optional

class Settings(BaseSettings):
    # Provedores (Mapeados diretamente do .env via prefixo ou nome exato)
    agent_provider_architect: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_ARCHITECT")
    agent_provider_developer: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_DEVELOPER")
    agent_provider_designer: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_DESIGNER")
    agent_provider_security: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_SECURITY")

    # Chaves de API
    deepseek_api_key: Optional[SecretStr] = None
    anthropic_api_key: Optional[SecretStr] = None
    google_api_key: Optional[SecretStr] = None

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

    def get_provider_for(self, role: str) -> str:
        """Helper para a Factory buscar o provedor correto"""
        mapping = {
            "architect": self.agent_provider_architect,
            "developer": self.agent_provider_developer,
            "designer": self.agent_provider_designer,
            "security_auditor": self.agent_provider_security
        }
        return mapping.get(role, "deepseek")

settings = Settings()