# src/core/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import SecretStr

class Settings(BaseSettings):
    # O Pydantic valida se essas chaves estão no seu .env
    anthropic_api_key: SecretStr
    google_api_key: SecretStr
    
    # Configurações do Banco de Dados de Estado (Checkpoints)
    database_url: str = "sqlite:///./src/core/checkpoints.db"
    
    # Configurações do Orquestrador
    max_log_turns: int = 5
    project_root: str = "."

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

settings = Settings()