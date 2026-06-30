"""Helpers compartilhados pelos analistas (módulos de feature engineering).

Cada analista é uma função `analyze(team, matches, period) -> list[Fact]`.
'period' é o rótulo de janela vindo de LeagueRules (ex.: 'nesta Copa') e DEVE
aparecer no texto do fato — é a regra de honestidade (fato + amostra).
"""

from __future__ import annotations

from ..models import Match


def running_min_max_diff(match: Match, team_id: int) -> tuple[int, int]:
    """Menor e maior saldo do time ao longo do jogo (via eventos de gol).

    Usado para detectar viradas (esteve atrás = mínimo < 0). Best-effort: se os
    eventos estiverem incompletos, subestima.
    """
    goals = sorted(
        (e for e in match.events if e.is_goal), key=lambda e: e.total_minute
    )
    diff = lo = hi = 0
    for e in goals:
        scored_for = e.team_id != team_id if e.is_own_goal else e.team_id == team_id
        diff += 1 if scored_for else -1
        lo, hi = min(lo, diff), max(hi, diff)
    return lo, hi


def scored_first(match: Match, team_id: int) -> bool | None:
    """O time fez o 1º gol do jogo? None se não houve gols/eventos."""
    goals = sorted(
        (e for e in match.events if e.is_goal), key=lambda e: e.total_minute
    )
    if not goals:
        return None
    e = goals[0]
    return e.team_id != team_id if e.is_own_goal else e.team_id == team_id
