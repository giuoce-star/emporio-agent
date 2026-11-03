"""Configuração central: caminhos, variáveis de ambiente e modelo."""

import os
from pathlib import Path

from dotenv import load_dotenv

RAIZ = Path(__file__).resolve().parent.parent
load_dotenv(RAIZ / ".env")

DATA_DIR = RAIZ / "data"
SESSIONS_DIR = RAIZ / "sessions"
POLITICAS_PDF = DATA_DIR / "politicas_da_loja.pdf"

MODEL = os.getenv("MODEL", "claude-haiku-5-5")
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "1024"))
# Limite de rodadas de tool use por mensagem do cliente (proteção contra loops).
MAX_RODADAS_TOOLS = 6
