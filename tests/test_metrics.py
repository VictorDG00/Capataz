"""Testes para MetricsCollector — Sprint 01 do Ciclo02."""
import json
import os
import pytest
from unittest.mock import MagicMock

from src.core.metrics import MetricsCollector, _extract_tokens, _get_price, PRICING


def _make_response(metadata: dict) -> MagicMock:
    msg = MagicMock()
    msg.response_metadata = metadata
    return msg


# --- _extract_tokens ---

def test_extrai_tokens_anthropic():
    resp = _make_response({"usage": {"input_tokens": 100, "output_tokens": 50}})
    result = _extract_tokens(resp)
    assert result == {"input": 100, "output": 50}


def test_extrai_tokens_google():
    resp = _make_response({"usage_metadata": {"prompt_token_count": 200, "candidates_token_count": 80}})
    result = _extract_tokens(resp)
    assert result == {"input": 200, "output": 80}


def test_extrai_tokens_openai():
    resp = _make_response({"token_usage": {"prompt_tokens": 150, "completion_tokens": 60}})
    result = _extract_tokens(resp)
    assert result == {"input": 150, "output": 60}


def test_extrai_tokens_metadata_ausente():
    resp = _make_response({})
    result = _extract_tokens(resp)
    assert result == {"input": 0, "output": 0}


def test_extrai_tokens_sem_response_metadata():
    resp = MagicMock(spec=[])  # sem response_metadata
    result = _extract_tokens(resp)
    assert result == {"input": 0, "output": 0}


# --- _get_price ---

def test_preco_deepseek():
    price = _get_price("deepseek-chat")
    assert price == PRICING["deepseek-chat"]


def test_preco_fallback_modelo_desconhecido():
    price = _get_price("modelo-inventado-xyz")
    assert price == PRICING["default"]


# --- MetricsCollector ---

@pytest.fixture
def collector(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".capataz" / "logs").mkdir(parents=True)
    return MetricsCollector(task="tarefa teste", thread_id="abc-123", cycle_file="Ciclo01.md")


def test_cria_arquivo_de_sessao(collector, tmp_path):
    logs = list((tmp_path / ".capataz" / "logs").glob("session_*.md"))
    assert len(logs) == 1
    content = logs[0].read_text()
    assert "tarefa teste" in content
    assert "abc-123" in content


def test_record_call_grava_na_timeline(collector, tmp_path):
    resp = _make_response({"usage": {"input_tokens": 300, "output_tokens": 100}})
    collector.record_call("architect", "claude-3-5-sonnet-20240620", resp, 12.5)

    log = list((tmp_path / ".capataz" / "logs").glob("session_*.md"))[0].read_text()
    assert "architect" in log
    assert "claude-3-5-sonnet" in log
    assert "12" in log  # duração


def test_record_call_calcula_custo(collector):
    resp = _make_response({"token_usage": {"prompt_tokens": 1_000_000, "completion_tokens": 0}})
    collector.record_call("developer", "deepseek-chat", resp, 1.0)

    role_data = collector._totals["developer"]
    expected_cost = PRICING["deepseek-chat"][0]  # $0.14 por 1M tokens input
    assert abs(role_data["cost"] - expected_cost) < 0.001


def test_record_validator_grava_sem_tokens(collector, tmp_path):
    collector.record_validator(8.5, "success")
    log = list((tmp_path / ".capataz" / "logs").glob("session_*.md"))[0].read_text()
    assert "validator" in log
    assert "SAST" in log


def test_record_retry_grava_motivo(collector, tmp_path):
    collector.record_retry("developer", "contrato violado: rota errada")
    log = list((tmp_path / ".capataz" / "logs").glob("session_*.md"))[0].read_text()
    assert "contrato violado" in log
    assert len(collector._retries) == 1


def test_close_session_grava_resumo_e_metrics(collector, tmp_path):
    resp = _make_response({"usage": {"input_tokens": 500, "output_tokens": 200}})
    collector.record_call("architect", "claude-3-5-sonnet-20240620", resp, 10.0)
    collector.close_session()

    log = list((tmp_path / ".capataz" / "logs").glob("session_*.md"))[0].read_text()
    assert "Resumo da Sessão" in log
    assert "700" in log  # 500 + 200 tokens

    metrics = (tmp_path / ".capataz" / "METRICS.md").read_text()
    assert "Métricas Acumuladas" in metrics
    assert "architect" in metrics


def test_close_session_acumula_entre_sessoes(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / ".capataz" / "logs").mkdir(parents=True)

    resp = _make_response({"token_usage": {"prompt_tokens": 100, "completion_tokens": 50}})

    c1 = MetricsCollector(task="sessão 1", thread_id="t1")
    c1.record_call("developer", "deepseek-chat", resp, 5.0)
    c1.close_session()

    c2 = MetricsCollector(task="sessão 2", thread_id="t2")
    c2.record_call("developer", "deepseek-chat", resp, 5.0)
    c2.close_session()

    totals_file = tmp_path / ".capataz" / "metrics_totals.json"
    totals = json.loads(totals_file.read_text())
    assert totals["sessions"] == 2
    assert totals["tokens"] == 300  # 150 + 150
