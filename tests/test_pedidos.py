import json
from datetime import date

from agente import tools

HOJE = date(2026, 11, 3)


def test_pedido_exige_identidade():
    assert tools.status_pedido(1, "email@errado.com", hoje=HOJE)["verificado"] is False
    assert tools.status_pedido(1, "", hoje=HOJE)["verificado"] is False
    # pedido inexistente recebe a mesma resposta (não revela o que existe)
    assert tools.status_pedido(999, "x@y.com", hoje=HOJE) == tools.status_pedido(
        1, "x@y.com", hoje=HOJE
    )


def test_pedido_por_email_ou_telefone():
    por_email = tools.status_pedido(1, " Pedro.Oliveira@jmail.com ", hoje=HOJE)
    assert por_email["verificado"] and por_email["status"] == "Entregue"
    for telefone in ["(67) 98432-1098", "67984321098", "98432-1098", "+55 67 98432-1098"]:
        assert tools.status_pedido(1, telefone, hoje=HOJE)["verificado"], telefone
    assert tools.status_pedido(1, "1098", hoje=HOJE)["verificado"] is False


def test_email_compartilhado_so_ve_o_proprio_pedido():
    # clientes 11 e 43 usam o mesmo e-mail; o pedido 10 é do 11
    assert tools.status_pedido(10, "bruno.martins@jmail.com", hoje=HOJE)["verificado"]


def test_pedido_cancelado_traz_motivo():
    resultado = tools.status_pedido(19, "pedro.oliveira@jmail.com", hoje=HOJE)
    assert resultado["status"] == "Cancelado"
    assert "Pagamento não confirmado" in resultado["observacao"]


def test_pedido_com_varios_itens_e_total_gravado():
    resultado = tools.status_pedido(3, "isabela.moreira@jmail.com", hoje=HOJE)
    assert resultado["itens"] == [{"produto": "Kala KA-ABP-CTG Barítono Cedar", "quantidade": 2}]
    assert resultado["valor_total"] == "R$ 3.450,00"  # valor gravado, não recalculado


def test_alerta_de_atraso():
    enviado = tools.status_pedido(8, "anacarol.ferreira@coldmail.com", hoje=HOJE)
    assert enviado["codigo_rastreio"] == "BRJL5544332BR"
    assert "alerta" in enviado
    no_prazo = tools.status_pedido(8, "anacarol.ferreira@coldmail.com", hoje=date(2026, 2, 20))
    assert "alerta" not in no_prazo


def test_executar_despacha_e_serializa():
    texto, erro = tools.executar("consultar_preco", {"produto_id": 95})
    assert not erro and json.loads(texto)["nome"].startswith("Takamine")
    _, erro = tools.executar("nao_existe", {})
    assert erro
    _, erro = tools.executar("consultar_preco", {"produto": 95})
    assert erro
