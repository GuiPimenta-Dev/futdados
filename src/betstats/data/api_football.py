"""Adapter da API-Football (api-sports.io / RapidAPI).

Normaliza o JSON cru para os tipos de models.py. Os contornos exatos das
respostas (campos, IDs) devem ser confirmados na primeira chamada real — ver
§5 do DESIGN.md. Jogos finalizados são cacheados em disco.
"""

from __future__ import annotations

import time
from typing import Any

import httpx

from .. import config
from ..config import CompetitionConfig
from ..models import (
    EventType,
    Match,
    MatchEvent,
    Team,
    TeamMatchStats,
    TeamTournamentData,
)
from . import cache
from .i18n import localize
from .provider import DataProvider, FixtureBrief, FINISHED_STATUSES


class APIFootballError(RuntimeError):
    pass


class APIFootballProvider(DataProvider):
    def __init__(self, api_key: str | None = None) -> None:
        self.api_key = api_key or config.APISPORTS_KEY
        if not self.api_key:
            raise APIFootballError(
                "APISPORTS_KEY ausente. Preencha o .env (ver .env.example)."
            )
        self.host = config.API_FOOTBALL_HOST
        self.via_rapidapi = config.VIA_RAPIDAPI
        self.base = f"https://{self.host}" + ("/v3" if self.via_rapidapi else "")

    # --- HTTP ---------------------------------------------------------------
    def _headers(self) -> dict[str, str]:
        if self.via_rapidapi:
            return {"x-rapidapi-key": self.api_key, "x-rapidapi-host": self.host}
        return {"x-apisports-key": self.api_key}

    def _get(self, path: str, params: dict[str, Any]) -> list[dict]:
        """GET com cache + retry de rate limit. Retorna a lista `response`.

        Em 429 (limite por minuto do plano grátis) espera e tenta de novo; o
        cache guarda cada resposta, então um re-run retoma de onde parou.
        """
        key = f"{path}?{sorted(params.items())}"
        cached = cache.get(key)
        if cached is not None:
            return cached

        url = f"{self.base}{path}"
        for attempt in range(config.API_MAX_RETRIES):
            resp = httpx.get(url, params=params, headers=self._headers(), timeout=30.0)
            if resp.status_code == 429:
                wait = int(resp.headers.get("Retry-After") or 0) or config.API_RATE_WAIT
                print(f"[rate limit] 429 em {path} — aguardando {wait}s e tentando de novo...")
                time.sleep(wait)
                continue
            resp.raise_for_status()
            payload = resp.json()
            errors = payload.get("errors")
            if errors:  # erro de plano/cota diária — repetir não adianta
                raise APIFootballError(f"API-Football retornou erros: {errors}")
            data = payload.get("response", [])
            cache.put(key, data)
            return data
        raise APIFootballError(
            f"Rate limit persistente em {path} após {config.API_MAX_RETRIES} tentativas."
        )

    # --- normalização -------------------------------------------------------
    @staticmethod
    def _team(node: dict) -> Team:
        logo = node.get("logo")
        return Team(
            id=int(node["id"]),
            name=localize(str(node["name"])),
            logo=str(logo) if logo else None,
        )

    def _brief(self, fx: dict) -> FixtureBrief:
        return FixtureBrief(
            fixture_id=int(fx["fixture"]["id"]),
            date=str(fx["fixture"]["date"]),
            round=str(fx["league"].get("round", "")),
            home=self._team(fx["teams"]["home"]),
            away=self._team(fx["teams"]["away"]),
            status=str(fx["fixture"]["status"]["short"]),
        )

    @staticmethod
    def _event_type(raw: str) -> EventType:
        raw = (raw or "").lower()
        if raw == "goal":
            return EventType.GOAL
        if raw == "card":
            return EventType.CARD
        if raw == "subst":
            return EventType.SUBST
        return EventType.OTHER

    def _events(self, fixture_id: int) -> list[MatchEvent]:
        out: list[MatchEvent] = []
        for ev in self._get("/fixtures/events", {"fixture": fixture_id}):
            t = ev.get("time", {}) or {}
            out.append(
                MatchEvent(
                    minute=int(t.get("elapsed") or 0),
                    extra=int(t.get("extra") or 0),
                    team_id=int((ev.get("team") or {}).get("id") or 0),
                    type=self._event_type(ev.get("type", "")),
                    detail=str(ev.get("detail", "")),
                    player=str((ev.get("player") or {}).get("name") or ""),
                )
            )
        return out

    @staticmethod
    def _stat_int(value: Any) -> int | None:
        if value is None:
            return None
        try:
            return int(str(value).replace("%", "").strip())
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _stat_float(value: Any) -> float | None:
        if value is None:
            return None
        try:
            return float(str(value).replace("%", "").strip())
        except (ValueError, TypeError):
            return None

    def _stats(self, fixture_id: int) -> dict[int, TeamMatchStats]:
        out: dict[int, TeamMatchStats] = {}
        for block in self._get("/fixtures/statistics", {"fixture": fixture_id}):
            team_id = int((block.get("team") or {}).get("id") or 0)
            by_type = {
                str(s.get("type")): s.get("value")
                for s in (block.get("statistics") or [])
            }
            poss = by_type.get("Ball Possession")
            out[team_id] = TeamMatchStats(
                team_id=team_id,
                shots_total=self._stat_int(by_type.get("Total Shots")),
                shots_on_goal=self._stat_int(by_type.get("Shots on Goal")),
                possession_pct=float(self._stat_int(poss)) if poss else None,
                corners=self._stat_int(by_type.get("Corner Kicks")),
                fouls=self._stat_int(by_type.get("Fouls")),
                yellow_cards=self._stat_int(by_type.get("Yellow Cards")),
                red_cards=self._stat_int(by_type.get("Red Cards")),
                blocked_shots=self._stat_int(by_type.get("Blocked Shots")),
                # xG: API-Football expõe `expected_goals` em ligas cobertas (WC2026 a verificar).
                xg=self._stat_float(by_type.get("expected_goals")),
            )
        return out

    def _full_match(self, comp: CompetitionConfig, fx: dict) -> Match:
        score = fx.get("score", {}) or {}
        ht = score.get("halftime", {}) or {}
        pen = score.get("penalty", {}) or {}
        fixture_id = int(fx["fixture"]["id"])
        return Match(
            fixture_id=fixture_id,
            date=str(fx["fixture"]["date"]),
            competition=comp.key,
            round=str(fx["league"].get("round", "")),
            home=self._team(fx["teams"]["home"]),
            away=self._team(fx["teams"]["away"]),
            home_goals=int((fx.get("goals") or {}).get("home") or 0),
            away_goals=int((fx.get("goals") or {}).get("away") or 0),
            ht_home=ht.get("home"),
            ht_away=ht.get("away"),
            pen_home=pen.get("home"),
            pen_away=pen.get("away"),
            events=self._events(fixture_id),
            stats=self._stats(fixture_id),
        )

    # --- DataProvider -------------------------------------------------------
    def list_fixtures(self, comp: CompetitionConfig) -> list[FixtureBrief]:
        raw = self._get(
            "/fixtures", {"league": comp.league_id, "season": comp.season}
        )
        return [self._brief(fx) for fx in raw]

    def get_fixture(
        self, comp: CompetitionConfig, fixture_id: int
    ) -> FixtureBrief | None:
        raw = self._get("/fixtures", {"id": fixture_id})
        return self._brief(raw[0]) if raw else None

    def get_standings(self, comp: CompetitionConfig) -> dict[int, int]:
        raw = self._get(
            "/standings", {"league": comp.league_id, "season": comp.season}
        )
        table: dict[int, int] = {}
        if raw:
            for group in (raw[0].get("league", {}) or {}).get("standings", []):
                for row in group:
                    table[int(row["team"]["id"])] = int(row["rank"])
        return table

    def build_team_tournament(
        self, comp: CompetitionConfig, team_id: int, recent: int | None = None
    ) -> TeamTournamentData:
        raw = self._get(
            "/fixtures",
            {"league": comp.league_id, "season": comp.season, "team": team_id},
        )
        finished = [
            fx for fx in raw if fx["fixture"]["status"]["short"] in FINISHED_STATUSES
        ]
        finished.sort(key=lambda fx: fx["fixture"]["date"])
        if recent is not None:  # só baixa detalhe dos N mais recentes
            finished = finished[-recent:]
        matches = [self._full_match(comp, fx) for fx in finished]
        team = next(
            (
                m.home if m.home.id == team_id else m.away
                for m in matches
                if team_id in (m.home.id, m.away.id)
            ),
            Team(id=team_id, name=f"Time {team_id}"),
        )
        return TeamTournamentData(team=team, competition=comp.key, matches=matches)
