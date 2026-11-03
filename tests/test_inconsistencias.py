"""Tratamento defensivo das inconsistências dos dados (sem chamar a API)."""

from datetime import date, datetime

import pytest

from agente import config, tools
from agente.prompt import contexto_atual

HOJE = date(2026, 3, 25)


def test_reference_date_vazia_ou_valida():
    assert config._ler_data_referencia("") is None
    assert config._ler_data_referencia(None) is None
    assert config._ler_data_referencia(" 2026-03-25 ") == HOJE
    with pytest.raises(ValueError, match="REFERENCE_DATE"):
        config._ler_data_referencia("25/03/2026")


def test_hoje_usa_reference_date(monkeypatch):
    monkeypatch.setattr(config, "REFERENCE_DATE", HOJE)
    assert config.hoje() == HOJE
    # tools usam config.hoje() quando nenhuma data é passada
    assert tools.prazos_troca_devolucao("2026-03-20")["hoje"] == "25/03/2026"
    assert "alerta" not in tools.status_pedido(13, "fernanda.ribeiro@coldmail.com")
    monkeypatch.setattr(config, "REFERENCE_DATE", None)
    assert config.hoje() == date.today()


def test_contexto_do_prompt_usa_reference_date():
    assert "quarta-feira, 25/03/2026." in contexto_atual(referencia=HOJE)
    assert "03/11/2026 10:00" in contexto_atual(agora=datetime(2026, 11, 3, 10, 0), referencia=None)


def test_total_diferente_da_soma_e_item_em_breve():
    r = tools.status_pedido(3, "isabela.moreira@jmail.com", hoje=HOJE)
    assert r["valor_total"] == "R$ 3.450,00"  # o gravado, sem correção
    texto = " ".join(r["divergencias_no_cadastro"])
    assert "R$ 3.498,00" in texto and "em breve" in texto
    assert "como_tratar_divergencias" in r


def test_pix_sem_desconto_e_parcela_abaixo_do_minimo():
    pix = tools.status_pedido(1, "pedro.oliveira@jmail.com", hoje=HOJE)
    assert "PIX" in pix["divergencias_no_cadastro"][0]
    parcelado = tools.status_pedido(18, "gustavo.nunes@inlook.com", hoje=HOJE)
    assert parcelado["forma_pagamento"] == "Cartão de crédito em 12x"
    assert "abaixo da parcela mínima" in parcelado["divergencias_no_cadastro"][0]


def test_pedido_sem_divergencia_nao_traz_o_campo():
    r = tools.status_pedido(2, "thiago.barbosa@jmail.com", hoje=HOJE)
    assert "divergencias_no_cadastro" not in r


def test_cadastro_conflitante_e_estoque_apesar_do_status():
    descontinuado = tools.consultar_preco(136)
    assert "conflitantes" in descontinuado["aviso_cadastro"]
    assert "13 unidade(s)" in descontinuado["aviso_estoque"]
    assert "estoque" not in descontinuado and "preco" not in descontinuado
    assert "aviso_estoque" in tools.consultar_preco(130)
    assert "aviso_estoque" not in tools.consultar_preco(113)  # descontinuado sem estoque


def test_dado_inconsistente_sem_hipotese_sobre_a_causa():
    # A regra está no prompt...
    from agente.prompt import PERSONA_E_REGRAS

    regras = " ".join(PERSONA_E_REGRAS.split())
    assert "diga que não consegue explicar a divergência" in regras
    assert "Não levante hipóteses sobre a causa" in regras
    # ...e vem junto de cada aviso de dado inconsistente devolvido pelas tools.
    pedido = tools.status_pedido(3, "isabela.moreira@jmail.com", hoje=HOJE)
    produto = tools.consultar_preco(136)
    for orientacao in (
        pedido["como_tratar_divergencias"],
        produto["aviso_cadastro"],
        produto["aviso_estoque"],
    ):
        assert tools.SEM_HIPOTESE in orientacao
    # As divergências descrevem só o que consta, sem sugerir causa.
    assert "época" not in " ".join(pedido["divergencias_no_cadastro"])


def test_nome_truncado_mantido_como_esta():
    assert tools.consultar_preco(84)["nome"] == "Giannini GN-15 Nylon Cedr Natural"
