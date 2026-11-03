"""Histórico da conversa em memória, salvo em sessions/<id>.json a cada turno."""

import json
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from agente.config import SESSIONS_DIR


@dataclass
class Sessao:
    id: str = field(default_factory=lambda: datetime.now().strftime("%Y%m%d-%H%M%S-") + uuid.uuid4().hex[:6])
    mensagens: list[dict] = field(default_factory=list)
    pasta: Path = SESSIONS_DIR

    @property
    def caminho(self) -> Path:
        return self.pasta / f"{self.id}.json"

    def salvar(self) -> None:
        self.pasta.mkdir(parents=True, exist_ok=True)
        temporario = self.caminho.with_suffix(".tmp")
        temporario.write_text(
            json.dumps({"id": self.id, "mensagens": self.mensagens}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        temporario.replace(self.caminho)  # troca atômica: não deixa JSON pela metade

    @classmethod
    def carregar(cls, id_: str, pasta: Path = SESSIONS_DIR) -> "Sessao":
        dados = json.loads((pasta / f"{id_}.json").read_text(encoding="utf-8"))
        return cls(id=dados["id"], mensagens=dados["mensagens"], pasta=pasta)
