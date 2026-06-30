"""Motor de feature engineering: roda todos os analistas sobre a janela
definida por LeagueRules e devolve os fatos candidatos.

Per-time: `run(data, rules)`. Nível confronto (mercados por convergência dos
DOIS times, DESIGN §6/#8c): `confronto(data_a, data_b, rules)`.
"""

from __future__ import annotations

from .. import config
from ..models import Fact, Match, Team, TeamTournamentData
from ..rules.base import LeagueRules
from . import anomalies, attack, betting, defense, markets, results, temporal

ANALYSTS = (attack, defense, temporal, results, anomalies, betting)


def run(data: TeamTournamentData, rules: LeagueRules) -> list[Fact]:
    matches = rules.window_matches(data)
    period = rules.period_label()
    facts: list[Fact] = []
    for analyst in ANALYSTS:
        facts.extend(analyst.analyze(data.team, matches, period))
    facts.extend(rules.extra_facts(data.team, matches, period))  # famílias da liga
    return facts


# --- nível confronto: mercados do JOGO por convergência -----------------------
def _rate(matches: list[Match], tid: int, pred) -> tuple[float, int]:
    """(% de jogos em que `pred(match, team_id)` vale, nº de jogos)."""
    n = len(matches)
    if n == 0:
        return 0.0, 0
    return sum(1 for m in matches if pred(m, tid)) / n * 100, n


def _over25(m: Match, tid: int) -> bool:
    return m.goals_for(tid) + m.goals_against(tid) >= 3


def _btts(m: Match, tid: int) -> bool:
    return m.goals_for(tid) > 0 and m.goals_against(tid) > 0


def _scored(m: Match, tid: int) -> bool:
    return m.goals_for(tid) > 0


def _conceded(m: Match, tid: int) -> bool:
    return m.goals_against(tid) > 0


def _conv_fact(text: str, value: str, sample: int, key: str, market: str, lead: float) -> Fact:
    """Fato de confronto que JÁ nasce com mercado anexado (markets.py o respeita)."""
    return Fact(
        text=text,
        value=value,
        sample=sample,
        category="confronto",
        kind="taxa",
        robustness="fragil",
        team="confronto",
        key=key,
        markets=[market],
        strength=markets.rate_strength(lead),
    )


def confronto(
    data_a: TeamTournamentData, data_b: TeamTournamentData, rules: LeagueRules
) -> list[Fact]:
    """Mercados do jogo que só acendem quando os DOIS times convergem.

    NUNCA vira probabilidade combinada — relata as duas taxas lado a lado. Cada
    lado precisa de amostra >= RATE e taxa >= CONVERGÊNCIA pra acender.
    """
    ma, mb = rules.window_matches(data_a), rules.window_matches(data_b)
    period = rules.period_label()
    ta, tb = data_a.team, data_b.team
    cv, smin = config.MARKET_CONVERGENCE_PCT, config.MIN_SAMPLE_MARKET_RATE
    out: list[Fact] = []

    def ok(pa: float, na: int, pb: float, nb: int) -> bool:
        return na >= smin and nb >= smin and pa >= cv and pb >= cv

    # Over 2,5 gols no jogo.
    oa, na = _rate(ma, ta.id, _over25)
    ob, nb = _rate(mb, tb.id, _over25)
    if ok(oa, na, ob, nb):
        out.append(
            _conv_fact(
                f"Over 2,5 gols apareceu em {oa:.0f}% dos jogos de {ta.name} e "
                f"{ob:.0f}% dos de {tb.name} {period}.",
                f"{oa:.0f}%/{ob:.0f}%",
                min(na, nb),
                "confronto:over25",
                "Mais de 2,5 gols no jogo",
                min(oa, ob),
            )
        )

    # Ambos marcam (BTTS).
    ba, na = _rate(ma, ta.id, _btts)
    bb, nb = _rate(mb, tb.id, _btts)
    if ok(ba, na, bb, nb):
        out.append(
            _conv_fact(
                f"Ambos marcaram em {ba:.0f}% dos jogos de {ta.name} e {bb:.0f}% "
                f"dos de {tb.name} {period}.",
                f"{ba:.0f}%/{bb:.0f}%",
                min(na, nb),
                "confronto:btts",
                "Ambos marcam",
                min(ba, bb),
            )
        )

    # "Time marca": ataque de um converge com a fragilidade defensiva do outro.
    for atk, dfn, key in ((ta, tb, "confronto:marca_a"), (tb, ta, "confronto:marca_b")):
        m_atk = ma if atk is ta else mb
        m_dfn = mb if dfn is tb else ma
        sc, ns = _rate(m_atk, atk.id, _scored)
        co, nc = _rate(m_dfn, dfn.id, _conceded)
        if ok(sc, ns, co, nc):
            out.append(
                _conv_fact(
                    f"{atk.name} marcou em {sc:.0f}% dos jogos {period}, e "
                    f"{dfn.name} sofreu gol em {co:.0f}% — convergência pro mercado.",
                    f"{sc:.0f}%/{co:.0f}%",
                    min(ns, nc),
                    key,
                    f"Para {atk.name} marcar",
                    min(sc, co),
                )
            )
    return out
