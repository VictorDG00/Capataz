# src/api/routes.py
import asyncio
import subprocess
import threading
import uuid
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse, StreamingResponse

from src.api.schemas import SessionStatus, StartRequest, StartResponse, TestStartResponse
from src.core.event_bus import EventBus
from src.core.project_config import ProjectConfig, load_project_config

router = APIRouter()

_sessions: dict[str, dict] = {}
_STATIC_DIR = Path(__file__).parent / "static"


def _get_config() -> Optional[ProjectConfig]:
    try:
        return load_project_config()
    except Exception:
        return None


@router.get("/")
async def index():
    """Serve a interface web principal."""
    return FileResponse(str(_STATIC_DIR / "index.html"))


@router.get("/config")
async def get_config():
    """Retorna a ProjectConfig atual como JSON."""
    config = _get_config() or ProjectConfig()
    return config.model_dump()


@router.post("/start", response_model=StartResponse)
async def start_session(body: StartRequest):
    """Inicia sessão do Capataz em background thread. Retorna session_id imediatamente."""
    session_id = str(uuid.uuid4())
    config = _get_config() or ProjectConfig()
    event_bus = EventBus(session_id=session_id)

    _sessions[session_id] = {
        "status": "running",
        "current_node": "",
        "tokens_used": 0,
        "cost_usd": 0.0,
        "test_process": None,
        "config": config,
        "event_bus": event_bus,
    }

    thread = threading.Thread(
        target=_run_graph_background,
        args=(session_id, body.task, config, event_bus),
        daemon=True,
    )
    thread.start()
    _sessions[session_id]["thread"] = thread

    return StartResponse(
        session_id=session_id,
        message="Sessão iniciada. Acompanhe via /session/{id}/stream",
    )


@router.get("/session/{session_id}/stream")
async def stream_session(session_id: str):
    """SSE — entrega eventos do grafo em tempo real ao browser."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    event_bus: EventBus = _sessions[session_id]["event_bus"]

    async def event_generator():
        try:
            async for data in _iter_redis_events(event_bus):
                yield f"data: {data}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.get("/session/{session_id}/status", response_model=SessionStatus)
async def session_status(session_id: str):
    """Retorna o status atual de uma sessão."""
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")
    return SessionStatus(
        session_id=session_id,
        status=sess["status"],
        current_node=sess["current_node"],
        tokens_used=sess["tokens_used"],
        cost_usd=sess["cost_usd"],
    )


@router.post("/session/{session_id}/test", response_model=TestStartResponse)
async def start_test(session_id: str):
    """Inicia run_command em background. Stdout vai para Redis via EventBus."""
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    config: ProjectConfig = sess["config"]
    run_command = config.project.run_command
    if not run_command:
        raise HTTPException(status_code=400, detail="run_command não configurado.")

    if sess.get("test_process") and sess["test_process"].poll() is None:
        raise HTTPException(status_code=409, detail="Processo já está rodando.")

    event_bus: EventBus = sess["event_bus"]
    process = subprocess.Popen(
        run_command,
        shell=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    sess["test_process"] = process

    threading.Thread(
        target=_stream_process_output,
        args=(process, event_bus),
        daemon=True,
    ).start()

    return TestStartResponse(pid=process.pid, message=f"Processo iniciado (PID {process.pid})")


@router.get("/session/{session_id}/test/stream")
async def stream_test(session_id: str):
    """SSE — entrega stdout do processo de teste ao browser."""
    if session_id not in _sessions:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    event_bus: EventBus = _sessions[session_id]["event_bus"]

    async def log_generator():
        try:
            async for data in _iter_redis_events(event_bus, event_filter="test_output"):
                import json
                try:
                    msg = json.loads(data).get("message", data)
                except Exception:
                    msg = data
                yield f"data: {msg}\n\n"
        except asyncio.CancelledError:
            pass

    return StreamingResponse(
        log_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@router.post("/session/{session_id}/test/stop")
async def stop_test(session_id: str):
    """Encerra o processo de teste via SIGTERM."""
    sess = _sessions.get(session_id)
    if not sess:
        raise HTTPException(status_code=404, detail="Sessão não encontrada.")

    process: Optional[subprocess.Popen] = sess.get("test_process")
    if not process or process.poll() is not None:
        return {"message": "Nenhum processo ativo."}

    process.terminate()
    return {"message": "Processo encerrado."}


# --- Helpers internos ---

async def _iter_redis_events(event_bus: EventBus, event_filter: Optional[str] = None):
    """Itera sobre eventos do Redis de forma assíncrona sem bloquear o event loop."""
    import json
    loop = asyncio.get_event_loop()
    queue: asyncio.Queue = asyncio.Queue()

    def _subscribe_thread():
        for data in event_bus.subscribe():
            if event_filter:
                try:
                    if json.loads(data).get("type") != event_filter:
                        continue
                except Exception:
                    pass
            loop.call_soon_threadsafe(queue.put_nowait, data)
        loop.call_soon_threadsafe(queue.put_nowait, None)

    threading.Thread(target=_subscribe_thread, daemon=True).start()

    while True:
        item = await queue.get()
        if item is None:
            break
        yield item


def _run_graph_background(session_id: str, task: str, config: ProjectConfig, event_bus: EventBus):
    """Executa o grafo em thread separada."""
    sess = _sessions[session_id]
    try:
        from src.agents.graph import create_graph
        from src.core.metrics import MetricsCollector

        collector = MetricsCollector(task=task, thread_id=session_id)
        engine = create_graph(
            collector=collector,
            event_bus=event_bus,
            state_path=".capataz/state.db",
        )
        initial_state = {
            "task": task,
            "cycle_file": "", "contract_path": "", "current_sprint": "",
            "latest_output": "", "turn_count": 0, "integration_failures": 0,
            "files_written": [], "status": "pending",
        }

        for event in engine.stream(initial_state, {"configurable": {"thread_id": session_id}}):
            for node in event:
                sess["current_node"] = node

        collector.close_session()
        sess["status"] = "done"
    except Exception as e:
        sess["status"] = "error"
        event_bus.publish("error", message=str(e)[:200])
    finally:
        sess["current_node"] = ""


def _stream_process_output(process: subprocess.Popen, event_bus: EventBus):
    """Lê stdout do processo linha a linha e publica no Redis como test_output."""
    for line in iter(process.stdout.readline, ""):
        event_bus.publish("test_output", message=line.rstrip())
    process.stdout.close()
