"""Analista ofensivo: gols, finalização, conversão, goleadas."""

from __future__ import annotations

from ..models import Fact, Match, Team

CATEGORY = "ataque"


def analyze(team: Team, matches: list[Match], period: str) -> list[Fact]:
    facts: list[Fact] = []
    n = len(matches)
    if n == 0:
        return facts
    tid, name = team.id, team.name

    goals = sum(m.goals_for(tid) for m in matches)
    facts.append(
        Fact(
            text=f"{name} marcou {goals} gols {period} — média de {goals / n:.1f} por jogo.",
            value=f"{goals} gols",
            sample=n,
            category=CATEGORY,
            kind="contagem",
            robustness="dura",
            team=name,
            key="ataque:gols_total",
        )
    )

    scored = sum(1 for m in matches if m.goals_for(tid) > 0)
    if scored == n:
        facts.append(
            Fact(
                text=f"{name} marcou em todos os {n} jogos {period}.",
                value=f"{n}/{n}",
                sample=n,
                category=CATEGORY,
                kind="binario",
                robustness="dura",
                team=name,
                key="ataque:marcou_todos",
            )
        )

    # Sequência atual marcando (do jogo mais recente pra trás). Só quando é uma
    # corrida parcial — se marcou em TODOS, o fato acima já cobre.
    streak = 0
    for m in reversed(matches):
        if m.goals_for(tid) > 0:
            streak += 1
        else:
            break
    if 3 <= streak < n:
        facts.append(
            Fact(
                text=f"{name} marcou nos últimos {streak} jogos seguidos {period}.",
                value=f"{streak} jogos",
                sample=streak,
                category=CATEGORY,
                kind="sequencia",
                robustness="dura",
                team=name,
                key="ataque:sequencia_marcando",
            )
        )

    sog = [
        m.stats[tid].shots_on_goal
        for m in matches
        if tid in m.stats and m.stats[tid].shots_on_goal is not None
    ]
    if sog:
        total_sog = sum(sog)
        facts.append(
            Fact(
                text=f"{name} acertou {total_sog / len(sog):.1f} chutes no gol por jogo {period}.",
                value=f"{total_sog / len(sog):.1f}/jogo",
                sample=len(sog),
                category=CATEGORY,
                kind="taxa",
                robustness="fragil",
                team=name,
                key="ataque:chutes_no_gol",
            )
        )
        if total_sog > 0:
            conv = goals / total_sog * 100
            facts.append(
                Fact(
                    text=(
                        f"{name} converteu {conv:.0f}% dos chutes no gol "
                        f"({goals} gols em {total_sog} chutes no alvo) {period}."
                    ),
                    value=f"{conv:.0f}%",
                    sample=len(sog),
                    category=CATEGORY,
                    kind="taxa",
                    robustness="fragil",
                    team=name,
                    key="ataque:conversao",
                )
            )

    best = max(matches, key=lambda m: m.goals_for(tid) - m.goals_against(tid))
    diff = best.goals_for(tid) - best.goals_against(tid)
    if diff >= 2:
        facts.append(
            Fact(
                text=(
                    f"Maior goleada de {name} {period}: {best.goals_for(tid)} a "
                    f"{best.goals_against(tid)} sobre {best.opponent(tid).name}."
                ),
                value=f"{best.goals_for(tid)}-{best.goals_against(tid)}",
                sample=1,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="ataque:maior_goleada",
            )
        )
    return facts
