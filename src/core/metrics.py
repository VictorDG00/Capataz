# src/core/metrics.py
import json
import os
from datetime import datetime
from typing import Optional

from langchain_core.messages import BaseMessage

PRICING: dict[str, tuple[float, float]] = {
    # modelo: (USD por 1M tokens input, USD por 1M tokens output)
    "claude-3-5-sonnet-20240620": (3.00, 15.00),
    "claude-3-5-sonnet":          (3.00, 15.00),
    "gemini-1.5-pro":             (1.25,  5.00),
    "gemini-1.5-flash":           (0.075, 0.30),
    "deepseek-chat":              (0.14,  0.28),
    "gpt-4o":                     (5.00, 15.00),
    "gpt-4o-mini":                (0.15,  0.60),
    "default":                    (1.00,  3.00),
}

_TOTALS_FILE = ".capataz/metrics_totals.json"
_METRICS_FILE = ".capataz/METRICS.md"
_LOGS_DIR = ".capataz/logs"


def _get_price(model: str) -> tuple[float, float]:
    """Retorna (input_price, output_price) por 1M tokens para o modelo dado."""
    for key in PRICING:
        if key in model:
            return PRICING[key]
    return PRICING["default"]


def _extract_tokens(response: BaseMessage) -> dict[str, int]:
    """
    Normaliza os 3 formatos de response_metadata do LangChain.
    Retorna {"input": N, "output": N}. Nunca levanta exceção.
    """
    try:
        meta = response.response_metadata
        if "usage" in meta:                          # Anthropic
            u = meta["usage"]
            return {"input": u.get("input_tokens", 0), "output": u.get("output_tokens", 0)}
        if "usage_metadata" in meta:                 # Google
            u = meta["usage_metadata"]
            return {"input": u.get("prompt_token_count", 0), "output": u.get("candidates_token_count", 0)}
        if "token_usage" in meta:                    # OpenAI / DeepSeek
            u = meta["token_usage"]
            return {"input": u.get("prompt_tokens", 0), "output": u.get("completion_tokens", 0)}
    except Exception:
        pass
    return {"input": 0, "output": 0}


def _bar(fraction: float, width: int = 20) -> str:
    filled = round(fraction * width)
    return "█" * filled + "░" * (width - filled)


def _fmt_duration(seconds: float) -> str:
    if seconds < 60:
        return f"{seconds:.1f}s"
    m, s = divmod(int(seconds), 60)
    return f"{m}m {s:02d}s"


def _fmt_cost(usd: float) -> str:
    return f"${usd:.4f}"


