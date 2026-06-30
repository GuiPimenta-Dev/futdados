"""LLM #2 — roteirista. Transforma os fatos selecionados num roteiro de ~90s.

Aplica a regra de honestidade (fato + amostra, sem profecia). Saída estruturada
validada com Pydantic, via o backend configurado (assinatura CLI ou API).
"""

from __future__ import annotations

from pydantic import BaseModel

from .. import config
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


def write_script(matchup: str, phase: str, ranked: list[RankedFact]) -> ScriptOutput:
    user = (
        f"Confronto: {matchup}\n"
        f"Fase: {phase}\n\n"
        f"Fatos selecionados (use SOMENTE estes números):\n{_render_facts(ranked)}\n\n"
        f"Escreva o roteiro de ~1min30 seguindo a estrutura e a regra de honestidade."
    )
    return structured_complete(
        WRITER_SYSTEM,
        user,
        ScriptOutput,
        model_id=config.WRITER_MODEL,
        max_tokens=config.WRITER_MAX_TOKENS,
    )
