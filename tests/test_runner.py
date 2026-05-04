"""Testes para TestRunner — Sprint 03 do Ciclo03."""
import pytest
from unittest.mock import patch

from src.core.runner import TestRunner, _parse_pytest_output


# --- _parse_pytest_output ---

def test_parse_passou():
    stdout = "===== 5 passed in 1.23s ====="
    result = _parse_pytest_output(stdout, "")
    assert result == {"passed": 5, "failed": 0, "errors": 0}


def test_parse_falhou():
    stdout = "===== 2 passed, 3 failed in 2.10s ====="
    result = _parse_pytest_output(stdout, "")
    assert result["passed"] == 2
    assert result["failed"] == 3


def test_parse_com_erros():
    stdout = "===== 1 passed, 1 error in 0.5s ====="
    result = _parse_pytest_output(stdout, "")
    assert result["errors"] == 1


def test_parse_output_vazio():
    result = _parse_pytest_output("", "")
    assert result == {"passed": 0, "failed": 0, "errors": 0}


# --- TestRunner.run ---

@pytest.fixture
def runner():
    return TestRunner()


def _mock_security(status="success", stdout="===== 5 passed in 1.0s =====", stderr=""):
    return {"status": status, "stdout": stdout, "stderr": stderr, "exit_code": 0 if status == "success" else 1}


def test_run_pytest_passou(runner):
    with patch("src.core.runner.security_manager") as mock_sec:
        mock_sec.run_isolated_command.return_value = _mock_security(
            stdout="===== 10 passed in 2.5s ====="
        )
        result = runner.run(runner="pytest", path="tests/")

    assert result["status"] == "passed"
    assert result["passed"] == 10
    assert result["failed"] == 0
    assert result["duration_seconds"] >= 0


def test_run_pytest_falhou(runner):
    with patch("src.core.runner.security_manager") as mock_sec:
        mock_sec.run_isolated_command.return_value = _mock_security(
            status="failed",
            stdout="FAILED tests/test_foo.py::test_bar\n===== 1 failed in 0.8s =====",
        )
        result = runner.run(runner="pytest")

    assert result["status"] == "failed"
    assert result["failed"] == 1
    assert "full_output" in result
    assert len(result["full_output"]) > 0


def test_run_timeout_retorna_error(runner):
    with patch("src.core.runner.security_manager") as mock_sec:
        mock_sec.run_isolated_command.return_value = {
            "status": "error",
            "message": "Execução interrompida por Timeout.",
            "stdout": "",
            "stderr": "",
        }
        result = runner.run(runner="pytest")

    assert result["status"] == "error"
    assert result["errors"] == 1
    assert "Timeout" in result["summary"]


def test_runner_desconhecido_retorna_error(runner):
    result = runner.run(runner="mocha")  # type: ignore
    assert result["status"] == "error"
    assert "não suportado" in result["summary"]


def test_summary_e_ultima_linha(runner):
    with patch("src.core.runner.security_manager") as mock_sec:
        mock_sec.run_isolated_command.return_value = _mock_security(
            stdout="linha 1\nlinha 2\n===== 3 passed ====="
        )
        result = runner.run()

    assert result["summary"] == "===== 3 passed ====="
