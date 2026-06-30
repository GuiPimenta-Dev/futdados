"""Pré-filtro de validade estatística + dedup (roda ANTES do LLM).

- Fatos de TAXA (%) precisam de amostra mínima; fatos binários/contagem/
  sequência "duros" passam mesmo com amostra pequena (são literalmente verdade).
- Dedup por (time, chave) para não mandar fatos redundantes ao ranqueador.
"""

from __future__ import annotations

from . import config
from .models import Fact


def validate(facts: list[Fact]) -> list[Fact]:
    kept: list[Fact] = []
    seen: set[tuple[str, str]] = set()
    for f in facts:
        if f.kind == "taxa" and f.sample < config.MIN_SAMPLE_FOR_RATE:
            continue
        dedup_key = (f.team, f.key)
        if dedup_key in seen:
            continue
        seen.add(dedup_key)
        kept.append(f)
    return kept
