# src/core/security.py
import subprocess
import os
import shlex

class SecurityManager:
    """
    Gerencia a execução segura de comandos gerados por IA.
    Aplica o princípio de 'Privilégio Mínimo'.
    """

    def __init__(self):
        # Lista de comandos permitidos (Whitelisting)
        self.allowed_commands = ["pytest", "npm", "ruff", "bandit", "next build"]

    def run_isolated_command(self, command: str, timeout: int = 60):
        """
        Executa um comando em um subprocesso controlado.
        Idealmente, isso deveria disparar um container Docker temporário.
        """
        # Sanitização: shlex divide a string respeitando aspas
        args = shlex.split(command)
        
        if args[0] not in self.allowed_commands:
            return {"status": "error", "message": f"Comando '{args[0]}' não permitido pelo Capataz."}

        try:
            # Executa com limites de recurso
            result = subprocess.run(
                args,
                capture_output=True,
                text=True,
                timeout=timeout,
                check=False # Não queremos que o Python quebre se o teste falhar
            )
            
            return {
                "status": "success" if result.returncode == 0 else "failed",
                "stdout": result.stdout,
                "stderr": result.stderr,
                "exit_code": result.returncode
            }
        except subprocess.TimeoutExpired:
            return {"status": "error", "message": "Execução interrompida por Timeout."}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def run_security_scan(self, path: str = "."):
        """
        Roda o Bandit (SAST) no código gerado.
        """
        return self.run_isolated_command(f"bandit -r {path}")

security_manager = SecurityManager()