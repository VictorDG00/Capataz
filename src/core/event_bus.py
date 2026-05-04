# src/core/event_bus.py
from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Generator, Optional

try:
    import redis
except ImportError:
    redis = None  # type: ignore[assignment]

_DEFAULT_REDIS_URL = "redis://localhost:6379"
_EVENT_TTL_SECONDS = 3600  # eventos expiram em 1h
_CONNECT_TIMEOUT = 1.0


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


class EventBus:
    """
    Canal de eventos Redis para comunicação em tempo real entre o grafo e a UI.

    Publica eventos de status do Capataz num canal dedicado por sessão.
    Sem Redis disponível, todos os métodos são silenciosos — o CLI continua
    funcionando normalmente (graceful degradation).

    Usa redis sync (não asyncio) porque o grafo roda em threads Python.
    O endpoint SSE do FastAPI chama subscribe() via asyncio.to_thread().
    """

    def __init__(self, session_id: str, redis_url: str = _DEFAULT_REDIS_URL):
        self.session_id = session_id
        self.channel = f"capataz:session:{session_id}"
        self._client: Optional[object] = None
        self._available = False

        try:
            if redis is None:
                return
            client = redis.from_url(
                redis_url,
                socket_connect_timeout=_CONNECT_TIMEOUT,
                decode_responses=True,
            )
            client.ping()
            self._client = client
            self._available = True
        except Exception:
            pass

    def publish(self, event_type: str, **kwargs) -> None:
        """
        Publica um evento no canal da sessão.

        Silencioso se Redis indisponível — nunca levanta exceção.

        Args:
            event_type: Tipo do evento (node_start, node_end, sprint_done, etc.)
            **kwargs: Campos adicionais do evento (node, message, tokens_used, etc.)
        """
        if not self._available or self._client is None:
            return

        event = {
            "session_id": self.session_id,
            "timestamp": _now_iso(),
            "type": event_type,
            "node": kwargs.get("node", ""),
            "sprint_name": kwargs.get("sprint_name", ""),
            "sprint_index": kwargs.get("sprint_index", 0),
            "tokens_used": kwargs.get("tokens_used", 0),
            "cost_usd": kwargs.get("cost_usd", 0.0),
            "duration_seconds": kwargs.get("duration_seconds", 0.0),
            "message": kwargs.get("message", ""),
        }

        try:
            self._client.publish(self.channel, json.dumps(event))
        except Exception:
            pass

    def subscribe(self) -> Generator[str, None, None]:
        """
        Gerador de strings JSON de eventos — usado pelo endpoint SSE.

        Bloqueia até o canal receber mensagens ou o cliente desconectar.
        Retorna silenciosamente se Redis indisponível.
        """
        if not self._available or self._client is None:
            return

        try:
            pubsub = self._client.pubsub()
            pubsub.subscribe(self.channel)
            for message in pubsub.listen():
                if message["type"] == "message":
                    yield message["data"]
        except Exception:
            return

    @staticmethod
    def is_available(redis_url: str = _DEFAULT_REDIS_URL) -> bool:
        """
        Testa conexão Redis sem levantar exceção.

        Returns False em menos de _CONNECT_TIMEOUT segundos se Redis não estiver rodando.
        """
        try:
            if redis is None:
                return False
            client = redis.from_url(
                redis_url,
                socket_connect_timeout=_CONNECT_TIMEOUT,
                decode_responses=True,
            )
            client.ping()
            return True
        except Exception:
            return False
