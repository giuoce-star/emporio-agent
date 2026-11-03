from agente import precos


def test_formatar_brl():
    assert precos.formatar_brl(1299) == "R$ 1.299,00"
    assert precos.formatar_brl(599.9) == "R$ 599,90"
    assert precos.formatar_brl(19567) == "R$ 19.567,00"


def test_pix_arredonda_meio_para_cima():
    # 599,90 * 0,95 = 569,905 -> 569,91 (float puro daria 569,90)
    resultado = precos.calcular_preco(599.9, None)
    assert resultado["pix"]["aplica_desconto"] is True
    assert resultado["pix"]["preco_pix"] == "R$ 569,91"
    assert resultado["promocao"] is None


def test_pix_nao_acumula_com_promocao():
    promo = {"description": "Desconto Exclusivo", "discount_percent": 18}
    resultado = precos.calcular_preco(2399, promo)
    assert resultado["promocao"]["preco_original"] == "R$ 2.399,00"
    assert resultado["promocao"]["desconto_percentual"] == 18
    assert resultado["promocao"]["preco_promocional"] == "R$ 1.967,18"
    assert resultado["pix"]["aplica_desconto"] is False
    assert resultado["pix"]["preco_pix"] == resultado["preco_final"] == "R$ 1.967,18"


def test_promocoes_nao_cumulativas_vale_a_maior():
    ativas = [
        {"description": "A", "discount_percent": 10},
        {"description": "B", "discount_percent": 25},
    ]
    assert precos.escolher_promocao(ativas)["description"] == "B"
    assert precos.escolher_promocao([]) is None


def test_parcelamento_por_faixa():
    # 7x a 12x: parcela mínima de R$ 100
    assert precos.parcelamento(2400)["max_parcelas"] == 12
    # 599,90 / 7 < 100, mas / 6 >= 80
    assert precos.parcelamento(599.9)["max_parcelas"] == 6
    # 159,90 / 3 = 53,30 >= 50
    assert precos.parcelamento(159.9)["max_parcelas"] == 3
    # abaixo de R$ 100 não parcela (2x daria menos de R$ 50)
    assert precos.parcelamento(90)["max_parcelas"] == 1


def test_frete_regiao_metropolitana():
    assert precos.calcular_frete("Campo Grande", 500.01)["frete"] == "Grátis"
    # "acima de R$ 500": exatamente 500 ainda paga
    assert precos.calcular_frete("campo grande", 500)["frete"] == "R$ 35,00"
    assert precos.calcular_frete("CAMPO GRANDE", 199.9)["frete"] == "R$ 35,00"


def test_frete_outras_cidades_pede_cep():
    resultado = precos.calcular_frete("Dourados", 5000)
    assert resultado["regiao_metropolitana"] is False
    assert "CEP" in resultado["frete"]
