"""Analista defensivo: gols sofridos, clean sheets, sequência sem sofrer."""

from __future__ import annotations

from ..models import Fact, Match, Team

CATEGORY = "defesa"


def analyze(team: Team, matches: list[Match], period: str) -> list[Fact]:
    facts: list[Fact] = []
    n = len(matches)
    if n == 0:
        return facts
    tid, name = team.id, team.name

    conceded = sum(m.goals_against(tid) for m in matches)
    facts.append(
        Fact(
            text=f"{name} sofreu {conceded} gols {period} — média de {conceded / n:.1f} por jogo.",
            value=f"{conceded} sofridos",
            sample=n,
            category=CATEGORY,
            kind="contagem",
            robustness="dura",
            team=name,
            key="defesa:gols_sofridos",
        )
    )

    clean = sum(1 for m in matches if m.clean_sheet(tid))
    if clean == n:
        facts.append(
            Fact(
                text=f"{name} não sofreu gol em nenhum dos {n} jogos {period}.",
                value=f"{n}/{n} sem sofrer",
                sample=n,
                category=CATEGORY,
                kind="binario",
                robustness="dura",
                team=name,
                key="defesa:clean_sheet_todos",
            )
        )
    elif clean > 0:
        facts.append(
            Fact(
                text=f"{name} passou em branco (sem sofrer gol) em {clean} dos {n} jogos {period}.",
                value=f"{clean}/{n}",
                sample=n,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="defesa:clean_sheets",
            )
        )

    # Maior sequência atual sem sofrer gol (em jogos), a partir do mais recente.
    streak = 0
    for m in reversed(matches):
        if m.clean_sheet(tid):
            streak += 1
        else:
            break
    if streak >= 2:
        facts.append(
            Fact(
                text=f"{name} não sofre gols há {streak} jogos seguidos {period}.",
                value=f"{streak} jogos",
                sample=streak,
                category=CATEGORY,
                kind="sequencia",
                robustness="dura",
                team=name,
                key="defesa:sequencia_sem_sofrer",
            )
        )
    return facts
