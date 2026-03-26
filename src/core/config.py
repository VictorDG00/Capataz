# src/core/config.py
from typing import Optional

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Provedores (Mapeados diretamente do .env via prefixo ou nome exato)
    agent_provider_architect: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_ARCHITECT")
    agent_provider_developer: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_DEVELOPER")
    agent_provider_designer: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_DESIGNER")
    agent_provider_security_auditor: str = Field(default="deepseek", validation_alias="AGENT_PROVIDER_SECURITY_AUDITOR")

    # Chaves de API
    deepseek_api_key: Optional[SecretStr] = Field(default=None, validation_alias="DEEPSEEK_API_KEY")
    anthropic_api_key: Optional[SecretStr] = Field(default=None, validation_alias="ANTHROPIC_API_KEY")
    google_api_key: Optional[SecretStr] = Field(default=None, validation_alias="GOOGLE_API_KEY")
    openai_api_key: Optional[SecretStr] = Field(default=None, validation_alias="OPENAI_API_KEY")

    # URLs / configs dos provedores
    deepseek_base_url: str = Field(default="https://api.deepseek.com", validation_alias="DEEPSEEK_BASE_URL")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    def get_provider_for(self, role: str) -> str:
        """Helper para a Factory buscar o provedor correto."""
        mapping = {
            "architect": self.agent_provider_architect,
            "developer": self.agent_provider_developer,
            "designer": self.agent_provider_designer,
            "security_auditor": self.agent_provider_security_auditor,
        }
        return mapping.get(role, "deepseek")


settings = Settings()
