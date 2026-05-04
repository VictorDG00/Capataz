# src/core/runner.py
import re
import time
from typing import Literal

from src.core.security import security_manager

RunnerType = Literal["pytest", "jest"]

_PYTEST_SUMMARY = re.compile(
    r"(\d+) passed|(\d+) failed|(\d+) error"
)


def _parse_pytest_output(stdout: str, stderr: str) -> dict[str, int]:
    """Extrai contagens de passed/failed/errors do output do pytest."""
    combined = stdout + stderr
    passed = failed = errors = 0
    for m in _PYTEST_SUMMARY.finditer(combined):
        if m.group(1):
            passed = int(m.group(1))
        elif m.group(2):
            failed = int(m.group(2))
        elif m.group(3):
            errors = int(m.group(3))
    return {"passed": passed, "failed": failed, "errors": errors}


def _last_line(text: str) -> str:
    lines = [l for l in text.strip().splitlines() if l.strip()]
    return lines[-1] if lines else ""


class TestRunner:
    """
    Executa a suite de testes do projeto-alvo e retorna resultado estruturado.

    Só executa comandos que estão na whitelist de core.security.
    O resultado é usado pelo Validator para decidir sucesso ou retry para o Developer.
    """

    def run(self, runner: RunnerType = "pytest", path: str = ".") -> dict:
        """
        Executa os testes do projeto e retorna schema estruturado.

        Args:
            runner: "pytest" ou "jest".
            path: Diretório ou arquivo de testes a executar.

        Returns:
            {
                "status": "passed" | "failed" | "error",
                "passed": int,
                "failed": int,
                "errors": int,
                "duration_seconds": float,
                "summary": str,       # última linha do output
                "full_output": str,   # output completo para feedback ao Developer
            }
        """
        if runner == "pytest":
            command = f"pytest {path} -v --tb=short"
        elif runner == "jest":
            command = f"npm test -- --watchAll=false"
        else:
            return {
                "status": "error",
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "duration_seconds": 0.0,
                "summary": f"Runner '{runner}' não suportado. Use 'pytest' ou 'jest'.",
                "full_output": "",
            }

        start = time.perf_counter()
        result = security_manager.run_isolated_command(command, timeout=120)
        duration = time.perf_counter() - start

        stdout = result.get("stdout", "")
        stderr = result.get("stderr", "")
        full_output = stdout + ("\n" + stderr if stderr else "")

        if result["status"] == "error":
            return {
                "status": "error",
                "passed": 0,
                "failed": 0,
                "errors": 1,
                "duration_seconds": duration,
                "summary": result.get("message", "Erro ao executar testes."),
                "full_output": full_output,
            }

        counts = _parse_pytest_output(stdout, stderr) if runner == "pytest" else {"passed": 0, "failed": 0, "errors": 0}

        status = "passed" if result["status"] == "success" else "failed"

        return {
            "status": status,
            "passed": counts["passed"],
            "failed": counts["failed"],
            "errors": counts["errors"],
            "duration_seconds": round(duration, 2),
            "summary": _last_line(full_output),
            "full_output": full_output,
        }


test_runner = TestRunner()
