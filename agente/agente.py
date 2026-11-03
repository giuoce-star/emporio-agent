"""Loop do agente: mensagem -> modelo -> tools -> resultados -> resposta."""

from collections.abc import Callable

from agente import llm as llm_mod
from agente import tools
from agente.config import MAX_RODADAS_TOOLS
from agente.prompt import contexto_atual, montar_system
from agente.sessao import Sessao

RESPOSTA_FALHA = (
    "Opa, tive um problema técnico aqui e não consegui concluir. Pode tentar de novo em "
    "instantes? Se preferir, fale com a gente no WhatsApp (67) 3321-4500."
)


class Agente:
    def __init__(
        self,
        sessao: Sessao | None = None,
        llm: llm_mod.LLM | None = None,
        ao_chamar_tool: Callable[[str, dict, str], None] | None = None,
    ):
        self.sessao = sessao or Sessao()
        self.llm = llm or llm_mod.LLM()
        self.ao_chamar_tool = ao_chamar_tool
        self.system = montar_system()
        self.uso_total = {"entrada": 0, "saida": 0, "cache_lido": 0, "cache_escrito": 0}

    def responder(self, texto_cliente: str) -> str:
        mensagens = self.sessao.mensagens
        inicio_turno = len(mensagens)
        mensagens.append(llm_mod.mensagem_usuario(texto_cliente))
        system = self.system + [llm_mod.bloco_system(contexto_atual())]

        try:
            for _ in range(MAX_RODADAS_TOOLS):
                resposta = self.llm.responder(system, mensagens, tools.SCHEMAS)
                for chave, valor in resposta.uso.items():
                    self.uso_total[chave] += valor
                mensagens.append(llm_mod.mensagem_assistente(resposta))
                if not resposta.chamadas:
                    break
                resultados = []
                for chamada in resposta.chamadas:
                    conteudo, erro = tools.executar(chamada.nome, chamada.argumentos)
                    if self.ao_chamar_tool:
                        self.ao_chamar_tool(chamada.nome, chamada.argumentos, conteudo)
                    resultados.append((chamada.id, conteudo, erro))
                mensagens.append(llm_mod.mensagem_resultados(resultados))
            else:
                # Estourou o limite de rodadas sem resposta final.
                del mensagens[inicio_turno:]
                return RESPOSTA_FALHA
        except llm_mod.ErroLLM:
            # Desfaz o turno para o histórico continuar válido na próxima mensagem.
            del mensagens[inicio_turno:]
            raise

        self.sessao.salvar()
        return resposta.texto or RESPOSTA_FALHA
