from datetime import date

from agente import tools

HOJE = date(2026, 11, 3)


def test_dentro_de_7_dias_tudo_vale():
    r = tools.prazos_troca_devolucao("2026-10-28", hoje=HOJE)
    assert r["arrependimento"]["dias_decorridos"] == 6
    assert r["arrependimento"]["dentro_do_prazo"]
    assert r["troca_por_defeito_na_loja"]["dentro_do_prazo"]


def test_setimo_dia_ainda_vale_oitavo_nao():
    assert tools.prazos_troca_devolucao("2026-10-27", hoje=HOJE)["arrependimento"]["dentro_do_prazo"]
    assert not tools.prazos_troca_devolucao("2026-10-26", hoje=HOJE)["arrependimento"]["dentro_do_prazo"]


def test_defeito_conta_da_compra_e_garantia_do_recebimento():
    r = tools.prazos_troca_devolucao("2026-10-10", data_compra="2026-09-30", hoje=HOJE)
    assert not r["arrependimento"]["dentro_do_prazo"]
    assert r["troca_por_defeito_na_loja"]["data_limite"] == "30/10/2026"
    assert not r["troca_por_defeito_na_loja"]["dentro_do_prazo"]
    assert r["garantia_legal"]["dentro_do_prazo"]
    assert "observacao" not in r


def test_prompt_proibe_sugerir_excecao_de_prazo():
    # Visto no exemplo 02: "Se quiser pedir uma exceção ... a equipe pode confirmar".
    from agente.prompt import PERSONA_E_REGRAS

    regras = " ".join(PERSONA_E_REGRAS.split())
    assert "a política não prevê exceção" in regras
    assert "sem sugerir que o cliente peça exceção" in regras


def test_datas_invalidas():
    assert "erro" in tools.prazos_troca_devolucao("03/11/2026", hoje=HOJE)
    assert "erro" in tools.prazos_troca_devolucao("2026-12-01", hoje=HOJE)


def test_prompt_nao_define_canal_do_retorno_da_reclamacao():
    # Visto no exemplo 04: "O retorno vem em até 24 horas úteis, pelo telefone (67) 99456-7890".
    from agente.prompt import PERSONA_E_REGRAS

    regras = " ".join(PERSONA_E_REGRAS.split())
    assert "diga só que ela retorna em até 24 horas úteis" in regras
    assert "Não diga por qual canal nem por qual telefone ou e-mail" in regras
