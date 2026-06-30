"""Dados sintéticos de uma Copa para testar o motor OFFLINE (sem API key).

Permite rodar feature engineering + validação (e os LLMs, se houver chave) sem
bater na API-Football. Os números são fictícios, mas plausíveis para um
mata-mata, e foram desenhados para gerar fatos interessantes.
"""

from __future__ import annotations

from ..models import EventType, Match, MatchEvent, Team, TeamMatchStats, TeamTournamentData

WC = "wc2026"


def _mk_match(
    fid: int,
    rnd: str,
    team: Team,
    opp: Team,
    is_home: bool,
    gf: int,
    ga: int,
    htf: int,
    hta: int,
    mins_for: list[int],
    mins_against: list[int],
    poss_for: float,
    shots_for: int,
    sog_for: int,
    pen_for: int | None = None,
    pen_against: int | None = None,
) -> Match:
    home, away = (team, opp) if is_home else (opp, team)
    home_goals, away_goals = (gf, ga) if is_home else (ga, gf)
    ht_home, ht_away = (htf, hta) if is_home else (hta, htf)
    ph, pa = (pen_for, pen_against) if is_home else (pen_against, pen_for)

    events = [
        MatchEvent(minute=m, extra=0, team_id=team.id, type=EventType.GOAL, detail="Normal Goal")
        for m in mins_for
    ] + [
        MatchEvent(minute=m, extra=0, team_id=opp.id, type=EventType.GOAL, detail="Normal Goal")
        for m in mins_against
    ]
    stats = {
        team.id: TeamMatchStats(
            team_id=team.id,
            shots_total=shots_for,
            shots_on_goal=sog_for,
            possession_pct=poss_for,
            red_cards=0,
        ),
        opp.id: TeamMatchStats(
            team_id=opp.id, possession_pct=round(100 - poss_for, 1), red_cards=0
        ),
    }
    return Match(
        fixture_id=fid,
        date=f"2026-06-{fid:02d}T18:00:00+00:00",
        competition=WC,
        round=rnd,
        home=home,
        away=away,
        home_goals=home_goals,
        away_goals=away_goals,
        ht_home=ht_home,
        ht_away=ht_away,
        pen_home=ph,
        pen_away=pa,
        events=events,
        stats=stats,
    )


def demo_matchup() -> tuple[TeamTournamentData, TeamTournamentData, str, str]:
    brasil = Team(id=6, name="Brasil")
    croacia = Team(id=3, name="Croácia")

    # Brasil: vence tudo, marca em todos, explode no 2º tempo.
    brasil_matches = [
        _mk_match(11, "Grupo - 1", brasil, Team(31, "Sérvia"), True, 2, 0, 0, 0, [52, 78], [], 60, 15, 6),
        _mk_match(12, "Grupo - 2", brasil, Team(32, "Suíça"), False, 1, 0, 0, 0, [83], [], 55, 12, 5),
        _mk_match(13, "Grupo - 3", brasil, Team(33, "Camarões"), True, 3, 1, 0, 1, [55, 67, 89], [33], 58, 18, 9),
        _mk_match(14, "Oitavas", brasil, Team(34, "Coreia do Sul"), True, 2, 1, 1, 1, [20, 75], [40], 62, 17, 8),
    ]

    # Croácia: invicta, defensiva, decidiu nos pênaltis.
    croacia_matches = [
        _mk_match(21, "Grupo - 1", croacia, Team(41, "Marrocos"), False, 0, 0, 0, 0, [], [], 46, 8, 2),
        _mk_match(22, "Grupo - 2", croacia, Team(42, "Bélgica"), True, 1, 0, 0, 0, [88], [], 41, 9, 3),
        _mk_match(23, "Grupo - 3", croacia, Team(43, "Canadá"), False, 1, 1, 1, 0, [35], [70], 48, 10, 4),
        _mk_match(24, "Oitavas", croacia, Team(44, "Japão"), True, 1, 1, 0, 0, [55], [83], 44, 7, 3, pen_for=4, pen_against=2),
    ]

    data_a = TeamTournamentData(team=brasil, competition=WC, matches=brasil_matches)
    data_b = TeamTournamentData(team=croacia, competition=WC, matches=croacia_matches)
    return data_a, data_b, "Brasil x Croácia", "Quartas de final"
