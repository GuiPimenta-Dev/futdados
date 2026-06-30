"""Builders enxutos para montar Match sintético nos testes."""

from __future__ import annotations

from betstats.models import EventType, Match, MatchEvent, Team, TeamMatchStats


def goal(minute: int, team_id: int, *, own: bool = False, pen: bool = False) -> MatchEvent:
    detail = "Own Goal" if own else ("Penalty" if pen else "Normal Goal")
    return MatchEvent(
        minute=minute, extra=0, team_id=team_id, type=EventType.GOAL, detail=detail
    )


def make_match(
    team_id: int = 1,
    opp_id: int = 2,
    *,
    gf: int = 0,
    ga: int = 0,
    ht_for: int | None = None,
    ht_against: int | None = None,
    mins_for=(),
    mins_against=(),
    events: list[MatchEvent] | None = None,
    is_home: bool = True,
    pen_for: int | None = None,
    pen_against: int | None = None,
    sog_for: int | None = None,
    shots_for: int | None = None,
    poss_for: float | None = None,
    reds_for: int | None = None,
    poss_against: float | None = None,
    fid: int = 1,
    rnd: str = "Grupo",
) -> Match:
    home_id, away_id = (team_id, opp_id) if is_home else (opp_id, team_id)
    home_goals, away_goals = (gf, ga) if is_home else (ga, gf)
    ht_home, ht_away = (ht_for, ht_against) if is_home else (ht_against, ht_for)
    ph, pa = (pen_for, pen_against) if is_home else (pen_against, pen_for)

    if events is None:
        events = [goal(m, team_id) for m in mins_for] + [
            goal(m, opp_id) for m in mins_against
        ]

    stats: dict[int, TeamMatchStats] = {}
    if any(v is not None for v in (sog_for, shots_for, poss_for, reds_for)):
        stats[team_id] = TeamMatchStats(
            team_id=team_id,
            shots_total=shots_for,
            shots_on_goal=sog_for,
            possession_pct=poss_for,
            red_cards=reds_for,
        )
    if poss_against is not None:
        stats[opp_id] = TeamMatchStats(team_id=opp_id, possession_pct=poss_against)

    return Match(
        fixture_id=fid,
        date="2026-06-01T00:00:00+00:00",
        competition="wc2026",
        round=rnd,
        home=Team(home_id, f"T{home_id}"),
        away=Team(away_id, f"T{away_id}"),
        home_goals=home_goals,
        away_goals=away_goals,
        ht_home=ht_home,
        ht_away=ht_away,
        pen_home=ph,
        pen_away=pa,
        events=events,
        stats=stats,
    )


def by_key(facts, key):
    return next((f for f in facts if f.key == key), None)
