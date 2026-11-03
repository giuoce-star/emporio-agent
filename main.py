"""CLI do agente de atendimento da Empório da Música.

Uso:
    python main.py                 # nova conversa
    python main.py --sessao ID     # retoma sessions/ID.json
    python main.py --debug         # mostra as tools chamadas e o uso de tokens
"""

import argparse
import json
import sys

from agente.agente import RESPOSTA_FALHA, Agente
from agente.config import MODEL
from agente.llm import ErroLLM
from agente.sessao import Sessao

SAIR = {"sair", "exit", "quit", "tchau"}


def main() -> None:
    for fluxo in (sys.stdin, sys.stdout):
        fluxo.reconfigure(encoding="utf-8")  # acentos no console do Windows

    parser = argparse.ArgumentParser(description="Atendimento Empório da Música")
    parser.add_argument("--sessao", help="ID de uma sessão salva para retomar")
    parser.add_argument("--debug", action="store_true", help="mostra tools e tokens")
    args = parser.parse_args()

    sessao = Sessao.carregar(args.sessao) if args.sessao else Sessao()

    def mostrar_tool(nome: str, argumentos: dict, resultado: str) -> None:
        print(f"  [tool] {nome}({json.dumps(argumentos, ensure_ascii=False)})")
        print(f"         -> {resultado[:300]}{'...' if len(resultado) > 300 else ''}")

    agente = Agente(sessao=sessao, ao_chamar_tool=mostrar_tool if args.debug else None)
    print(f"Empório da Música — atendimento (modelo {MODEL}, sessão {sessao.id})")
    print("Digite 'sair' para encerrar.\n")

    while True:
        try:
            texto = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not texto:
            continue
        if texto.lower() in SAIR:
            break
        try:
            resposta = agente.responder(texto)
        except ErroLLM as exc:
            print(f"  [erro] {exc}", file=sys.stderr)
            resposta = RESPOSTA_FALHA
        print(f"\nEmpório: {resposta}\n")
        if args.debug:
            print(f"  [tokens acumulados] {agente.uso_total}\n")

    print(f"Conversa salva em {sessao.caminho}")


if __name__ == "__main__":
    main()
