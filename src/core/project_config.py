# src/core/project_config.py
from __future__ import annotations

from typing import Optional

import yaml
from pydantic import BaseModel, ValidationError

_DEFAULT_PATH = ".capataz.yaml"


class ProjectInfo(BaseModel):
    name: str = "Projeto sem nome"
    description: str = ""
    language: str = "python"
    framework: str = ""
    run_command: str = ""
    test_command: str = "pytest tests/"


class AgentsConfig(BaseModel):
    architect: str = "deepseek"
    developer: str = "deepseek"
    integrator: str = "deepseek"
    designer: str = "deepseek"


class LimitsConfig(BaseModel):
    max_tokens_per_session: int = 100_000
    max_retries_per_sprint: int = 3
    max_sprints_per_cycle: int = 10


class GitConfig(BaseModel):
    base_branch: str = "develop"
    target_repo: Optional[str] = None


class ProjectConfig(BaseModel):
    """
    Representação validada do arquivo `.capataz.yaml`.

    Sobrescreve os defaults de `core.config.Settings` por projeto,
    sem exigir alteração no `.env` global.
    """

    project: ProjectInfo = ProjectInfo()
    agents: AgentsConfig = AgentsConfig()
    limits: LimitsConfig = LimitsConfig()
    git: GitConfig = GitConfig()


def load_project_config(path: str = _DEFAULT_PATH) -> Optional[ProjectConfig]:
    """
    Lê e valida o arquivo `.capataz.yaml` do diretório atual.

    Returns:
        ProjectConfig se o arquivo existir e for válido.
        None se o arquivo não existir (graceful degradation — CLI continua).

    Raises:
        ValueError: se o arquivo existir mas tiver campos inválidos,
                    com mensagem descritiva do campo problemático.
    """
    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = yaml.safe_load(f) or {}
    except FileNotFoundError:
        return None

    try:
        return ProjectConfig.model_validate(raw)
    except ValidationError as e:
        first_error = e.errors()[0]
        field = " → ".join(str(loc) for loc in first_error["loc"])
        raise ValueError(
            f".capataz.yaml inválido no campo '{field}': {first_error['msg']}"
        ) from e
