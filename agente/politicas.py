"""Texto do manual de políticas, extraído do PDF uma vez por processo.

O manual tem ~8 páginas (~4 mil tokens): cabe inteiro no prompt de sistema,
então não há RAG. O modo "layout" do pypdf preserva parágrafos e tabelas; o
modo padrão quebra uma palavra por linha neste PDF.
"""

import re
from functools import lru_cache
from pathlib import Path

from pypdf import PdfReader

from agente.config import POLITICAS_PDF

_CABECALHO = re.compile(r"^Empório da Música\s+Manual de Políticas e Procedimentos$")
_RODAPE = re.compile(r"^Página \d+$")


def limpar(texto: str) -> str:
    linhas = []
    for linha in texto.splitlines():
        linha = linha.strip()
        if _CABECALHO.match(linha) or _RODAPE.match(linha):
            continue
        linha = re.sub(r"^•\s+", "- ", linha)
        linha = re.sub(r"\s{3,}", " | ", linha)  # colunas de tabela
        linhas.append(linha)
    return re.sub(r"\n{3,}", "\n\n", "\n".join(linhas)).strip()


@lru_cache(maxsize=1)
def texto_politicas(caminho: Path = POLITICAS_PDF) -> str:
    leitor = PdfReader(caminho)
    return limpar("\n".join(p.extract_text(extraction_mode="layout") for p in leitor.pages))
