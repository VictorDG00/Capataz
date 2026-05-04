# src/api/schemas.py
from typing import Optional
from pydantic import BaseModel


class StartRequest(BaseModel):
    """Payload para iniciar uma sessão do Capataz."""
    task: str


class SessionStatus(BaseModel):
    """Status resumido de uma sessão em andamento."""
    session_id: str
    status: str          # running | done | error
    current_node: str
    tokens_used: int
    cost_usd: float


class StartResponse(BaseModel):
    session_id: str
    message: str


class TestStartResponse(BaseModel):
    pid: Optional[int]
    message: str
