"""Único ponto de contato com o provedor do modelo (Anthropic).

O resto do código usa só `LLM.responder` e os construtores de mensagem daqui.
Trocar de provedor significa reescrever este arquivo e manter essa interface.
"""

from dataclasses import dataclass, field

import anthropic

from agente.config import EFFORT, MAX_TOKENS, MODEL


class ErroLLM(Exception):
    """Falha ao falar com o modelo, com mensagem segura para log."""


@dataclass
class ChamadaTool:
    id: str
    nome: str
    argumentos: dict


@dataclass
class Resposta:
    texto: str
    chamadas: list[ChamadaTool]
    motivo_parada: str
    conteudo_bruto: list[dict] = field(repr=False)  # blocos para devolver no histórico
    uso: dict = field(default_factory=dict)


class LLM:
    def __init__(self, modelo: str = MODEL, cliente: anthropic.Anthropic | None = None):
        self.modelo = modelo
        self.cliente = cliente or anthropic.Anthropic()

    def responder(self, system: list[dict], mensagens: list[dict], tools: list[dict]) -> Resposta:
        try:
            r = self.cliente.messages.create(
                model=self.modelo,
                max_tokens=MAX_TOKENS,
                system=system,
                messages=mensagens,
                tools=tools,
                output_config={"effort": EFFORT},
            )
        except anthropic.AuthenticationError as exc:
            raise ErroLLM("Chave da API inválida ou ausente (ANTHROPIC_API_KEY).") from exc
        except anthropic.BadRequestError as exc:
            raise ErroLLM(f"Requisição recusada pela API: {exc.message}") from exc
        except anthropic.RateLimitError as exc:
            raise ErroLLM("Limite de requisições atingido; tente de novo em instantes.") from exc
        except anthropic.APIStatusError as exc:
            raise ErroLLM(f"Erro da API ({exc.status_code}).") from exc
        except anthropic.APIConnectionError as exc:
            raise ErroLLM("Sem conexão com a API.") from exc

        chamadas = [
            ChamadaTool(b.id, b.name, dict(b.input)) for b in r.content if b.type == "tool_use"
        ]
        texto = "\n".join(b.text for b in r.content if b.type == "text").strip()
        if r.stop_reason == "refusal":
            texto = texto or "Desculpe, não consigo ajudar com isso por aqui."
        return Resposta(
            texto=texto,
            chamadas=chamadas,
            motivo_parada=r.stop_reason,
            # Blocos inteiros (inclusive thinking) voltam ao histórico sem alteração.
            conteudo_bruto=[b.to_dict() for b in r.content],
            uso={
                "entrada": r.usage.input_tokens,
                "saida": r.usage.output_tokens,
                "cache_lido": r.usage.cache_read_input_tokens or 0,
                "cache_escrito": r.usage.cache_creation_input_tokens or 0,
            },
        )


def mensagem_usuario(texto: str) -> dict:
    return {"role": "user", "content": texto}


def mensagem_assistente(resposta: Resposta) -> dict:
    return {"role": "assistant", "content": resposta.conteudo_bruto}


def mensagem_resultados(resultados: list[tuple[str, str, bool]]) -> dict:
    """Todos os resultados de uma rodada numa única mensagem: (id, conteúdo, erro)."""
    return {
        "role": "user",
        "content": [
            {"type": "tool_result", "tool_use_id": id_, "content": conteudo, "is_error": erro}
            for id_, conteudo, erro in resultados
        ],
    }


def bloco_system(texto: str) -> dict:
    return {"type": "text", "text": texto}
