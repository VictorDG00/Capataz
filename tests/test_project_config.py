"""Testes para core.project_config — Sprint 01 do Ciclo04."""
import pytest
from src.core.project_config import load_project_config, ProjectConfig


VALID_YAML = """
project:
  name: "Meu App"
  description: "Teste"
  language: python
  framework: fastapi
  run_command: "uvicorn main:app --reload"
  test_command: "pytest tests/"

agents:
  architect: claude
  developer: deepseek
  integrator: deepseek

limits:
  max_tokens_per_session: 50000
  max_retries_per_sprint: 2

git:
  base_branch: main
  target_repo: owner/repo
"""

MINIMAL_YAML = """
project:
  name: "Minimal"
"""

INVALID_YAML = """
project:
  name: "App"
limits:
  max_tokens_per_session: "nao-e-numero"
"""


@pytest.fixture(autouse=True)
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


def _write(content: str, name: str = ".capataz.yaml"):
    with open(name, "w") as f:
        f.write(content)


def test_arquivo_ausente_retorna_none():
    result = load_project_config()
    assert result is None


def test_yaml_valido_carregado():
    _write(VALID_YAML)
    config = load_project_config()
    assert config is not None
    assert config.project.name == "Meu App"
    assert config.agents.architect == "claude"
    assert config.limits.max_tokens_per_session == 50000
    assert config.git.base_branch == "main"
    assert config.git.target_repo == "owner/repo"


def test_yaml_minimo_usa_defaults():
    _write(MINIMAL_YAML)
    config = load_project_config()
    assert config.project.name == "Minimal"
    assert config.agents.developer == "deepseek"
    assert config.limits.max_retries_per_sprint == 3
    assert config.git.base_branch == "develop"


def test_yaml_invalido_levanta_valueerror():
    _write(INVALID_YAML)
    with pytest.raises(ValueError, match=".capataz.yaml inválido"):
        load_project_config()


def test_path_customizado(tmp_path):
    custom = tmp_path / "custom.yaml"
    custom.write_text("project:\n  name: Custom\n")
    config = load_project_config(str(custom))
    assert config.project.name == "Custom"


def test_yaml_vazio_usa_todos_defaults():
    _write("")
    config = load_project_config()
    assert isinstance(config, ProjectConfig)
    assert config.project.name == "Projeto sem nome"


def test_run_command_preservado():
    _write(VALID_YAML)
    config = load_project_config()
    assert config.project.run_command == "uvicorn main:app --reload"
