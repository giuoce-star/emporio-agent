"""Carga dos CSVs de data/ e normalização para busca.

Os arquivos originais não são alterados: toda limpeza fica aqui, em código.
"""

import json
import re
import unicodedata
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import pandas as pd

from agente.config import DATA_DIR

# Produtos cujo nome, descrição e specs se contradizem (ex.: "Korg Synth 1 Pro" com
# descrição de um Roland de 88 teclas e specs de 61). Confiamos em nome, preço,
# estoque e status, e não repassamos descrição nem specs ao modelo.
PRODUTOS_DESCRICAO_INCONSISTENTE = set(range(135, 145))


def normalizar(texto) -> str:
    """Minúsculas, sem acento e só com letras/dígitos separados por espaço."""
    if texto is None or (isinstance(texto, float) and pd.isna(texto)):
        return ""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    return " ".join(re.sub(r"[^a-z0-9]+", " ", texto.lower()).split())


@dataclass(frozen=True)
class Dados:
    produtos: pd.DataFrame
    categorias: pd.DataFrame
    promocoes: pd.DataFrame
    pedidos: pd.DataFrame
    itens: pd.DataFrame
    clientes: pd.DataFrame


def _ler(pasta: Path, nome: str) -> pd.DataFrame:
    return pd.read_csv(pasta / nome, encoding="utf-8")


def carregar_de(pasta: Path) -> Dados:
    categorias = _ler(pasta, "categories.csv")
    produtos = _ler(pasta, "products.csv").merge(
        categorias[["category_id", "name"]].rename(columns={"name": "categoria"}),
        on="category_id",
        how="left",
    )
    produtos["confiavel"] = ~produtos["product_id"].isin(PRODUTOS_DESCRICAO_INCONSISTENTE)
    produtos["specs"] = produtos["specs"].map(json.loads)

    # Texto de busca: nome + categoria + descrição (só a dos produtos confiáveis,
    # para a busca não achar um "Roland" pela descrição de um Korg).
    def texto_busca(p) -> str:
        partes = [p["name"], p["categoria"]]
        if p["confiavel"]:
            partes.append(p["description"])
        return normalizar(" ".join(partes))

    produtos["busca"] = produtos.apply(texto_busca, axis=1)
    # Versão sem espaços, para "gn15" casar com "GN-15" e "gd 20" com "GD20".
    produtos["busca_compacta"] = produtos["busca"].str.replace(" ", "", regex=False)
    # Só nome + categoria: base do casamento parcial, para uma palavra solta da
    # descrição ("volume alto") não trazer um violão na busca por "saxofone alto".
    produtos["busca_nome"] = (produtos["name"] + " " + produtos["categoria"]).map(normalizar)
    produtos["busca_nome_compacta"] = produtos["busca_nome"].str.replace(" ", "", regex=False)

    promocoes = _ler(pasta, "promotions.csv")
    promocoes["is_active"] = promocoes["is_active"].astype(bool)

    pedidos = _ler(pasta, "orders.csv")
    for coluna in ("order_date", "estimated_delivery"):
        pedidos[coluna] = pd.to_datetime(pedidos[coluna], format="%Y-%m-%d").dt.date
    pedidos["estimated_delivery"] = pedidos["estimated_delivery"].astype(object).where(
        pedidos["estimated_delivery"].notna(), None
    )

    return Dados(
        produtos=produtos.set_index("product_id", drop=False),
        categorias=categorias,
        promocoes=promocoes,
        pedidos=pedidos.set_index("order_id", drop=False),
        itens=_ler(pasta, "order_items.csv"),
        clientes=_ler(pasta, "customers.csv").set_index("customer_id", drop=False),
    )


@lru_cache(maxsize=1)
def carregar() -> Dados:
    return carregar_de(DATA_DIR)
