"""Testes para FileWriter — Sprint 02 do Ciclo03."""
import os
import pytest
from src.core.writer import FileWriter, _validate_path


SAMPLE_OUTPUT = """
Aqui está o código que implementei para a sprint.

### Arquivo: src/api/routes.py
```python
def hello():
    return "world"
```

### Arquivo: tests/test_routes.py
```python
def test_hello():
    assert hello() == "world"
```

### Arquivo: src/utils/helper.py
```javascript
export const add = (a, b) => a + b;
```
"""

OUTPUT_SINGLE = """
### Arquivo: src/main.py
```python
print("capataz")
```
"""

OUTPUT_NO_BLOCKS = "Aqui está minha análise sem blocos de arquivo."


@pytest.fixture
def writer():
    return FileWriter()


@pytest.fixture(autouse=True)
def workdir(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)


# --- _validate_path ---

def test_path_valido_dentro_do_base(tmp_path):
    result = _validate_path("src/api.py", str(tmp_path))
    assert result == str(tmp_path / "src" / "api.py")


def test_path_traversal_simples_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="Path traversal"):
        _validate_path("../segredo.txt", str(tmp_path))


def test_path_traversal_absoluto_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="Path traversal"):
        _validate_path("/etc/passwd", str(tmp_path))


def test_path_traversal_embutido_rejeitado(tmp_path):
    with pytest.raises(ValueError, match="Path traversal"):
        _validate_path("src/../../etc/passwd", str(tmp_path))


# --- FileWriter.write_from_output ---

def test_grava_tres_arquivos(writer, tmp_path):
    written = writer.write_from_output(SAMPLE_OUTPUT, str(tmp_path))
    assert len(written) == 3


def test_conteudo_correto(writer, tmp_path):
    writer.write_from_output(SAMPLE_OUTPUT, str(tmp_path))
    routes = (tmp_path / "src" / "api" / "routes.py").read_text()
    assert 'def hello' in routes
    assert '"world"' in routes


def test_cria_diretorios_intermediarios(writer, tmp_path):
    writer.write_from_output(SAMPLE_OUTPUT, str(tmp_path))
    assert (tmp_path / "src" / "api").is_dir()
    assert (tmp_path / "tests").is_dir()


def test_sem_blocos_retorna_lista_vazia(writer, tmp_path):
    written = writer.write_from_output(OUTPUT_NO_BLOCKS, str(tmp_path))
    assert written == []


def test_bloco_unico(writer, tmp_path):
    written = writer.write_from_output(OUTPUT_SINGLE, str(tmp_path))
    assert len(written) == 1
    assert (tmp_path / "src" / "main.py").exists()


def test_path_traversal_no_output_levanta_erro(writer, tmp_path):
    malicious = """
### Arquivo: ../../../etc/passwd
```
root:x:0:0
```
"""
    with pytest.raises(ValueError, match="Path traversal"):
        writer.write_from_output(malicious, str(tmp_path))


def test_base_path_padrao_usa_diretorio_atual(writer, tmp_path):
    written = writer.write_from_output(OUTPUT_SINGLE)
    assert len(written) == 1
    assert os.path.exists(written[0])
