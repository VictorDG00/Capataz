"""Testes para FastAPI routes — Sprint 03 do Ciclo04."""
import json
import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient

from src.api.main import app

client = TestClient(app)


@pytest.fixture(autouse=True)
def clean_sessions():
    from src.api.routes import _sessions
    _sessions.clear()
    yield
    _sessions.clear()


# --- GET /config ---

def test_get_config_sem_yaml_retorna_defaults(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    response = client.get("/config")
    assert response.status_code == 200
    data = response.json()
    assert "project" in data
    assert "agents" in data
    assert "limits" in data


def test_get_config_com_yaml(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".capataz.yaml").write_text("project:\n  name: TestApp\n")
    response = client.get("/config")
    assert response.status_code == 200
    assert response.json()["project"]["name"] == "TestApp"


# --- POST /start ---

def test_start_retorna_session_id():
    with patch("src.api.routes._run_graph_background"):
        with patch("threading.Thread") as mock_thread:
            mock_thread.return_value.start = MagicMock()
            response = client.post("/start", json={"task": "criar auth"})

    assert response.status_code == 200
    data = response.json()
    assert "session_id" in data
    assert len(data["session_id"]) == 36  # UUID


def test_start_cria_sessao_em_running():
    from src.api.routes import _sessions
    with patch("threading.Thread") as mock_thread:
        mock_thread.return_value.start = MagicMock()
        response = client.post("/start", json={"task": "criar api"})

    session_id = response.json()["session_id"]
    assert session_id in _sessions
    assert _sessions[session_id]["status"] == "running"


# --- GET /session/{id}/status ---

def test_status_sessao_existente():
    from src.api.routes import _sessions, EventBus
    sid = "test-session-123"
    _sessions[sid] = {
        "status": "running", "current_node": "developer",
        "tokens_used": 500, "cost_usd": 0.05,
        "test_process": None, "config": MagicMock(),
        "event_bus": MagicMock(),
    }
    response = client.get(f"/session/{sid}/status")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "running"
    assert data["current_node"] == "developer"
    assert data["tokens_used"] == 500


def test_status_sessao_inexistente():
    response = client.get("/session/nao-existe/status")
    assert response.status_code == 404


# --- POST /session/{id}/test ---

def test_start_test_sem_run_command():
    from src.api.routes import _sessions
    from src.core.project_config import ProjectConfig, ProjectInfo
    sid = "test-456"
    config = ProjectConfig()  # run_command vazio
    _sessions[sid] = {
        "status": "done", "current_node": "", "tokens_used": 0, "cost_usd": 0.0,
        "test_process": None, "config": config, "event_bus": MagicMock(),
    }
    response = client.post(f"/session/{sid}/test")
    assert response.status_code == 400
    assert "run_command" in response.json()["detail"]


def test_start_test_com_run_command():
    from src.api.routes import _sessions
    from src.core.project_config import ProjectConfig, ProjectInfo
    sid = "test-789"
    config = ProjectConfig()
    config.project.run_command = "echo hello"
    _sessions[sid] = {
        "status": "done", "current_node": "", "tokens_used": 0, "cost_usd": 0.0,
        "test_process": None, "config": config, "event_bus": MagicMock(),
    }
    with patch("threading.Thread") as mock_thread:
        mock_thread.return_value.start = MagicMock()
        response = client.post(f"/session/{sid}/test")

    assert response.status_code == 200
    assert "pid" in response.json()


# --- POST /session/{id}/test/stop ---

def test_stop_test_sem_processo():
    from src.api.routes import _sessions
    sid = "stop-test"
    _sessions[sid] = {
        "status": "done", "current_node": "", "tokens_used": 0, "cost_usd": 0.0,
        "test_process": None, "config": MagicMock(), "event_bus": MagicMock(),
    }
    response = client.post(f"/session/{sid}/test/stop")
    assert response.status_code == 200
    assert "Nenhum processo" in response.json()["message"]


def test_stop_test_com_processo_ativo():
    from src.api.routes import _sessions
    sid = "stop-active"
    mock_proc = MagicMock()
    mock_proc.poll.return_value = None  # processo ativo
    _sessions[sid] = {
        "status": "running", "current_node": "", "tokens_used": 0, "cost_usd": 0.0,
        "test_process": mock_proc, "config": MagicMock(), "event_bus": MagicMock(),
    }
    response = client.post(f"/session/{sid}/test/stop")
    assert response.status_code == 200
    mock_proc.terminate.assert_called_once()
