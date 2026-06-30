"""Motor de feature engineering: roda todos os analistas sobre a janela
definida por LeagueRules e devolve os fatos candidatos.

Per-time: `run(data, rules)`. Nível confronto (mercados por convergência dos
DOIS times, DESIGN §6/#8c): `confronto(data_a, data_b, rules)`.
"""

from __future__ import annotations

from .. import config
from ..data import elo
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


def _conv_fact(text: str, value: str, sample: int, key: str, market: str, strength: str) -> Fact:
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
        strength=strength,
    )


# --- ajuste por força de adversário (Elo, uso interno — DESIGN §6-bis) --------
def _weak_fraction(matches: list[Match], tid: int) -> float:
    """Fração da AMOSTRA (todos os jogos) contra adversário 'fraco' (Elo).

    Desconhecido conta como NEUTRO no denominador — nunca como fraco —, então uma
    amostra majoritariamente desconhecida (ou Elo indisponível) não dispara o gate.
    """
    if not matches:
        return 0.0
    weak = sum(1 for m in matches if elo.tier(m.opponent(tid).name) == elo.FRACO)
    return weak / len(matches)


def _gate(strength: str, weak_frac: float) -> str | None:
    """Trava do passo §6-bis: ≥⅔ da amostra contra fraco → cai um nível.
    forte→moderado; moderado→não acende (None)."""
    if weak_frac >= config.CONTRAST_WEAK_FRAC:
        return "moderado" if strength == "forte" else None
    return strength


def _avg_shots_for(matches: list[Match], tid: int) -> tuple[float | None, int]:
    vals = [
        m.stats[tid].shots_total
        for m in matches
        if tid in m.stats and m.stats[tid].shots_total is not None
    ]
    return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)


def _avg_shots_against(matches: list[Match], tid: int) -> tuple[float | None, int]:
    """Finalizações que o time CEDE (chutes do adversário nos jogos dele)."""
    vals: list[int] = []
    for m in matches:
        opp = m.opponent(tid).id
        s = m.stats.get(opp)
        if s is not None and s.shots_total is not None:
            vals.append(s.shots_total)
    return (sum(vals) / len(vals), len(vals)) if vals else (None, 0)


def _rate_2h_for(matches: list[Match], tid: int) -> tuple[float, int]:
    """% dos gols FEITOS que saíram no 2º tempo (entre jogos com placar de 1ºT)."""
    sh = tot = n = 0
    for m in matches:
        g = m.goals_for(tid)
        s2 = m.second_half_goals_for(tid)
        if s2 is None or g == 0:
            continue
        sh += s2
        tot += g
        n += 1
    return (sh / tot * 100 if tot else 0.0), n


def _rate_2h_against(matches: list[Match], tid: int) -> tuple[float, int]:
    """% dos gols SOFRIDOS que saíram no 2º tempo."""
    sh = tot = n = 0
    for m in matches:
        g = m.goals_against(tid)
        s2 = m.second_half_goals_against(tid)
        if s2 is None or g == 0:
            continue
        sh += s2
        tot += g
        n += 1
    return (sh / tot * 100 if tot else 0.0), n


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
    # Fração da amostra de cada time contra adversário fraco (gate de zebra).
    wf_a, wf_b = _weak_fraction(ma, ta.id), _weak_fraction(mb, tb.id)
    out: list[Fact] = []

    def ok(pa: float, na: int, pb: float, nb: int) -> bool:
        return na >= smin and nb >= smin and pa >= cv and pb >= cv

    # Over 2,5 gols no jogo. Gate de jogo: o pior dos dois lados (max fração fraca).
    oa, na = _rate(ma, ta.id, _over25)
    ob, nb = _rate(mb, tb.id, _over25)
    if ok(oa, na, ob, nb):
        s = _gate(markets.rate_strength(min(oa, ob)), max(wf_a, wf_b))
        if s:
            out.append(
                _conv_fact(
                    f"Over 2,5 gols apareceu em {oa:.0f}% dos jogos de {ta.name} e "
                    f"{ob:.0f}% dos de {tb.name} {period}.",
                    f"{oa:.0f}%/{ob:.0f}%",
                    min(na, nb),
                    "confronto:over25",
                    "Mais de 2,5 gols no jogo",
                    s,
                )
            )

    # Ambos marcam (BTTS).
    ba, na = _rate(ma, ta.id, _btts)
    bb, nb = _rate(mb, tb.id, _btts)
    if ok(ba, na, bb, nb):
        s = _gate(markets.rate_strength(min(ba, bb)), max(wf_a, wf_b))
        if s:
            out.append(
                _conv_fact(
                    f"Ambos marcaram em {ba:.0f}% dos jogos de {ta.name} e {bb:.0f}% "
                    f"dos de {tb.name} {period}.",
                    f"{ba:.0f}%/{bb:.0f}%",
                    min(na, nb),
                    "confronto:btts",
                    "Ambos marcam",
                    s,
                )
            )

    # "Time marca": ataque de um converge com a fragilidade defensiva do outro.
    # Gate pela fração fraca do ATACANTE (é o ataque que pode estar inflado).
    for atk, dfn, key, wf in (
        (ta, tb, "confronto:marca_a", wf_a),
        (tb, ta, "confronto:marca_b", wf_b),
    ):
        m_atk = ma if atk is ta else mb
        m_dfn = mb if dfn is tb else ma
        sc, ns = _rate(m_atk, atk.id, _scored)
        co, nc = _rate(m_dfn, dfn.id, _conceded)
        if ok(sc, ns, co, nc):
            s = _gate(markets.rate_strength(min(sc, co)), wf)
            if s:
                out.append(
                    _conv_fact(
                        f"{atk.name} marcou em {sc:.0f}% dos jogos {period}, e "
                        f"{dfn.name} sofreu gol em {co:.0f}% — convergência pro mercado.",
                        f"{sc:.0f}%/{co:.0f}%",
                        min(ns, nc),
                        key,
                        f"Para {atk.name} marcar",
                        s,
                    )
                )

    # === Contraste de PROCESSO (§6-bis): assimetria força×fraqueza ============
    out.extend(_contrast_finalizacao(ma, mb, ta, tb, period, wf_a, wf_b))
    out.extend(_contrast_ritmo(ma, mb, ta, tb, period, wf_a, wf_b))
    return out


