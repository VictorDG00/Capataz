"""Testes para GitOps — Sprint 04 do Ciclo03."""
import pytest
from unittest.mock import patch, MagicMock

from src.core.git import GitOps, _slugify, _run_git


# --- Helpers ---

def test_slugify_basico():
    result = _slugify("Criar autenticacao JWT")
    assert result == "criar-autenticacao-jwt"


def test_slugify_limita_tamanho():
    longo = "a" * 100
    assert len(_slugify(longo, max_len=40)) <= 40


def test_slugify_remove_especiais():
    assert _slugify("feat: add @user endpoint!") == "feat-add-user-endpoint"


# --- GitOps ---

@pytest.fixture
def git(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    return GitOps(repo_path=str(tmp_path))


def test_create_branch_nome_correto(git):
    with patch("src.core.git._run_git") as mock_git:
        mock_git.return_value = ""
        branch = git.create_branch("Implementar login OAuth", role="developer")

    assert branch.startswith("sprint-")
    assert branch.endswith("-developer")
    assert "login" in branch or "implementar" in branch


def test_create_branch_chama_git_checkout(git):
    with patch("src.core.git._run_git") as mock_git:
        mock_git.return_value = ""
        git.create_branch("auth backend")

    calls = [c[0][0] for c in mock_git.call_args_list]
    assert any("checkout" in c for c in calls)
    assert any("fetch" in c for c in calls)


def test_commit_files_chama_git_add_e_commit(git):
    with patch("src.core.git._run_git") as mock_git:
        mock_git.return_value = "abc123"
        git.commit_files(["src/foo.py", "tests/test_foo.py"], "feat: add foo")

    calls = [c[0][0] for c in mock_git.call_args_list]
    add_calls = [c for c in calls if "add" in c]
    commit_calls = [c for c in calls if "commit" in c]
    assert len(add_calls) == 2
    assert len(commit_calls) == 1


def test_push_chama_git_push(git):
    with patch("src.core.git._run_git") as mock_git:
        mock_git.return_value = ""
        git.push("sprint-auth-developer")

    calls = [c[0][0] for c in mock_git.call_args_list]
    assert any("push" in c for c in calls)


def test_open_pr_chama_github_api(git, monkeypatch):
    monkeypatch.setenv("GITHUB_TOKEN", "ghp_fake_token")
    monkeypatch.setenv("TARGET_REPO", "owner/repo")

    # Reinicia settings para pegar o env
    import importlib
    import src.core.config as cfg_mod
    importlib.reload(cfg_mod)
    import src.core.git as git_mod
    importlib.reload(git_mod)

    mock_response = MagicMock()
    mock_response.json.return_value = {"html_url": "https://github.com/owner/repo/pull/42"}
    mock_response.raise_for_status = MagicMock()

    with patch("src.core.git.httpx.post", return_value=mock_response) as mock_post:
        ops = git_mod.GitOps()
        url = ops.open_pr("sprint-auth-developer", "sprint(01): auth", "## Sprint")

    assert url == "https://github.com/owner/repo/pull/42"
    mock_post.assert_called_once()
    call_kwargs = mock_post.call_args[1]
    assert "Authorization" in call_kwargs["headers"]
    assert "ghp_fake_token" in call_kwargs["headers"]["Authorization"]


def test_run_full_flow_sem_arquivos_retorna_none(git):
    result = git.run_full_flow("sprint", "01", [], "Ciclo01.md")
    assert result is None


def test_sem_github_token_levanta_erro(git):
    import os
    os.environ.pop("GITHUB_TOKEN", None)

    import importlib
    import src.core.config as cfg_mod
    importlib.reload(cfg_mod)
    import src.core.git as git_mod
    importlib.reload(git_mod)

    ops = git_mod.GitOps()
    with pytest.raises(RuntimeError, match="GITHUB_TOKEN"):
        ops.open_pr("branch", "title", "body")
