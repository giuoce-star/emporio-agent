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
# O thinking adaptativo conta dentro de max_tokens; 1024 truncaria respostas.
MAX_TOKENS = int(os.getenv("MAX_TOKENS", "4096"))
EFFORT = os.getenv("EFFORT", "medium")
# Limite de rodadas de tool use por mensagem do cliente (proteção contra loops).
MAX_RODADAS_TOOLS = 6
