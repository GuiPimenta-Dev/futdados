"""Mapeamento determinístico fato → mercado de aposta (DESIGN §6, Decisão #8b).

O LLM NUNCA inventa o vínculo fato→mercado: ele nasce aqui, no código, e vira um
dado rastreável (`Fact.markets` + `Fact.strength`). `attach_markets` aplica a
PORTA DE ELEGIBILIDADE (#8d) — é o que impede um "4 de 4" frágil de virar dica.

- Fato "duro" (binário/sequência/evento forte): mercado com amostra >= HARD.
- Fato de TAXA (%): mercado só com amostra >= RATE, denominador explícito e um
  LADO claro (lean >= convergência); abaixo disso é cara-ou-coroa, sem sinal.
"""

from __future__ import annotations

import re

from .. import config
from ..models import Fact

# Fatos "duros": o mercado vem da própria existência do padrão (não de uma %).
_HARD_MARKETS: dict[str, str] = {
    "ataque:marcou_todos": "Para {team} marcar",
    "ataque:sequencia_marcando": "Para {team} marcar",
    "defesa:clean_sheet_todos": "{team} não sofre gol (clean sheet)",
    "defesa:sequencia_sem_sofrer": "{team} não sofre gol (clean sheet)",
    "anomalia:venceu_todos": "Vitória de {team} (1X2)",
    "anomalia:invicto": "{team} não perde (dupla chance)",
    "temporal:gols_finais": "Gol depois dos 75'",
    "resultado:abriu_placar": "{team} marca o primeiro gol",
}

# Fatos de TAXA: o mercado depende do LADO pra onde a % aponta (high/low).
_RATE_MARKETS: dict[str, dict[str, str]] = {
    "aposta:over25": {"high": "Mais de 2,5 gols no jogo", "low": "Menos de 2,5 gols no jogo"},
    "aposta:btts": {"high": "Ambos marcam", "low": "Ambos não marcam"},
    "aposta:marca_taxa": {"high": "Para {team} marcar", "low": "{team} não marca"},
    "aposta:sofre_taxa": {
        "high": "{team} sofre gol",
        "low": "{team} não sofre gol (clean sheet)",
    },
    "temporal:gols_por_tempo": {"high": "Gols no 2º tempo", "low": "Gols no 1º tempo"},
}

_PCT_RE = re.compile(r"(\d+(?:[.,]\d+)?)\s*%")


def parse_pct(value: str) -> float | None:
    """Extrai a primeira porcentagem de um `value` (ex.: '80% no 2ºT' -> 80.0)."""
    m = _PCT_RE.search(value or "")
    return float(m.group(1).replace(",", ".")) if m else None


def rate_strength(pct: float) -> str:
    """Força de um sinal de taxa pela distância do 50/50."""
    dist = max(pct, 100 - pct)
    return "forte" if dist >= config.MARKET_STRONG_PCT else "moderado"


def attach_markets(facts: list[Fact]) -> list[Fact]:
    """Anexa `markets` + `strength` a cada fato elegível (mutação in-place).

    Pula fatos que já trazem mercado (ex.: convergência de confronto, que se
    autodetermina). Devolve a mesma lista para encadear.
    """
    for f in facts:
        if f.markets:  # já mapeado na origem (confronto)
            continue
        if f.key in _HARD_MARKETS:
            if f.sample < config.MIN_SAMPLE_MARKET_HARD:
                continue
            f.markets = [_HARD_MARKETS[f.key].format(team=f.team)]
            f.strength = "forte" if f.sample >= 4 else "moderado"
        elif f.key in _RATE_MARKETS:
            pct = parse_pct(f.value)
            if pct is None or f.sample < config.MIN_SAMPLE_MARKET_RATE:
                continue
            if max(pct, 100 - pct) < config.MARKET_CONVERGENCE_PCT:
                continue  # cara-ou-coroa: sem lado claro, sem mercado
            side = "high" if pct >= 50 else "low"
            market = _RATE_MARKETS[f.key].get(side)
            if not market:
                continue
            f.markets = [market.format(team=f.team)]
            f.strength = rate_strength(pct)
    return facts
