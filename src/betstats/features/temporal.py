"""Analista temporal: gols por tempo, minuto do 1º gol, gols tardios.

Splits 1º/2º tempo vêm do PLACAR (HT/FT) — à prova de gol contra. Minuto do
gol vem dos eventos.
"""

from __future__ import annotations

from ..models import Fact, Match, Team

CATEGORY = "temporal"


def analyze(team: Team, matches: list[Match], period: str) -> list[Fact]:
    facts: list[Fact] = []
    n = len(matches)
    if n == 0:
        return facts
    tid, name = team.id, team.name

    # Gols por tempo (a favor), via placar HT/FT.
    with_ht = [m for m in matches if m.ht_goals_for(tid) is not None]
    if with_ht:
        first = sum(m.ht_goals_for(tid) for m in with_ht)
        second = sum(m.second_half_goals_for(tid) for m in with_ht)
        total = first + second
        if total > 0:
            pct2 = second / total * 100
            facts.append(
                Fact(
                    text=(
                        f"{name} fez {pct2:.0f}% dos gols no 2º tempo {period} "
                        f"({second} de {total})."
                    ),
                    value=f"{pct2:.0f}% no 2ºT",
                    sample=len(with_ht),
                    category=CATEGORY,
                    kind="taxa",
                    robustness="fragil",
                    team=name,
                    key="temporal:gols_por_tempo",
                )
            )

    # Gols sofridos por tempo.
    with_ht_a = [m for m in matches if m.ht_goals_against(tid) is not None]
    if with_ht_a:
        first_a = sum(m.ht_goals_against(tid) for m in with_ht_a)
        second_a = sum(m.second_half_goals_against(tid) for m in with_ht_a)
        total_a = first_a + second_a
        if total_a > 0:
            pct2a = second_a / total_a * 100
            facts.append(
                Fact(
                    text=(
                        f"{name} sofreu {pct2a:.0f}% dos gols no 2º tempo {period} "
                        f"({second_a} de {total_a})."
                    ),
                    value=f"{pct2a:.0f}% sofridos 2ºT",
                    sample=len(with_ht_a),
                    category=CATEGORY,
                    kind="taxa",
                    robustness="fragil",
                    team=name,
                    key="temporal:sofridos_por_tempo",
                )
            )

    # Minuto médio do primeiro gol (nos jogos em que marcou).
    first_minutes = [
        m.goal_minutes_for(tid)[0] for m in matches if m.goal_minutes_for(tid)
    ]
    if len(first_minutes) >= 2:
        avg = sum(first_minutes) / len(first_minutes)
        facts.append(
            Fact(
                text=(
                    f"Quando marca, {name} abre o placar em média aos {avg:.0f} minutos "
                    f"{period} (em {len(first_minutes)} jogos)."
                ),
                value=f"min {avg:.0f}",
                sample=len(first_minutes),
                category=CATEGORY,
                kind="taxa",
                robustness="fragil",
                team=name,
                key="temporal:minuto_primeiro_gol",
            )
        )

    # Gols nos minutos finais (75'+).
    late = sum(1 for m in matches for mn in m.goal_minutes_for(tid) if mn >= 75)
    if late >= 2:
        facts.append(
            Fact(
                text=f"{name} marcou {late} gols a partir dos 75 minutos {period}.",
                value=f"{late} gols 75'+",
                sample=n,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="temporal:gols_finais",
            )
        )
    return facts
