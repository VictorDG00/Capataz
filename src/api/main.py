# src/api/main.py
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from pathlib import Path

from src.api.routes import router

app = FastAPI(
    title="Capataz",
    description="Forja de Software Autônoma — Interface Web",
    version="1.0.0",
)

_STATIC_DIR = Path(__file__).parent / "static"
_STATIC_DIR.mkdir(exist_ok=True)

app.include_router(router)
