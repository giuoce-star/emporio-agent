"""Tools que o modelo pode chamar. Determinísticas, sobre os CSVs.

Cada tool devolve um dict serializável; `executar` faz o despacho a partir do
nome e dos argumentos que o modelo enviou.
"""

import json
import re
from datetime import date, timedelta

from agente import precos
from agente.dados import Dados, carregar, normalizar

STATUS_PEDIDO = {
    "pending": "Aguardando pagamento/aprovação",
    "confirmed": "Pagamento confirmado, em separação",
    "shipped": "Enviado",
    "delivered": "Entregue",
    "cancelled": "Cancelado",
}
FORMAS_PAGAMENTO = {
    "pix": "PIX",
    "debit": "Cartão de débito",
    "boleto": "Boleto bancário",
    "credit_3x": "Cartão de crédito em 3x",
    "credit_6x": "Cartão de crédito em 6x",
    "credit_12x": "Cartão de crédito em 12x",
}

PALAVRAS_VAZIAS = set(
    "a o as os um uma uns umas de da do das dos e em no na nos nas para pra pro com "
    "sem por que qual quais tem voces voce vcs quero queria gostaria procuro procurando "
    "algum alguma me mim eu meu minha preco precos valor quanto custa loja".split()
)


def _radical(token: str) -> str:
    """Plural simples em português: violões -> violao, guitarras -> guitarra."""
    if token.endswith(("oes", "aes")):
        return token[:-3] + "ao"
    if token.endswith("s") and len(token) > 3:
        return token[:-1]
    return token


def _tokens(termo: str) -> list[str]:
    return [_radical(t) for t in normalizar(termo).split() if t not in PALAVRAS_VAZIAS]


def _disponibilidade(p) -> str:
    if p["status"] == "discontinued":
        return "descontinuado (não faz mais parte do catálogo)"
    if p["status"] == "coming_soon":
        return "em breve (ainda não disponível para compra)"
    if p["stock_quantity"] <= 0:
        return "esgotado no momento"
    return "disponível"


def _vendavel(p) -> bool:
    return p["status"] == "active" and p["stock_quantity"] > 0


def _promocao_ativa(dados: Dados, produto_id: int) -> dict | None:
    promos = dados.promocoes
    ativas = promos[(promos["product_id"] == produto_id) & promos["is_active"]]
    return precos.escolher_promocao(ativas.to_dict("records"))


def _preco_final(dados: Dados, p) -> float:
    promo = _promocao_ativa(dados, p["product_id"])
    if promo:
        return float(precos.aplicar_desconto(p["price_brl"], promo["discount_percent"]))
    return float(p["price_brl"])


def _resumo_produto(dados: Dados, p) -> dict:
    item = {
        "produto_id": int(p["product_id"]),
        "nome": p["name"],
        "categoria": p["categoria"],
        "disponibilidade": _disponibilidade(p),
    }
    if p["status"] == "active":
        preco = precos.calcular_preco(p["price_brl"], _promocao_ativa(dados, p["product_id"]))
        item["preco_final"] = preco["preco_final"]
        if preco["promocao"]:
            item["promocao"] = preco["promocao"]
        item["preco_pix"] = preco["pix"]["preco_pix"]
    if p["confiavel"]:
        item["descricao"] = p["description"]
    return item


def _alternativas(dados: Dados, p, limite: int = 3) -> list[dict]:
    produtos = dados.produtos
    candidatos = produtos[
        (produtos["category_id"] == p["category_id"])
        & (produtos["product_id"] != p["product_id"])
        & (produtos["status"] == "active")
        & (produtos["stock_quantity"] > 0)
    ]
    mais_proximos = (candidatos["price_brl"] - p["price_brl"]).abs().sort_values().index[:limite]
    return [_resumo_produto(dados, candidatos.loc[i]) for i in mais_proximos]