def _contrast_finalizacao(
    ma: list[Match], mb: list[Match], ta: Team, tb: Team, period: str,
    wf_a: float, wf_b: float,
) -> list[Fact]:
    """Volume de finalização de um × finalizações cedidas pelo outro → over/marca.

    Acende só na ASSIMETRIA: o ataque de A cria muito E a defesa de B cede muito.
    Mais estável que taxa de gol em 3 jogos — finalização não regride tanto."""
    smin = config.CONTRAST_MIN_SAMPLE
    hi, strong = config.CONTRAST_SHOTS_HIGH, config.CONTRAST_SHOTS_STRONG
    out: list[Fact] = []
    for atk, dfn, key, wf in (
        (ta, tb, "contraste:finalizacao_a", wf_a),
        (tb, ta, "contraste:finalizacao_b", wf_b),
    ):
        m_atk = ma if atk is ta else mb
        m_dfn = mb if dfn is tb else ma
        af, naf = _avg_shots_for(m_atk, atk.id)
        dc, ndc = _avg_shots_against(m_dfn, dfn.id)
        if af is None or dc is None or naf < smin or ndc < smin:
            continue
        if af < hi or dc < hi:  # precisa de volume dos DOIS lados (assimetria real)
            continue
        s = _gate("forte" if min(af, dc) >= strong else "moderado", wf)
        if not s:
            continue
        out.append(
            _conv_fact(
                f"{atk.name} finaliza {af:.0f} vezes por jogo {period}; {dfn.name} "
                f"cede {dc:.0f} finalizações por jogo — a pressão converge.",
                f"{af:.0f}/{dc:.0f} fin.",
                min(naf, ndc),
                key,
                f"Para {atk.name} marcar",
                s,
            )
        )
    return out


def _contrast_ritmo(
    ma: list[Match], mb: list[Match], ta: Team, tb: Team, period: str,
    wf_a: float, wf_b: float,
) -> list[Fact]:
    """Quem marca no 2ºT × quem sofre no 2ºT → mercado 'gol no 2º tempo'."""
    smin = config.CONTRAST_MIN_SAMPLE
    hi = config.CONTRAST_2H_HIGH
    out: list[Fact] = []
    for atk, dfn, key, wf in (
        (ta, tb, "contraste:ritmo_a", wf_a),
        (tb, ta, "contraste:ritmo_b", wf_b),
    ):
        m_atk = ma if atk is ta else mb
        m_dfn = mb if dfn is tb else ma
        sf, nf = _rate_2h_for(m_atk, atk.id)
        sc, nc = _rate_2h_against(m_dfn, dfn.id)
        if nf < smin or nc < smin or sf < hi or sc < hi:
            continue
        s = _gate("forte" if min(sf, sc) >= config.MARKET_STRONG_PCT else "moderado", wf)
        if not s:
            continue
        out.append(
            _conv_fact(
                f"{atk.name} faz {sf:.0f}% dos gols no 2º tempo {period}, e {dfn.name} "
                f"sofre {sc:.0f}% no 2º tempo — o jogo tende a esquentar no fim.",
                f"{sf:.0f}%/{sc:.0f}% 2ºT",
                min(nf, nc),
                key,
                "Gol no 2º tempo",
                s,
            )
        )
    return out
