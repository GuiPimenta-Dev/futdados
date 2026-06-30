"""LLM #1 — editor de pauta. Seleciona os top-N fatos por interesse.

O LLM escolhe por ÍNDICE (nunca reescreve números). Saída estruturada validada
com Pydantic, via o backend configurado (assinatura CLI ou API).
"""

from __future__ import annotations

from pydantic import BaseModel

from .. import config
from ..models import Fact, RankedFact
from .complete import structured_complete
from .prompts import RANKER_SYSTEM


class Selection(BaseModel):
    index: int
    interest: float
    rationale: str


class RankerOutput(BaseModel):
    selections: list[Selection]


def _market_tag(f: Fact) -> str:
    if f.markets:
        return f" [MERCADO: {' / '.join(f.markets)} · força: {f.strength}]"
    return " [sem mercado]"


def _render_candidates(facts: list[Fact]) -> str:
    return "\n".join(
        f"[{i}] ({f.category}/{f.kind}, amostra={f.sample}, {f.robustness})"
        f"{_market_tag(f)} {f.text}"
        for i, f in enumerate(facts)
    )


def rank(matchup: str, facts: list[Fact], top_n: int = config.TOP_N_INSIGHTS) -> list[RankedFact]:
    if not facts:
        return []
    user = (
        f"Confronto: {matchup}\n\n"
        f"Fatos candidatos (todos verdadeiros):\n{_render_candidates(facts)}\n\n"
        f"Escolha os {top_n} mais interessantes para o vídeo. Devolva os índices "
        f"em 'selections', com 'interest' (0 a 1) e 'rationale' curto para cada."
    )
    out = structured_complete(
        RANKER_SYSTEM,
        user,
        RankerOutput,
        model_id=config.RANKER_MODEL,
        max_tokens=config.RANKER_MAX_TOKENS,
    )

    ranked: list[RankedFact] = []
    for sel in sorted(out.selections, key=lambda s: s.interest, reverse=True):
        if 0 <= sel.index < len(facts):
            ranked.append(
                RankedFact(fact=facts[sel.index], interest=sel.interest, rationale=sel.rationale)
            )
    return ranked[:top_n]