def buscar_produtos(
    termo: str = "",
    categoria: str = "",
    preco_min: float | None = None,
    preco_max: float | None = None,
    limite: int = 8,
    dados: Dados | None = None,
) -> dict:
    dados = dados or carregar()
    produtos = dados.produtos

    if categoria:
        alvo = _radical(normalizar(categoria))
        produtos = produtos[produtos["categoria"].map(lambda c: alvo in normalizar(c))]

    tokens = _tokens(termo)
    if tokens:
        def pontos(p) -> int:
            return sum(t in p["busca"] or t in p["busca_compacta"] for t in tokens)

        placar = produtos.apply(pontos, axis=1) if len(produtos) else produtos["product_id"]
        # Primeiro exige todos os termos; se nada casar, aceita casamento parcial.
        if (placar == len(tokens)).any():
            produtos = produtos[placar == len(tokens)]
        else:
            produtos = produtos[placar > 0]
            placar = placar[placar > 0]
            produtos = produtos.loc[placar.sort_values(ascending=False).index]

    if preco_min is not None or preco_max is not None:
        finais = produtos.apply(lambda p: _preco_final(dados, p), axis=1)
        filtro = finais.notna()
        if preco_min is not None:
            filtro &= finais >= preco_min
        if preco_max is not None:
            filtro &= finais <= preco_max
        produtos = produtos[filtro]

    # Vendáveis primeiro, preservando a ordem de relevância dentro de cada grupo.
    produtos = produtos.assign(_vendavel=produtos.apply(_vendavel, axis=1) if len(produtos) else [])
    produtos = produtos.sort_values("_vendavel", ascending=False, kind="stable")

    limite = max(1, min(int(limite), 15))
    resultado = {
        "total_encontrado": int(len(produtos)),
        "produtos": [_resumo_produto(dados, p) for _, p in produtos.head(limite).iterrows()],
    }
    if not len(produtos):
        resultado["observacao"] = (
            "Nenhum produto encontrado no sistema com esses critérios. "
            "Não ofereça itens que não estejam no sistema."
        )
    return resultado


def consultar_preco(produto_id: int, dados: Dados | None = None) -> dict:
    dados = dados or carregar()
    try:
        p = dados.produtos.loc[int(produto_id)]
    except (KeyError, ValueError):
        return {"erro": f"Produto {produto_id} não encontrado no sistema."}

    resultado = {
        "produto_id": int(p["product_id"]),
        "nome": p["name"],
        "categoria": p["categoria"],
        "disponibilidade": _disponibilidade(p),
    }
    if p["status"] == "active":
        resultado["estoque"] = int(p["stock_quantity"])
        resultado["preco"] = precos.calcular_preco(
            p["price_brl"], _promocao_ativa(dados, p["product_id"])
        )

    promos = dados.promocoes
    encerradas = promos[(promos["product_id"] == p["product_id"]) & ~promos["is_active"]]
    if len(encerradas):
        resultado["promocoes_encerradas"] = [
            {"nome": r["description"], "desconto_percentual": int(r["discount_percent"])}
            for _, r in encerradas.iterrows()
        ]

    if p["confiavel"]:
        resultado["descricao"] = p["description"]
        resultado["especificacoes"] = p["specs"]
    else:
        resultado["observacao_detalhes"] = (
            "Detalhes técnicos deste item estão em revisão no sistema; "
            "não descreva características além do nome."
        )

    if not _vendavel(p):
        resultado["alternativas"] = _alternativas(dados, p)
    return resultado


def calcular_frete(cidade: str, valor_pedido: float) -> dict:
    return precos.calcular_frete(cidade, valor_pedido)


