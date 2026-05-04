# src/core/writer.py
import os
import re

_FILE_BLOCK_PATTERN = re.compile(
    r"###\s+Arquivo:\s+(.+?)\n```(?:\w+)?\n(.*?)```",
    re.DOTALL,
)


def _validate_path(path: str, base_path: str) -> str:
    """
    Resolve o path relativo dentro de base_path e rejeita path traversal.

    Raises:
        ValueError: se o path resultante sair do base_path.
    """
    abs_base = os.path.realpath(base_path)
    abs_target = os.path.realpath(os.path.join(base_path, path))

    if not abs_target.startswith(abs_base + os.sep) and abs_target != abs_base:
        raise ValueError(
            f"Path traversal detectado: '{path}' resolve para fora de '{base_path}'. "
            "O Developer não pode gravar arquivos fora do repositório-alvo."
        )
    return abs_target


class FileWriter:
    """
    Parseia o output textual do Developer e grava arquivos no disco.

    O Developer deve usar o formato:

        ### Arquivo: caminho/relativo/ao/projeto.py
        ```python
        # conteúdo do arquivo
        ```

    Qualquer número de blocos pode aparecer no output. Blocos sem o
    cabeçalho `### Arquivo:` são ignorados.
    """

    def write_from_output(self, output: str, base_path: str = ".") -> list[str]:
        """
        Parseia blocos de código do output do Developer e grava no disco.

        Args:
            output: String com o output completo do Developer.
            base_path: Diretório raiz onde os arquivos serão gravados.
                       Padrão: diretório atual.

        Returns:
            Lista de caminhos absolutos dos arquivos gravados.

        Raises:
            ValueError: se algum path tentar sair de base_path (path traversal).
        """
        written: list[str] = []

        for match in _FILE_BLOCK_PATTERN.finditer(output):
            relative_path = match.group(1).strip()
            content = match.group(2)

            abs_path = _validate_path(relative_path, base_path)
            os.makedirs(os.path.dirname(abs_path), exist_ok=True)

            with open(abs_path, "w", encoding="utf-8") as f:
                f.write(content)

            written.append(abs_path)

        return written


file_writer = FileWriter()
