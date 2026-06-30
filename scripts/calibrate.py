#!/usr/bin/env python3
"""Mini-backtest de calibração (DESIGN §6-bis, passo 4) — roda UMA vez, descartável.

Objetivo: parar de chutar os limiares de contraste. Faz replay dos jogos JÁ
disputados (do `.cache`), computando o sinal de cada confronto usando SÓ os jogos
ANTERIORES a cada partida (zero lookahead), e mede **acerto-de-mercado por faixa de
força** — não "acertou o vencedor". Saída: uma tabela mercado×força com taxa de
acerto e amostra, separando a família de CONTRASTE do resto.

Uso:  PYTHONPATH=src python scripts/calibrate.py
Ajuste os limiares (config.CONTRAST_*) via env e rode de novo pra comparar.

Limite honesto: a Copa tem poucos jogos com histórico suficiente; a amostra do
backtest é pequena. Linhas com n baixo são sinalizadas — leia como direção, não
como verdade estatística. No Brasileirão (amostra funda) isto fica robusto.
"""

from __future__ import annotations

import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from betstats.config import WORLD_CUP_2026 as WC  # noqa: E402
from betstats.data.espn import ESPNProvider  # noqa: E402
from betstats.features import engine, markets  # noqa: E402
from betstats.models import Match, TeamTournamentData  # noqa: E402
from betstats.rules.world_cup import WorldCupRules  # noqa: E402

RULES = WorldCupRules()
MIN_PRIOR = 3  # jogos prévios mínimos por time pra um confronto entrar no backtest


# --- avaliação de mercado: o mercado "bateu" no jogo M? (None = não dá pra avaliar)
def _half2_total(m: Match) -> int | None:
    if m.ht_home is None or m.ht_away is None:
        return None
    return (m.home_goals - m.ht_home) + (m.away_goals - m.ht_away)


def evaluate(market: str, m: Match, a_id: int, a_name: str, b_id: int, b_name: str) -> bool | None:
    total = m.home_goals + m.away_goals
    btts = m.home_goals > 0 and m.away_goals > 0
    mk = market.lower()

    if "mais de 2,5" in mk:
        return total >= 3
    if "menos de 2,5" in mk:
        return total < 3
    if "ambos marcam" in mk:
        return btts
    if "ambos não marcam" in mk:
        return not btts
    if "gol no 2º tempo" in mk or "gol depois dos 75" in mk:
        h2 = _half2_total(m)
        return None if h2 is None else h2 > 0

    # mercados direcionais: descobrir o time-sujeito pelo nome no texto do mercado.
    subj = a_id if a_name in market else (b_id if b_name in market else None)
    if subj is None:
        return None
    if "não sofre gol" in mk or "clean sheet" in mk:
        return m.goals_against(subj) == 0
    if "sofre gol" in mk:
        return m.goals_against(subj) > 0
    if "não marca" in mk:
        return m.goals_for(subj) == 0
    if "marca o primeiro gol" in mk:
        from betstats.features.base import scored_first
        return scored_first(m, subj)  # None se sem eventos
    if "marcar" in mk or "marca" in mk:
        return m.goals_for(subj) > 0
    if "vitória" in mk or "1x2" in mk:
        return m.result_for(subj) == "V"
    if "não perde" in mk or "dupla chance" in mk:
        return m.result_for(subj) != "D"
    return None


def _family(key: str) -> str:
    return "CONTRASTE" if key.startswith("contraste:") else "base"


def _canon(market: str, a_name: str, b_name: str) -> str:
    """Normaliza o mercado removendo o nome do time (agrega entre times)."""
    return market.replace(a_name, "{T}").replace(b_name, "{T}")


def main() -> int:
    provider = ESPNProvider()
    fixtures = [f for f in provider.list_fixtures(WC) if f.finished]
    print(f"Jogos encerrados no cache: {len(fixtures)}")

    # full match-list por time (memoizado), pra fatiar 'jogos anteriores a D'.
    full: dict[int, TeamTournamentData] = {}

    def team_data(tid: int) -> TeamTournamentData:
        if tid not in full:
            full[tid] = provider.build_team_tournament(WC, tid)
        return full[tid]

    # acumuladores: (family, canon_market, strength) -> [hits, total]
    agg: dict[tuple[str, str, str], list[int]] = defaultdict(lambda: [0, 0])
    n_eval = n_skip = 0

    for fx in fixtures:
        a, b = fx.home, fx.away
        da_full, db_full = team_data(a.id), team_data(b.id)
        mobj = next((m for m in da_full.matches if m.fixture_id == fx.fixture_id), None)
        if mobj is None:
            continue
        prior_a = [m for m in da_full.matches if m.date < mobj.date]
        prior_b = [m for m in db_full.matches if m.date < mobj.date]
        if len(prior_a) < MIN_PRIOR or len(prior_b) < MIN_PRIOR:
            n_skip += 1
            continue
        n_eval += 1
        da = TeamTournamentData(team=a, competition=WC.key, matches=prior_a)
        db = TeamTournamentData(team=b, competition=WC.key, matches=prior_b)
        facts = engine.run(da, RULES) + engine.run(db, RULES) + engine.confronto(da, db, RULES)
        markets.attach_markets(facts)
        for f in facts:
            for mkt in f.markets:
                res = evaluate(mkt, mobj, a.id, a.name, b.id, b.name)
                if res is None:
                    continue
                slot = agg[(_family(f.key), _canon(mkt, a.name, b.name), f.strength)]
                slot[0] += int(res)
                slot[1] += 1

    print(f"Confrontos avaliados: {n_eval} | pulados (histórico < {MIN_PRIOR}): {n_skip}\n")
    print(f"{'família':10} {'mercado':32} {'força':9} {'acerto':>8} {'n':>4}")
    print("-" * 70)
    for (fam, mkt, strg), (hits, tot) in sorted(agg.items()):
        rate = hits / tot * 100 if tot else 0
        flag = "  ⚠ n baixo" if tot < 5 else ""
        print(f"{fam:10} {mkt[:32]:32} {strg or '—':9} {rate:6.0f}% {tot:4d}{flag}")

    # resumo forte vs moderado (o que o backtest precisa provar: forte > moeda)
    print("\nResumo por força (todos os mercados):")
    for strg in ("forte", "moderado"):
        rows = [(h, t) for (_, _, s), (h, t) in agg.items() if s == strg]
        h, t = sum(r[0] for r in rows), sum(r[1] for r in rows)
        print(f"  {strg:9}: {(h / t * 100 if t else 0):5.0f}% acerto em n={t}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