def prazos_troca_devolucao(
    data_recebimento: str, data_compra: str = "", hoje: date | None = None
) -> dict:
    """Situação de cada prazo do manual, em dias corridos, a partir das datas informadas."""
    hoje = hoje or date.today()
    try:
        recebimento = date.fromisoformat(data_recebimento)
        compra = date.fromisoformat(data_compra) if data_compra else None
    except ValueError:
        return {"erro": "Datas devem estar no formato AAAA-MM-DD."}
    if recebimento > hoje or (compra and compra > hoje):
        return {"erro": "As datas informadas estão no futuro; confirme com o cliente."}

    def prazo(inicio: date, dias: int) -> dict:
        limite = inicio + timedelta(days=dias)
        return {
            "conta_a_partir_de": inicio.strftime("%d/%m/%Y"),
            "prazo_dias": dias,
            "data_limite": limite.strftime("%d/%m/%Y"),
            "dias_decorridos": (hoje - inicio).days,
            "dentro_do_prazo": hoje <= limite,
        }

    resultado = {
        "hoje": hoje.strftime("%d/%m/%Y"),
        "arrependimento": {
            **prazo(recebimento, 7),
            "condicoes": "Compra online; embalagem original, sem uso, com acessórios e manuais. "
            "Frete de devolução por conta da loja; reembolso na mesma forma de pagamento em até 10 dias úteis.",
        },
        "troca_por_preferencia": {
            **prazo(recebimento, 7),
            "condicoes": "Produto em perfeito estado e na embalagem original, sujeito à "
            "disponibilidade do item desejado; diferenças de valor cobradas ou reembolsadas.",
        },
        "troca_por_defeito_na_loja": {
            **prazo(compra or recebimento, 30),
            "condicoes": "Defeito de fabricação; não cobre mau uso, quedas, umidade ou modificações. "
            "Depois do prazo, o caminho é a garantia (a loja pode intermediar com o fabricante).",
        },
        "garantia_legal": {
            **prazo(recebimento, 90),
            "condicoes": "Defeitos de fabricação, pelo Código de Defesa do Consumidor. A garantia "
            "do fabricante (6 meses a 2 anos, conforme o certificado) pode se somar a ela.",
        },
    }
    if not compra:
        resultado["observacao"] = (
            "Data da compra não informada: o prazo de troca por defeito foi contado a partir do "
            "recebimento. Confirme a data da compra se o resultado estiver no limite."
        )
    return resultado


def _so_digitos(texto: str) -> str:
    return re.sub(r"\D", "", texto or "")


def _identidade_confere(cliente, email_ou_telefone: str) -> bool:
    informado = (email_ou_telefone or "").strip().lower()
    if "@" in informado:
        return informado == str(cliente["email"]).strip().lower()
    digitos, cadastrado = _so_digitos(informado), _so_digitos(cliente["phone"])
    # Aceita com ou sem DDD/código do país, mas exige pelo menos o número completo.
    return len(digitos) >= 9 and (cadastrado.endswith(digitos) or digitos.endswith(cadastrado))


def status_pedido(
    numero_pedido: int,
    email_ou_telefone: str,
    dados: Dados | None = None,
    hoje: date | None = None,
) -> dict:
    dados = dados or carregar()
    hoje = hoje or date.today()
    falha = {
        "verificado": False,
        "erro": (
            "Não foi possível localizar um pedido com esse número e esse e-mail/telefone. "
            "Peça para o cliente conferir os dados."
        ),
    }
    try:
        pedido = dados.pedidos.loc[int(numero_pedido)]
    except (KeyError, ValueError):
        return falha  # mesma resposta para não revelar quais pedidos existem
    cliente = dados.clientes.loc[pedido["customer_id"]]
    if not _identidade_confere(cliente, email_ou_telefone):
        return falha

    itens = dados.itens[dados.itens["order_id"] == pedido["order_id"]]
    resultado = {
        "verificado": True,
        "primeiro_nome_cliente": cliente["name"].split()[0],
        "numero_pedido": int(pedido["order_id"]),
        "data_pedido": pedido["order_date"].strftime("%d/%m/%Y"),
        "status": STATUS_PEDIDO.get(pedido["status"], pedido["status"]),
        "itens": [
            {"produto": dados.produtos.loc[i["product_id"], "name"], "quantidade": int(i["quantity"])}
            for _, i in itens.iterrows()
        ],
        "valor_total": precos.formatar_brl(pedido["total_brl"]),
        "forma_pagamento": FORMAS_PAGAMENTO.get(pedido["payment_method"], pedido["payment_method"]),
    }
    if isinstance(pedido["tracking_code"], str):
        resultado["codigo_rastreio"] = pedido["tracking_code"]
    previsao = pedido["estimated_delivery"]
    if previsao is not None:
        resultado["previsao_entrega"] = previsao.strftime("%d/%m/%Y")
    if isinstance(pedido["notes"], str):
        resultado["observacao"] = pedido["notes"]

    em_aberto = pedido["status"] in ("pending", "confirmed", "shipped")
    if em_aberto and previsao is not None and previsao < hoje:
        resultado["alerta"] = (
            f"A previsão de entrega ({previsao:%d/%m/%Y}) já passou e o pedido não consta como "
            "entregue. Seja transparente e oriente o cliente a falar com a equipe pelo "
            "WhatsApp (67) 3321-4500 para verificar."
        )
    elif pedido["status"] in ("pending", "confirmed") and (hoje - pedido["order_date"]).days > 15:
        dias = (hoje - pedido["order_date"]).days
        resultado["alerta"] = (
            f"O pedido está com esse status há {dias} dias, acima do esperado. Seja "
            "transparente e oriente o cliente a falar com a equipe pelo WhatsApp "
            "(67) 3321-4500 para verificar."
        )
    return resultado


