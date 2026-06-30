"""Analista de aposta: as TAXAS que os mercados pedem, na faixa 60-90%.

Os analistas de curiosidade só disparam em extremos (100%/0%, "em todos"). Mas
os mercados mais apostados (over/under, ambos marcam, time marca) vivem também
na faixa intermediária. Este módulo computa essas taxas explicitamente, por time
e por jogo, para que `features/markets.py` tenha matéria-prima pra anexar mercado
sem depender de um extremo.

São FATOS DESCRITIVOS do passado (com amostra embutida) — o mercado é anexado
depois, e só se passar a porta de elegibilidade (DESIGN §6).
"""

from __future__ import annotations

from ..models import Fact, Match, Team

CATEGORY = "aposta"


def analyze(team: Team, matches: list[Match], period: str) -> list[Fact]:
    facts: list[Fact] = []
    n = len(matches)
    if n == 0:
        return facts
    tid, name = team.id, team.name

    # Over 2,5 gols no JOGO (gols totais = a favor + sofridos).
    over = sum(1 for m in matches if m.goals_for(tid) + m.goals_against(tid) >= 3)
    pct = over / n * 100
    facts.append(
        Fact(
            text=(
                f"Os jogos de {name} {period} tiveram mais de 2,5 gols em "
                f"{over} de {n} ({pct:.0f}%)."
            ),
            value=f"{pct:.0f}%",
            sample=n,
            category=CATEGORY,
            kind="taxa",
            robustness="fragil",
            team=name,
            key="aposta:over25",
        )
    )

    # Ambos marcam (BTTS): o time marcou E sofreu no mesmo jogo.
    btts = sum(1 for m in matches if m.goals_for(tid) > 0 and m.goals_against(tid) > 0)
    pctb = btts / n * 100
    facts.append(
        Fact(
            text=(
                f"Nos jogos de {name} {period}, ambos os times marcaram em "
                f"{btts} de {n} ({pctb:.0f}%)."
            ),
            value=f"{pctb:.0f}%",
            sample=n,
            category=CATEGORY,
            kind="taxa",
            robustness="fragil",
            team=name,
            key="aposta:btts",
        )
    )

    # Taxa de marcar (complementa o binário "marcou em todos": só quando NÃO é
    # 100% nem 0%, pra não duplicar o fato de anomalia/ataque).
    scored = sum(1 for m in matches if m.goals_for(tid) > 0)
    if 0 < scored < n:
        pcts = scored / n * 100
        facts.append(
            Fact(
                text=f"{name} marcou em {scored} de {n} jogos {period} ({pcts:.0f}%).",
                value=f"{pcts:.0f}%",
                sample=n,
                category=CATEGORY,
                kind="taxa",
                robustness="fragil",
                team=name,
                key="aposta:marca_taxa",
            )
        )

    # Taxa de sofrer gol (informa BTTS/over do lado defensivo).
    conceded = sum(1 for m in matches if m.goals_against(tid) > 0)
    pctc = conceded / n * 100
    facts.append(
        Fact(
            text=f"{name} sofreu gol em {conceded} de {n} jogos {period} ({pctc:.0f}%).",
            value=f"{pctc:.0f}%",
            sample=n,
            category=CATEGORY,
            kind="taxa",
            robustness="fragil",
            team=name,
            key="aposta:sofre_taxa",
        )
    )
    return facts
