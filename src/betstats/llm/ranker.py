"""LLM #1 — editor de pauta. Seleciona os top-N fatos por interesse.

O LLM escolhe por ÍNDICE (nunca reescreve números). Saída estruturada validada
com Pydantic, via o backend configurado (assinatura CLI ou API).
"""

from __future__ import annotations

from pydantic import BaseModel

from .. import config
from ..features import angles
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


def _spine_hint(facts: list[Fact], spine: Fact | None) -> str:
    """Aponta a ESPINHA (tese do jogo) pro ranker ancorar a seleção nela."""
    if spine is None:
        return ""
    idx = facts.index(spine)
    return (
        f"\nESPINHA do confronto (a tese mais forte) = fato [{idx}]: \"{spine.text}\". "
        f"INCLUA-O e ancore a seleção nele: os demais devem cobrir mercados DISTINTOS "
        f"que CONVERSEM com essa tese (não fatos soltos). Ele será o beat de abertura.\n"
    )


def _ensure_spine_first(
    ranked: list[RankedFact], facts: list[Fact], spine: Fact | None, top_n: int
) -> list[RankedFact]:
    """Garante (determinístico) que a espinha entra e abre — coesão não fica na sorte do LLM."""
    if spine is None:
        return ranked[:top_n]
    rest = [r for r in ranked if r.fact is not spine]
    head = next((r for r in ranked if r.fact is spine), None) or RankedFact(
        fact=spine, interest=1.0, rationale="Espinha do confronto (contraste/mercado mais forte)."
    )
    return [head, *rest][:top_n]


def rank(matchup: str, facts: list[Fact], top_n: int | None = None) -> list[RankedFact]:
    if not facts:
        return []
    spine = angles.pick_spine(facts)
    if top_n is None:
        # Duração elástica: espinha de contraste destrava o formato profundo (mais
        # corroboradores p/ o roteirista desdobrar a tese). Ver config / DESIGN §7.
        top_n = config.TOP_N_DEEP if angles.is_deep_spine(spine) else config.TOP_N_INSIGHTS
    user = (
        f"Confronto: {matchup}\n\n"
        f"Fatos candidatos (todos verdadeiros):\n{_render_candidates(facts)}\n"
        f"{_spine_hint(facts, spine)}\n"
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
    return _ensure_spine_first(ranked, facts, spine, top_n)