SCHEMAS = [
    {
        "name": "buscar_produtos",
        "description": (
            "Busca instrumentos no catálogo da loja por texto livre (marca, modelo, tipo, "
            "característica), categoria e/ou faixa de preço. Retorna disponibilidade, preço "
            "final já calculado (com promoção ativa, se houver) e preço no PIX. Use sempre "
            "antes de falar de qualquer produto, preço ou estoque."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "termo": {
                    "type": "string",
                    "description": "Texto de busca, ex.: 'takamine gd20', 'violão nylon iniciante', 'ukulele tenor'.",
                },
                "categoria": {
                    "type": "string",
                    "description": "Categoria, ex.: 'Violões', 'Guitarras', 'Ukuleles', 'Baixos', 'Baterias', 'Teclados'.",
                },
                "preco_min": {"type": "number", "description": "Preço final mínimo em reais."},
                "preco_max": {"type": "number", "description": "Preço final máximo em reais."},
                "limite": {"type": "integer", "description": "Máximo de resultados (padrão 8, até 15)."},
            },
        },
    },
    {
        "name": "consultar_preco",
        "description": (
            "Detalhes de um produto pelo ID: disponibilidade, estoque, preço de tabela, "
            "promoção ativa (com preço original e percentual), promoções já encerradas, "
            "preço no PIX, parcelamento máximo sem juros e alternativas se estiver "
            "indisponível. Todos os valores já vêm calculados: repasse-os sem refazer contas."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "produto_id": {"type": "integer", "description": "ID retornado por buscar_produtos."}
            },
            "required": ["produto_id"],
        },
    },
    {
        "name": "calcular_frete",
        "description": (
            "Regra de frete para a cidade do cliente e o valor total do pedido. Na região "
            "metropolitana de Campo Grande calcula o valor; nas demais cidades informa que "
            "é preciso cotação pelo CEP."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "cidade": {"type": "string", "description": "Cidade de entrega."},
                "valor_pedido": {"type": "number", "description": "Valor total do pedido em reais."},
            },
            "required": ["cidade", "valor_pedido"],
        },
    },
    {
        "name": "prazos_troca_devolucao",
        "description": (
            "Calcula, para as datas informadas, a situação de cada prazo: devolução por "
            "arrependimento, troca por preferência, troca por defeito na loja e garantia legal. "
            "Use sempre que o cliente quiser devolver ou trocar algo, em vez de contar dias."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "data_recebimento": {
                    "type": "string",
                    "description": "Data em que o cliente recebeu o produto, AAAA-MM-DD.",
                },
                "data_compra": {
                    "type": "string",
                    "description": "Data da compra, AAAA-MM-DD, se o cliente souber.",
                },
            },
            "required": ["data_recebimento"],
        },
    },
    {
        "name": "status_pedido",
        "description": (
            "Consulta o status de um pedido. Exige o número do pedido E o e-mail ou telefone "
            "do cadastro, informados pelo próprio cliente na conversa. Nunca chame sem os dois."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "numero_pedido": {"type": "integer"},
                "email_ou_telefone": {"type": "string"},
            },
            "required": ["numero_pedido", "email_ou_telefone"],
        },
    },
]

_FUNCOES = {
    "buscar_produtos": buscar_produtos,
    "consultar_preco": consultar_preco,
    "calcular_frete": calcular_frete,
    "prazos_troca_devolucao": prazos_troca_devolucao,
    "status_pedido": status_pedido,
}


def executar(nome: str, argumentos: dict) -> tuple[str, bool]:
    """Executa a tool e devolve (JSON do resultado, houve_erro)."""
    funcao = _FUNCOES.get(nome)
    if funcao is None:
        return json.dumps({"erro": f"Tool desconhecida: {nome}"}, ensure_ascii=False), True
    try:
        resultado = funcao(**argumentos)
    except (TypeError, ValueError) as exc:
        return json.dumps({"erro": f"Argumentos inválidos: {exc}"}, ensure_ascii=False), True
    return json.dumps(resultado, ensure_ascii=False, default=str), "erro" in resultado
