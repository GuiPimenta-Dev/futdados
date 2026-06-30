"""LLM #2 — roteirista. Transforma os fatos selecionados num roteiro de ~90s.

Aplica a regra de honestidade (fato + amostra, sem profecia). Saída estruturada
validada com Pydantic, via o backend configurado (assinatura CLI ou API).
"""

from __future__ import annotations

from pydantic import BaseModel

from .. import config
from ..features.angles import is_deep_spine
from ..models import RankedFact
from .complete import structured_complete
from .prompts import WRITER_SYSTEM


class ScriptOutput(BaseModel):
    hook: str
    beats: list[str]
    # Índice (0-based) do fato-fonte de CADA beat, na lista de fatos fornecida.
    # Paralelo a `beats` (mesmo tamanho); alimenta o card de número do vídeo.
    beat_facts: list[int] = []
    cta: str
    title: str
    # Frase-soco curtíssima (2-4 palavras) pra THUMBNAIL — alta tensão, gera
    # curiosidade, SEM clickbait barato. Ex.: "JOGO DE GOL?", "DEFESA FURADA".
    thumb_hook: str = ""
    caption: str
    hashtags: list[str]


def _render_facts(ranked: list[RankedFact]) -> str:
    lines = []
    for i, r in enumerate(ranked):
        f = r.fact
        market = (
            f"; mercado: {' / '.join(f.markets)} (força: {f.strength})"
            if f.markets
            else "; sem mercado"
        )
        lines.append(
            f"[{i}] {f.text} (valor: {f.value}; amostra: {f.sample} jogos{market})"
        )
    return "\n".join(lines)


def _format_directive(ranked: list[RankedFact]) -> str:
    """Escolhe o FORMATO (enxuto/profundo) pelo tipo da espinha — ranked[0], que
    `_ensure_spine_first` garante ser a tese. Determinístico (princípio #5): a
    duração não fica na sorte do LLM. Ver config / DESIGN §7."""
    deep = bool(ranked) and is_deep_spine(ranked[0].fact)
    lo, hi = config.WRITER_WORDS_DEEP if deep else config.WRITER_WORDS_LEAN
    if deep:
        return (
            f"FORMATO: PROFUNDO ({lo}-{hi} palavras, ~70-85s). A espinha [0] é um "
            "CONTRASTE DE PROCESSO — DESDOBRE-A em 2 beats (um por lado: quem ataca, "
            "quem cede), cada um com SEU número, antes dos corroboradores. Use só os "
            "números que JÁ estão no texto do fato-espinha; nunca invente um terceiro."
        )
    return (
        f"FORMATO: ENXUTO ({lo}-{hi} palavras, ~55s). A espinha não traz mecanismo a "
        "desdobrar — abra por ela em UM beat e siga com os corroboradores. Não estique."
    )


def write_script(matchup: str, phase: str, ranked: list[RankedFact]) -> ScriptOutput:
    user = (
        f"Confronto: {matchup}\n"
        f"Fase: {phase}\n\n"
        f"{_format_directive(ranked)}\n\n"
        f"Fatos selecionados (use SOMENTE estes números):\n{_render_facts(ranked)}\n\n"
        f"Escreva o roteiro seguindo a estrutura do formato indicado e a regra de honestidade."
    )
    return structured_complete(
        WRITER_SYSTEM,
        user,
        ScriptOutput,
        model_id=config.WRITER_MODEL,
        max_tokens=config.WRITER_MAX_TOKENS,
    )
