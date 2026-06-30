"""Renderização do entregável em Markdown (roteiro + pauta).

Pivot nível B: cada fato-fonte mostra o MERCADO e a FORÇA do sinal, e o
disclaimer é GARANTIDO pelo código (não depende do LLM) — ver DESIGN §7.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from .models import Fact, RankedFact

if TYPE_CHECKING:
    from .llm.writer import ScriptOutput


def _markets_of(facts) -> list[str]:
    """Mercados distintos iluminados pelos fatos, preservando a ordem."""
    seen: list[str] = []
    for f in facts:
        for m in f.markets:
            if m not in seen:
                seen.append(m)
    return seen


def render_full(
    matchup: str, phase: str, ranked: list[RankedFact], script: "ScriptOutput"
) -> str:
    beats = "\n".join(f"{i}. {b}" for i, b in enumerate(script.beats, 1))
    tags = " ".join(f"#{h.lstrip('#')}" for h in script.hashtags)
    sources = "\n".join(
        f"- {r.fact.text} _(amostra: {r.fact.sample} jogos · "
        f"{('mercado: ' + ' / '.join(r.fact.markets) + ' · força: ' + r.fact.strength) if r.fact.markets else 'sem mercado'} · "
        f"interesse: {r.interest:.2f})_"
        for r in ranked
    )
    markets = _markets_of(r.fact for r in ranked)
    markets_block = (
        "\n".join(f"- {m}" for m in markets) if markets else "- (nenhum mercado acendeu nesta amostra)"
    )
    return f"""# {matchup} — {phase}

> Raio X do Jogo — números que explicam o jogo. Confira a pauta antes de gravar/postar.

## Roteiro (~1min)

**Gancho (0-3s):** {script.hook}

{beats}

**Fecho / CTA:** {script.cta}

## Mercados iluminados (pela estatística)

{markets_block}

## Publicação

- **Título:** {script.title}
- **Legenda:** {script.caption}
- **Hashtags:** {tags}

## Pauta — fatos-fonte (com números, amostra e mercado)

{sources}
"""


def render_candidates(matchup: str, phase: str, candidates: list[Fact]) -> str:
    lines = "\n".join(
        f"- `[{f.category}/{f.kind}]`"
        f"{(' `' + ' / '.join(f.markets) + '` (' + f.strength + ')') if f.markets else ''}"
        f" {f.text} _(amostra: {f.sample})_"
        for f in candidates
    )
    markets = _markets_of(candidates)
    markets_block = "\n".join(f"- {m}" for m in markets) if markets else "- (nenhum)"
    return f"""# {matchup} — {phase}

> Candidatos validados pelo motor determinístico (LLM não executado — sem ANTHROPIC_API_KEY).

## {len(candidates)} fatos candidatos

{lines}

## Mercados iluminados

{markets_block}
"""