class MetricsCollector:
    """
    Coleta tokens, custo e tempo de cada chamada LLM durante uma sessão do Capataz.
    Grava logs em .capataz/logs/ e atualiza .capataz/METRICS.md ao fechar a sessão.
    Injetado via construtor nos agentes — não entra no AgentState (não é serializável).
    """

    def __init__(self, task: str, thread_id: str, cycle_file: str = "—") -> None:
        """Cria o arquivo de sessão com cabeçalho."""
        self.task = task
        self.thread_id = thread_id
        self.cycle_file = cycle_file
        self.started_at = datetime.now()
        self.session_id = self.started_at.strftime("%Y%m%d_%H%M%S")

        # Acumuladores da sessão
        self._totals: dict[str, dict] = {}  # role → {input, output, cost, calls, duration}
        self._timeline: list[str] = []
        self._retries: list[str] = []

        os.makedirs(_LOGS_DIR, exist_ok=True)
        self._session_file = os.path.join(_LOGS_DIR, f"session_{self.session_id}.md")
        self._write_header()

    def _write_header(self) -> None:
        header = f"""# Sessão: {self.started_at.strftime("%Y-%m-%d %H:%M:%S")}
**Task:** {self.task}
**Thread ID:** {self.thread_id}
**Ciclo:** {self.cycle_file}

---

## Timeline de Execução

| Hora | Role | Evento | Input tok | Output tok | Total | Custo | Duração |
|------|------|--------|-----------|------------|-------|-------|---------|
"""
        with open(self._session_file, "w", encoding="utf-8") as f:
            f.write(header)

    def _accumulate(self, role: str, input_tok: int, output_tok: int, cost: float, duration: float) -> None:
        if role not in self._totals:
            self._totals[role] = {"input": 0, "output": 0, "cost": 0.0, "calls": 0, "duration": 0.0}
        r = self._totals[role]
        r["input"] += input_tok
        r["output"] += output_tok
        r["cost"] += cost
        r["calls"] += 1
        r["duration"] += duration

    def record_call(self, role: str, model: str, response: BaseMessage, duration: float) -> None:
        """Registra uma chamada LLM: extrai tokens, calcula custo e grava na timeline."""
        tokens = _extract_tokens(response)
        inp, out = tokens["input"], tokens["output"]
        price_in, price_out = _get_price(model)
        cost = (inp * price_in + out * price_out) / 1_000_000

        self._accumulate(role, inp, out, cost, duration)

        hora = datetime.now().strftime("%H:%M:%S")
        total = inp + out
        line = f"| {hora} | {role} | {model} | {inp:,} | {out:,} | {total:,} | {_fmt_cost(cost)} | {_fmt_duration(duration)} |"
        self._timeline.append(line)
        with open(self._session_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def record_validator(self, duration: float, status: str) -> None:
        """Registra evento do Validator (SAST/testes) — sem chamada LLM."""
        hora = datetime.now().strftime("%H:%M:%S")
        emoji = "✅" if status in ("success", "passed") else "❌"
        line = f"| {hora} | validator | {emoji} SAST scan ({status}) | — | — | — | — | {_fmt_duration(duration)} |"
        self._timeline.append(line)
        with open(self._session_file, "a", encoding="utf-8") as f:
            f.write(line + "\n")

    def record_retry(self, role: str, reason: str) -> None:
        """Registra evento de retry com motivo legível."""
        hora = datetime.now().strftime("%H:%M:%S")
        entry = f"| {hora} | {role} | 🔁 Retry: {reason[:80]} | — | — | — | — | — |"
        self._timeline.append(entry)
        self._retries.append(f"- **{hora}** [{role}] {reason}")
        with open(self._session_file, "a", encoding="utf-8") as f:
            f.write(entry + "\n")

    def close_session(self) -> None:
        """Escreve o resumo da sessão no log e atualiza METRICS.md com totais acumulados."""
        ended_at = datetime.now()
        total_duration = (ended_at - self.started_at).total_seconds()

        total_input = sum(r["input"] for r in self._totals.values())
        total_output = sum(r["output"] for r in self._totals.values())
        total_tokens = total_input + total_output
        total_cost = sum(r["cost"] for r in self._totals.values())
        total_retries = len(self._retries)

        # Distribuição por role (barras ASCII)
        dist_lines = []
        for role, data in sorted(self._totals.items()):
            role_tokens = data["input"] + data["output"]
            pct = (role_tokens / total_tokens * 100) if total_tokens > 0 else 0
            bar = _bar(pct / 100)
            dist_lines.append(f"{role:<12} {bar} {pct:4.1f}% ({role_tokens:,} tok)")

        retry_section = "\n".join(self._retries) if self._retries else "Nenhum retry nesta sessão."

        summary = f"""
---

## Resumo da Sessão

| Métrica | Valor |
|---------|-------|
| Tokens totais | {total_tokens:,} |
| Custo estimado | {_fmt_cost(total_cost)} |
| Tempo de execução | {_fmt_duration(total_duration)} |
| Retries | {total_retries} |
| Modelos utilizados | {", ".join(sorted(self._totals.keys()))} |

## Distribuição por Role
```
{chr(10).join(dist_lines)}
```

## Eventos de Retry
{retry_section}
"""
        with open(self._session_file, "a", encoding="utf-8") as f:
            f.write(summary)

        self._update_metrics_md(total_tokens, total_cost, total_duration, total_retries)

    def _update_metrics_md(
        self,
        session_tokens: int,
        session_cost: float,
        session_duration: float,
        session_retries: int,
    ) -> None:
        """Lê totais acumulados, soma os da sessão atual e sobrescreve METRICS.md."""
        totals = self._load_totals()
        totals["sessions"] += 1
        totals["tokens"] += session_tokens
        totals["cost"] += session_cost
        totals["duration"] += session_duration
        totals["retries"] += session_retries

        for role, data in self._totals.items():
            if role not in totals["by_role"]:
                totals["by_role"][role] = {"tokens": 0, "cost": 0.0}
            totals["by_role"][role]["tokens"] += data["input"] + data["output"]
            totals["by_role"][role]["cost"] += data["cost"]

        hist_entry = {
            "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "task": self.task[:40],
            "tokens": session_tokens,
            "cost": session_cost,
            "duration": session_duration,
            "retries": session_retries,
        }
        totals["history"].insert(0, hist_entry)
        totals["history"] = totals["history"][:20]  # mantém as 20 últimas

        self._save_totals(totals)
        self._render_metrics_md(totals)

    def _load_totals(self) -> dict:
        if os.path.exists(_TOTALS_FILE):
            try:
                with open(_TOTALS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                pass
        return {"sessions": 0, "tokens": 0, "cost": 0.0, "duration": 0.0, "retries": 0, "by_role": {}, "history": []}

    def _save_totals(self, totals: dict) -> None:
        with open(_TOTALS_FILE, "w", encoding="utf-8") as f:
            json.dump(totals, f, indent=2, ensure_ascii=False)

    def _render_metrics_md(self, totals: dict) -> None:
        """Gera o METRICS.md completo a partir dos totais acumulados."""
        updated = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        total_tok = totals["tokens"]

        by_role_rows = []
        for role, data in sorted(totals["by_role"].items()):
            pct = (data["tokens"] / total_tok * 100) if total_tok > 0 else 0
            avg = data["tokens"] / totals["sessions"] if totals["sessions"] > 0 else 0
            by_role_rows.append(
                f"| {role:<12} | {data['tokens']:>9,} | {_fmt_cost(data['cost']):>9} | {pct:5.1f}% | {avg:>9,.0f} |"
            )

        hist_rows = []
        for h in totals["history"]:
            status = "✅" if h["retries"] == 0 else "⚠️"
            hist_rows.append(
                f"| {h['date']} | {h['task']:<40} | {h['tokens']:>7,} | {_fmt_cost(h['cost']):>7} "
                f"| {_fmt_duration(h['duration']):>8} | {h['retries']} {status} |"
            )

        content = f"""# Métricas Acumuladas do Capataz

Atualizado em: {updated}

## Resumo Geral
| Métrica | Valor |
|---------|-------|
| Total de sessões | {totals['sessions']:,} |
| Tokens consumidos | {total_tok:,} |
| Custo estimado | {_fmt_cost(totals['cost'])} |
| Tempo total | {_fmt_duration(totals['duration'])} |
| Retries totais | {totals['retries']:,} |

## Consumo por Role
| Role | Tokens | Custo | % do total | Avg/sessão |
|------|--------|-------|------------|------------|
{chr(10).join(by_role_rows)}

## Histórico de Sessões (últimas 20)
| Data/Hora | Task | Tokens | Custo | Tempo | Retries |
|-----------|------|--------|-------|-------|---------|
{chr(10).join(hist_rows)}
"""
        with open(_METRICS_FILE, "w", encoding="utf-8") as f:
            f.write(content)
