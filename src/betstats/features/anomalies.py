"""Analista de anomalias: padrões extremos (100%/0%), sequências perfeitas,
e curiosidades contra-intuitivas (vencer com menos posse).
"""

from __future__ import annotations

from ..models import Fact, Match, Team

CATEGORY = "anomalia"


def analyze(team: Team, matches: list[Match], period: str) -> list[Fact]:
    facts: list[Fact] = []
    n = len(matches)
    if n < 2:
        return facts
    tid, name = team.id, team.name

    results = [m.result_for(tid) for m in matches]
    if all(r == "V" for r in results):
        facts.append(
            Fact(
                text=f"{name} venceu TODOS os {n} jogos {period}.",
                value=f"{n}/{n} vitórias",
                sample=n,
                category=CATEGORY,
                kind="binario",
                robustness="dura",
                team=name,
                key="anomalia:venceu_todos",
            )
        )
    elif "D" not in results:
        facts.append(
            Fact(
                text=f"{name} está invicto {period} ({n} jogos sem perder).",
                value=f"{n} sem perder",
                sample=n,
                category=CATEGORY,
                kind="binario",
                robustness="dura",
                team=name,
                key="anomalia:invicto",
            )
        )

    if all(abs(m.goals_for(tid) - m.goals_against(tid)) == 1 for m in matches):
        facts.append(
            Fact(
                text=f"TODOS os {n} jogos de {name} {period} terminaram com diferença de 1 gol.",
                value=f"{n}/{n} por 1 gol",
                sample=n,
                category=CATEGORY,
                kind="binario",
                robustness="dura",
                team=name,
                key="anomalia:tudo_um_gol",
            )
        )

    # Venceu tendo menos posse de bola (curiosidade contra-intuitiva).
    upsets = 0
    poss_games = 0
    for m in matches:
        ms = m.stats.get(tid)
        opp = m.stats.get(m.opponent(tid).id)
        if not ms or not opp or ms.possession_pct is None or opp.possession_pct is None:
            continue
        poss_games += 1
        if m.result_for(tid) == "V" and ms.possession_pct < opp.possession_pct:
            upsets += 1
    if poss_games and upsets >= 2:
        facts.append(
            Fact(
                text=f"{name} venceu {upsets} jogos mesmo com menos posse de bola {period}.",
                value=f"{upsets} com menos posse",
                sample=poss_games,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="anomalia:vence_com_menos_posse",
            )
        )

    reds = sum(
        m.stats[tid].red_cards
        for m in matches
        if tid in m.stats and m.stats[tid].red_cards
    )
    if reds >= 2:
        facts.append(
            Fact(
                text=f"{name} levou {reds} cartões vermelhos {period}.",
                value=f"{reds} vermelhos",
                sample=n,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="anomalia:vermelhos",
            )
        )
    return facts
