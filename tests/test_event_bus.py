"""Testes para EventBus — Sprint 02 do Ciclo04."""
import json
import pytest
from unittest.mock import MagicMock, patch


# --- is_available ---

def test_is_available_sem_redis_retorna_false():
    from src.core.event_bus import EventBus
    # Porta inexistente → deve retornar False em < 1s
    result = EventBus.is_available("redis://localhost:19999")
    assert result is False


# --- EventBus sem Redis (graceful degradation) ---

@pytest.fixture
def bus_sem_redis():
    from src.core.event_bus import EventBus
    # Porta inexistente → _available = False
    return EventBus(session_id="test-123", redis_url="redis://localhost:19999")


def test_publish_sem_redis_nao_levanta_excecao(bus_sem_redis):
    bus_sem_redis.publish("node_start", node="architect", message="Planejando...")


def test_subscribe_sem_redis_retorna_imediatamente(bus_sem_redis):
    result = list(bus_sem_redis.subscribe())
    assert result == []


# --- EventBus com Redis mockado ---

@pytest.fixture
def bus_com_redis_mock():
    mock_client = MagicMock()
    mock_client.ping.return_value = True

    with patch("src.core.event_bus.redis") as mock_redis_lib:
        mock_redis_lib.from_url.return_value = mock_client

        from src.core.event_bus import EventBus
        bus = EventBus.__new__(EventBus)
        bus.session_id = "sess-abc"
        bus.channel = "capataz:session:sess-abc"
        bus._client = mock_client
        bus._available = True
        yield bus, mock_client


def test_publish_chama_redis_publish(bus_com_redis_mock):
    bus, mock_client = bus_com_redis_mock
    bus.publish("node_start", node="architect", message="Iniciando")
    mock_client.publish.assert_called_once()
    channel, payload = mock_client.publish.call_args[0]
    assert channel == "capataz:session:sess-abc"
    data = json.loads(payload)
    assert data["type"] == "node_start"
    assert data["node"] == "architect"
    assert data["session_id"] == "sess-abc"
    assert "timestamp" in data


def test_publish_campos_opcionais_tem_defaults(bus_com_redis_mock):
    bus, mock_client = bus_com_redis_mock
    bus.publish("cycle_done")
    _, payload = mock_client.publish.call_args[0]
    data = json.loads(payload)
    assert data["tokens_used"] == 0
    assert data["cost_usd"] == 0.0
    assert data["sprint_name"] == ""


def test_publish_redis_com_erro_nao_propaga(bus_com_redis_mock):
    bus, mock_client = bus_com_redis_mock
    mock_client.publish.side_effect = Exception("Redis error")
    bus.publish("node_start", node="test")  # não deve levantar


def test_subscribe_entrega_mensagens(bus_com_redis_mock):
    bus, mock_client = bus_com_redis_mock
    pubsub = MagicMock()
    mock_client.pubsub.return_value = pubsub
    pubsub.listen.return_value = [
        {"type": "subscribe", "data": 1},
        {"type": "message", "data": '{"type":"node_start"}'},
        {"type": "message", "data": '{"type":"cycle_done"}'},
    ]

    messages = list(bus.subscribe())
    assert len(messages) == 2
    assert json.loads(messages[0])["type"] == "node_start"
    assert json.loads(messages[1])["type"] == "cycle_done"


def test_event_bus_integrado_no_create_graph():
    """create_graph aceita event_bus sem quebrar."""
    from src.agents.graph import create_graph
    from src.core.event_bus import EventBus

    bus = EventBus(session_id="test", redis_url="redis://localhost:19999")
    engine = create_graph(event_bus=bus)
    assert engine is not None
