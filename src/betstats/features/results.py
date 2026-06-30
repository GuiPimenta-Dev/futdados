"""Analista de resultado/forma: campanha, jogos apertados, viradas, pênaltis."""

from __future__ import annotations

from ..models import Fact, Match, Team
from .base import running_min_max_diff, scored_first

CATEGORY = "resultado"


def analyze(team: Team, matches: list[Match], period: str) -> list[Fact]:
    facts: list[Fact] = []
    n = len(matches)
    if n == 0:
        return facts
    tid, name = team.id, team.name

    v = sum(1 for m in matches if m.result_for(tid) == "V")
    e = sum(1 for m in matches if m.result_for(tid) == "E")
    d = sum(1 for m in matches if m.result_for(tid) == "D")
    saldo = sum(m.goals_for(tid) - m.goals_against(tid) for m in matches)
    facts.append(
        Fact(
            text=(
                f"{name} {period}: {v} vitórias, {e} empates e {d} derrotas; "
                f"saldo de gols {saldo:+d}."
            ),
            value=f"{v}V {e}E {d}D",
            sample=n,
            category=CATEGORY,
            kind="contagem",
            robustness="dura",
            team=name,
            key="resultado:campanha",
        )
    )

    one_goal = sum(1 for m in matches if abs(m.goals_for(tid) - m.goals_against(tid)) == 1)
    if one_goal >= 2:
        facts.append(
            Fact(
                text=f"{one_goal} dos {n} jogos de {name} {period} foram decididos por 1 gol.",
                value=f"{one_goal}/{n} por 1 gol",
                sample=n,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="resultado:um_gol",
            )
        )

    # Viradas / buscar resultado (esteve atrás e não perdeu) — via eventos.
    comebacks = 0
    for m in matches:
        lo, _ = running_min_max_diff(m, tid)
        if lo < 0 and m.result_for(tid) in ("V", "E"):
            comebacks += 1
    if comebacks >= 2:
        facts.append(
            Fact(
                text=f"{name} veio de atrás para pontuar em {comebacks} jogos {period}.",
                value=f"{comebacks} viradas/buscas",
                sample=n,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="resultado:viradas",
            )
        )

    # Resultado quando faz o primeiro gol.
    first_goal_games = [(m, scored_first(m, tid)) for m in matches]
    scored_first_n = sum(1 for _, sf in first_goal_games if sf)
    won_after_first = sum(
        1 for m, sf in first_goal_games if sf and m.result_for(tid) == "V"
    )
    if scored_first_n >= 2:
        facts.append(
            Fact(
                text=(
                    f"{name} abriu o placar em {scored_first_n} jogos {period} e "
                    f"venceu {won_after_first} deles."
                ),
                value=f"{won_after_first}/{scored_first_n}",
                sample=scored_first_n,
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="resultado:abriu_placar",
            )
        )

    # Disputas de pênalti (mata-mata).
    shootouts = [m for m in matches if m.decided_by_penalties]
    if shootouts:
        won = sum(1 for m in shootouts if m.won_shootout(tid))
        facts.append(
            Fact(
                text=(
                    f"{name} disputou {len(shootouts)} decisão(ões) por pênaltis {period} "
                    f"e venceu {won}."
                ),
                value=f"{won}/{len(shootouts)} nos pênaltis",
                sample=len(shootouts),
                category=CATEGORY,
                kind="contagem",
                robustness="dura",
                team=name,
                key="resultado:penaltis",
            )
        )
    return facts
