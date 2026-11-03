"""Regras de preço, pagamento e frete do manual, em funções puras.

Tudo que envolve dinheiro é calculado aqui, com Decimal, e nunca pelo modelo.
"""

from decimal import ROUND_HALF_UP, Decimal

from agente.dados import normalizar

CENTAVO = Decimal("0.01")
DESCONTO_PIX = Decimal("5")  # %
FRETE_FIXO = Decimal("35.00")
FRETE_GRATIS_ACIMA = Decimal("500.00")  # "acima de": R$ 500,00 exatos ainda paga frete

# Seção 3.1 do manual: (até N parcelas, parcela mínima). Para até 3x o texto diz
# "sem valor mínimo (exceto abaixo de R$ 50,00)"; lemos como parcela mínima de R$ 50.
FAIXAS_PARCELAMENTO = [(3, Decimal("50")), (6, Decimal("80")), (12, Decimal("100"))]

# O manual não lista os municípios da região metropolitana; só Campo Grande é
# tratada como certa. Demais cidades: cotação por CEP.
CIDADES_REGIAO_METROPOLITANA = {"campo grande"}


def dinheiro(valor) -> Decimal:
    return Decimal(str(valor)).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def formatar_brl(valor) -> str:
    texto = f"{dinheiro(valor):,.2f}"  # 1,299.00
    return "R$ " + texto.replace(",", "_").replace(".", ",").replace("_", ".")


def aplicar_desconto(preco, percentual) -> Decimal:
    preco = Decimal(str(preco))
    return dinheiro(preco * (Decimal(100) - Decimal(str(percentual))) / Decimal(100))


def escolher_promocao(promocoes_ativas: list[dict]) -> dict | None:
    """Promoções não são cumulativas: se houver mais de uma ativa, vale a maior."""
    if not promocoes_ativas:
        return None
    return max(promocoes_ativas, key=lambda p: p["discount_percent"])


def parcelamento(valor) -> dict:
    """Maior número de parcelas sem juros que respeita a parcela mínima da faixa."""
    valor = dinheiro(valor)
    for n in range(12, 1, -1):
        minimo = next(m for limite, m in FAIXAS_PARCELAMENTO if n <= limite)
        if valor / n >= minimo:
            return {"max_parcelas": n, "valor_parcela": formatar_brl(valor / n)}
    return {"max_parcelas": 1, "valor_parcela": formatar_brl(valor)}


def calcular_preco(preco_tabela, promocao: dict | None) -> dict:
    """Preço final de um produto, com promoção (se ativa) e condição PIX.

    `promocao` é a promoção ativa já escolhida (ver escolher_promocao) ou None.
    """
    tabela = dinheiro(preco_tabela)
    resultado = {"preco_tabela": formatar_brl(tabela)}

    if promocao:
        final = aplicar_desconto(tabela, promocao["discount_percent"])
        resultado["promocao"] = {
            "nome": promocao["description"],
            "desconto_percentual": int(promocao["discount_percent"]),
            "preco_original": formatar_brl(tabela),
            "preco_promocional": formatar_brl(final),
        }
        resultado["pix"] = {
            "aplica_desconto": False,
            "preco_pix": formatar_brl(final),
            "observacao": "O desconto de 5% no PIX não vale sobre preço promocional.",
        }
    else:
        final = tabela
        resultado["promocao"] = None
        resultado["pix"] = {
            "aplica_desconto": True,
            "preco_pix": formatar_brl(aplicar_desconto(tabela, DESCONTO_PIX)),
            "observacao": "5% de desconto pagando à vista no PIX.",
        }

    resultado["preco_final"] = formatar_brl(final)
    resultado["cartao_credito"] = parcelamento(final)
    return resultado


def calcular_frete(cidade: str, valor_pedido) -> dict:
    valor = dinheiro(valor_pedido)
    if normalizar(cidade) in CIDADES_REGIAO_METROPOLITANA:
        gratis = valor > FRETE_GRATIS_ACIMA
        return {
            "regiao_metropolitana": True,
            "frete": "Grátis" if gratis else formatar_brl(FRETE_FIXO),
            "prazo": "1 a 3 dias úteis, entrega por motoboy próprio",
            "regra": "Frete grátis acima de R$ 500,00; abaixo disso, taxa fixa de R$ 35,00.",
        }
    return {
        "regiao_metropolitana": False,
        "frete": "Cotação pelo CEP de destino",
        "prazo": "PAC 5 a 12, SEDEX 2 a 5 ou Jadlog 3 a 8 dias úteis",
        "regra": (
            "Fora da região metropolitana o valor depende do CEP, peso e dimensões; "
            "o atendimento não calcula. Instrumentos grandes podem exigir frete especial."
        ),
    }
