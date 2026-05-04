# src/core/git.py
import re
import subprocess
from typing import Optional

import httpx

from src.core.config import settings

_GITHUB_API = "https://api.github.com"


def _run_git(args: list[str], cwd: str = ".") -> str:
    """Executa um comando git e retorna stdout. Levanta RuntimeError em falha."""
    result = subprocess.run(
        ["git"] + args,
        capture_output=True,
        text=True,
        cwd=cwd,
    )
    if result.returncode != 0:
        raise RuntimeError(
            f"git {' '.join(args)} falhou (exit {result.returncode}):\n{result.stderr}"
        )
    return result.stdout.strip()


def _slugify(text: str, max_len: int = 40) -> str:
    """Converte texto em slug para uso em nomes de branch."""
    slug = re.sub(r"[^\w\s-]", "", text.lower())
    slug = re.sub(r"[\s_]+", "-", slug).strip("-")
    return slug[:max_len]


class GitOps:
    """
    Operações git no repositório-alvo: branch, commit, push e abertura de PR.

    Usa subprocess para comandos git locais e httpx para a GitHub API.
    Não usa PyGithub para manter dependências mínimas e comportamento previsível.

    Requer GITHUB_TOKEN e TARGET_REPO configurados em .env.
    O nó git no grafo só é adicionado quando GITHUB_TOKEN estiver presente.
    """

    def __init__(self, repo_path: str = "."):
        self.repo_path = repo_path

    def _token(self) -> str:
        if not settings.github_token:
            raise RuntimeError("GITHUB_TOKEN não configurado. Adicione ao .env.")
        return settings.github_token.get_secret_value()

    def _target_repo(self) -> str:
        if not settings.target_repo:
            raise RuntimeError("TARGET_REPO não configurado. Exemplo: owner/repo")
        return settings.target_repo

    def create_branch(self, sprint_name: str, role: str = "developer") -> str:
        """
        Cria branch a partir de GIT_BASE_BRANCH seguindo o padrão de CODING_STANDARDS.md:
        sprint-[nome-declarativo]-[role]

        Returns:
            Nome da branch criada.
        """
        slug = _slugify(sprint_name)
        branch_name = f"sprint-{slug}-{role}"

        base = settings.git_base_branch
        _run_git(["fetch", "origin", base], self.repo_path)
        _run_git(["checkout", "-B", branch_name, f"origin/{base}"], self.repo_path)
        return branch_name

    def commit_files(self, files: list[str], message: str) -> str:
        """
        Adiciona os arquivos ao stage e faz commit.

        Args:
            files: Lista de caminhos absolutos ou relativos ao repo.
            message: Mensagem de commit (Conventional Commits).

        Returns:
            Hash do commit criado.
        """
        for f in files:
            _run_git(["add", f], self.repo_path)
        _run_git(["commit", "-m", message], self.repo_path)
        return _run_git(["rev-parse", "HEAD"], self.repo_path)

    def push(self, branch_name: str) -> None:
        """Faz push da branch para o remote origin."""
        _run_git(["push", "--set-upstream", "origin", branch_name], self.repo_path)

    def open_pr(self, branch_name: str, title: str, body: str) -> str:
        """
        Abre um Pull Request via GitHub API.

        Args:
            branch_name: Branch de origem do PR.
            title: Título do PR.
            body: Body em Markdown.

        Returns:
            URL do PR criado.
        """
        token = self._token()
        repo = self._target_repo()
        base = settings.git_base_branch

        response = httpx.post(
            f"{_GITHUB_API}/repos/{repo}/pulls",
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
            },
            json={"title": title, "body": body, "head": branch_name, "base": base},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()["html_url"]

    def run_full_flow(
        self,
        sprint_name: str,
        sprint_number: str,
        files_written: list[str],
        cycle_file: str,
    ) -> Optional[str]:
        """
        Executa o fluxo completo: create_branch → commit → push → open_pr.

        Returns:
            URL do PR aberto, ou None se files_written estiver vazio.
        """
        if not files_written:
            return None

        branch = self.create_branch(sprint_name)
        commit_msg = f"sprint({sprint_number}): {_slugify(sprint_name, 60)}"
        self.commit_files(files_written, commit_msg)
        self.push(branch)

        pr_body = (
            f"## Sprint {sprint_number}: {sprint_name}\n\n"
            f"Implementado pelo Capataz a partir de `{cycle_file}`.\n\n"
            f"### Arquivos modificados\n"
            + "\n".join(f"- `{f}`" for f in files_written)
        )
        return self.open_pr(branch, commit_msg, pr_body)


git_ops = GitOps()
