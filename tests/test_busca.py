from agente import tools
from agente.dados import normalizar


def ids(resultado):
    return [p["produto_id"] for p in resultado["produtos"]]


def test_normalizar():
    assert normalizar("Violão Elétrico AÇO") == "violao eletrico aco"
    assert normalizar("GN-15") == "gn 15"


def test_busca_modelo_com_variacoes_de_escrita():
    for termo in ["Takamine GD20", "takamine gd-20", "GD 20", "gd20"]:
        assert ids(tools.buscar_produtos(termo)) == [95], termo


def test_busca_sem_acento_e_plural():
    resultado = tools.buscar_produtos("violoes eletricos aço")
    assert resultado["total_encontrado"] > 0
    assert all(p["categoria"] == "Violões" for p in resultado["produtos"])


def test_busca_por_categoria_e_preco_final():
    resultado = tools.buscar_produtos(categoria="ukulele", preco_max=200, limite=15)
    assert set(ids(resultado)) == {116, 118, 119}


def test_filtro_de_preco_usa_preco_promocional():
    # 121 custa 549,00 de tabela, 439,20 com a promoção de 20%
    assert 121 in ids(tools.buscar_produtos(categoria="ukulele", preco_max=450, limite=15))


def test_acessorio_nao_existe_no_catalogo():
    resultado = tools.buscar_produtos("palheta")
    assert resultado["total_encontrado"] == 0
    assert "observacao" in resultado


def test_casamento_parcial_ignora_descricao():
    # "alto" aparece em "volume alto" na descrição de um violão: não deve vir.
    assert tools.buscar_produtos("saxofone alto")["total_encontrado"] == 0
    parcial = tools.buscar_produtos("yamaha saxofone")
    assert parcial["total_encontrado"] > 0 and "em parte" in parcial["observacao"]


def test_vendaveis_aparecem_primeiro():
    resultado = tools.buscar_produtos("7 cordas", limite=15)
    disponibilidades = [p["disponibilidade"] for p in resultado["produtos"]]
    assert disponibilidades[-1].startswith("descontinuado")  # 113
    assert disponibilidades[0] == "disponível"


def test_descricao_inconsistente_nao_vaza():
    resultado = tools.consultar_preco(142)  # nome Korg, descrição de um Roland
    assert "descricao" not in resultado and "especificacoes" not in resultado
    assert ids(tools.buscar_produtos("roland")) == [144]  # só pelo nome


def test_consultar_preco_promocao_ativa():
    resultado = tools.consultar_preco(94)
    assert resultado["preco"]["promocao"]["desconto_percentual"] == 8
    assert resultado["preco"]["pix"]["aplica_desconto"] is False


def test_consultar_preco_promocao_expirada():
    resultado = tools.consultar_preco(91)  # Black Friday 30%, inativa
    assert resultado["preco"]["promocao"] is None
    assert resultado["preco"]["preco_final"] == "R$ 899,00"
    assert resultado["promocoes_encerradas"][0]["nome"] == "Black Friday"


def test_indisponiveis_sem_preco_e_com_alternativas():
    descontinuado = tools.consultar_preco(136)  # descontinuado, mas com estoque 13
    assert "preco" not in descontinuado and "estoque" not in descontinuado
    assert descontinuado["alternativas"]
    em_breve = tools.consultar_preco(130)
    assert em_breve["disponibilidade"].startswith("em breve")
    esgotado = tools.consultar_preco(96)
    assert esgotado["disponibilidade"] == "esgotado no momento"
    assert all(a["disponibilidade"] == "disponível" for a in esgotado["alternativas"])


def test_produto_inexistente():
    assert "erro" in tools.consultar_preco(9999)
