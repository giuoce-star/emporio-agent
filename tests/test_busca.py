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


def test_filtro_de_categoria_com_plural_em_oes_e_acentos():
    # Bug real: categoria="Violões" retornava 0 ("violao" não é substring de "violoes").
    por_termo = tools.buscar_produtos(termo="violão", limite=15)["total_encontrado"]
    for categoria in ["Violões", "violões", "violoes", "violão", "VIOLAO"]:
        resultado = tools.buscar_produtos(categoria=categoria, limite=15)
        assert resultado["total_encontrado"] == por_termo == 35, categoria
        assert {p["categoria"] for p in resultado["produtos"]} == {"Violões"}


def test_filtro_de_categoria_nomes_compostos_e_vazias():
    assert tools.buscar_produtos(categoria="Baterias e Percussão")["total_encontrado"] == 3
    assert tools.buscar_produtos(categoria="percussão")["total_encontrado"] == 3
    assert tools.buscar_produtos(categoria="teclado")["total_encontrado"] == 3
    assert tools.buscar_produtos(categoria="Guitarras")["total_encontrado"] == 5
    assert tools.buscar_produtos(categoria="sopro")["total_encontrado"] == 0  # sem produtos


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


def _valor(preco: str) -> float:
    return float(preco.removeprefix("R$ ").replace(".", "").replace(",", "."))


def test_ordem_por_preco_final_disponiveis_primeiro():
    resultado = tools.buscar_produtos("7 cordas", limite=15)
    produtos = resultado["produtos"]
    disponiveis = [p for p in produtos if p["disponibilidade"] == "disponível"]
    # disponíveis formam um bloco contínuo no início
    assert produtos[: len(disponiveis)] == disponiveis
    assert produtos[-1]["produto_id"] == 113  # descontinuado no fim
    precos = [_valor(p["preco_final"]) for p in disponiveis]
    assert precos == sorted(precos)


def test_ordem_usa_preco_promocional():
    # Ohana CK-20 (121): R$ 549,00 de tabela, R$ 439,20 com promoção -> vem antes do
    # Kalani KAL-500C (122), de R$ 479,00, que custaria menos pela tabela.
    produtos = tools.buscar_produtos(categoria="ukulele", limite=15)["produtos"]
    ids_ordem = [p["produto_id"] for p in produtos]
    assert ids_ordem.index(121) < ids_ordem.index(122)
    assert ids_ordem[-1] == 130  # "em breve" (sem preço) vai para o fim
    precos = [_valor(p["preco_final"]) for p in produtos if "preco_final" in p]
    assert precos == sorted(precos)


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


def test_alternativas_priorizam_caracteristicas_do_nome():
    # Bug visto no exemplo 03: para o Shelby SN-7C (7 cordas, nylon, descontinuado)
    # as alternativas eram violões de 6 cordas de aço, só pelo preço próximo.
    sete_cordas = [a["nome"] for a in tools.consultar_preco(113)["alternativas"]]
    assert all("7 Cordas" in n for n in sete_cordas)
    assert "Nylon" in sete_cordas[0]  # mais parecido (7 cordas + nylon) primeiro
    # Cor ("Sunburst") não conta como semelhança; formato ("Dreadnought") conta.
    dreadnought = [a["nome"] for a in tools.consultar_preco(96)["alternativas"]]
    assert all("Dreadnought" in n for n in dreadnought)
    assert all(a["disponibilidade"] == "disponível" for a in tools.consultar_preco(96)["alternativas"])


def test_prompt_manda_buscar_caracteristica_antes_de_negar():
    from agente.prompt import PERSONA_E_REGRAS

    regras = " ".join(PERSONA_E_REGRAS.split())
    assert "busque pela característica sem marca nem modelo" in regras


def test_produto_inexistente():
    assert "erro" in tools.consultar_preco(9999)
