"""Loop do agente com um LLM falso: nenhuma chamada à API."""

import json

import pytest

from agente.agente import RESPOSTA_FALHA, Agente
from agente.llm import ChamadaTool, ErroLLM, Resposta
from agente.sessao import Sessao


class LLMFalso:
    def __init__(self, roteiro):
        self.roteiro = list(roteiro)
        self.recebido = []

    def responder(self, system, mensagens, tools):
        self.recebido.append(json.loads(json.dumps(mensagens)))
        item = self.roteiro.pop(0)
        if isinstance(item, Exception):
            raise item
        return item


def resposta(texto="", chamadas=()):
    blocos = [{"type": "text", "text": texto}] if texto else []
    blocos += [{"type": "tool_use", "id": c.id, "name": c.nome, "input": c.argumentos} for c in chamadas]
    return Resposta(texto, list(chamadas), "tool_use" if chamadas else "end_turn", blocos)


@pytest.fixture
def sessao(tmp_path):
    return Sessao(id="teste", pasta=tmp_path)


def test_executa_tool_e_devolve_resultado(sessao):
    llm = LLMFalso([
        resposta(chamadas=[ChamadaTool("t1", "consultar_preco", {"produto_id": 95})]),
        resposta("O Takamine GD20 sai por R$ 2.199,00."),
    ])
    texto = Agente(sessao=sessao, llm=llm).responder("quanto custa o takamine gd20?")

    assert texto == "O Takamine GD20 sai por R$ 2.199,00."
    resultado = llm.recebido[1][-1]["content"][0]
    assert resultado["tool_use_id"] == "t1" and resultado["is_error"] is False
    assert json.loads(resultado["content"])["preco"]["preco_final"] == "R$ 2.199,00"
    # user, assistant(tool_use), user(tool_result), assistant(texto)
    assert [m["role"] for m in sessao.mensagens] == ["user", "assistant", "user", "assistant"]
    assert Sessao.carregar("teste", pasta=sessao.pasta).mensagens == sessao.mensagens


def test_erro_da_api_desfaz_o_turno(sessao):
    agente = Agente(sessao=sessao, llm=LLMFalso([resposta("oi!"), ErroLLM("fora do ar")]))
    agente.responder("olá")
    with pytest.raises(ErroLLM):
        agente.responder("e agora?")
    assert [m["role"] for m in sessao.mensagens] == ["user", "assistant"]


def test_limite_de_rodadas(sessao):
    chamada = ChamadaTool("t", "buscar_produtos", {"termo": "violão"})
    agente = Agente(sessao=sessao, llm=LLMFalso([resposta(chamadas=[chamada])] * 10))
    assert agente.responder("loop") == RESPOSTA_FALHA
    assert sessao.mensagens == []
