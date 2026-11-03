"""O gerador de exemplos usa o Sonnet por padrão. Não chama a API: só importa o script."""

import os
import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
LER_MODELO = (
    "import runpy; "
    "print(runpy.run_path('examples/gerar_exemplos.py', run_name='teste')['MODEL'])"
)


def _modelo(env_extra: dict) -> str:
    env = {k: v for k, v in os.environ.items() if k != "MODEL"} | env_extra
    saida = subprocess.run(
        [sys.executable, "-c", LER_MODELO], cwd=RAIZ, env=env,
        capture_output=True, text=True, check=True,
    )
    return saida.stdout.strip()


def test_sonnet_por_padrao_mesmo_com_haiku_no_env():
    # O .env do projeto define MODEL=claude-haiku-5-5; o gerador tem que ignorá-lo.
    assert _modelo({}) == "claude-sonnet-5-5"


def test_model_no_ambiente_sobrescreve():
    assert _modelo({"MODEL": "claude-haiku-5-5"}) == "claude-haiku-5-5"
