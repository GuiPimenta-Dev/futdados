"""Adapter da API pública (não-oficial) da ESPN — fonte GRATUITA do MVP.

Sem chave. Cobre a Copa 2026 com a mesma profundidade da API-Football: fixtures,
minuto dos gols (com gol-contra/pênalti), placar do 1º tempo, disputa de
pênaltis, estatísticas por jogo (chutes/posse/cartões) e tabela de grupos.

Normaliza o JSON da ESPN para os tipos de models.py — o resto do pipeline não
conhece a fonte. Como o motor só usa jogos JÁ ENCERRADOS (dados pré-jogo), o
cache em disco é permanente: uma quebra futura de schema da ESPN vira conserto
de parsing, não perda de dado.

⚠️ API não-oficial: sem ToS pública nem garantia de estabilidade. Aceitável pro
MVP com parsing defensivo; troque para `api_football` quando precisar de uma
fonte contratual (BETSTATS_PROVIDER=api_football).
"""

from __future__ import annotations

import re
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
from .provider import DataProvider, FixtureBrief

# CompetitionConfig.key -> slug de liga da ESPN.
_LEAGUE_SLUG = {"wc2026": "fifa.world", "brasileirao_a": "bra.1"}

# season.slug da ESPN -> rótulo de fase em PT-BR (Copa).
_PHASE_PT = {
    "group-stage": "Fase de grupos",
    "round-of-32": "16-avos de final",
    "round-of-16": "Oitavas de final",
    "quarterfinals": "Quartas de final",
    "semifinals": "Semifinal",
    "3rd-place-match": "Disputa de 3º lugar",
    "final": "Final",
}

_CLOCK_RE = re.compile(r"(\d+)'(?:\+(\d+)')?")


class ESPNError(RuntimeError):
    pass


class ESPNProvider(DataProvider):
    def __init__(self) -> None:
        self.base = config.ESPN_BASE
        self.standings_base = config.ESPN_STANDINGS_BASE

    # --- HTTP + cache -------------------------------------------------------
    def _slug(self, comp: CompetitionConfig) -> str:
        slug = _LEAGUE_SLUG.get(comp.key)
        if not slug:
            raise ESPNError(f"Sem slug ESPN para a competição {comp.key!r}.")
        return slug

    def _get(self, url: str) -> dict[str, Any]:
        """GET com cache permanente (jogos encerrados não mudam)."""
        cached = cache.get(url)
        if cached is not None:
            return cached
        resp = httpx.get(url, headers={"User-Agent": "betstats/1.0"}, timeout=30.0)
        resp.raise_for_status()
        data = resp.json()
        cache.put(url, data)
        return data

    # --- normalização -------------------------------------------------------
    @staticmethod
    def _team(node: dict) -> Team:
        t = node.get("team", node)
        logos = t.get("logos") or []
        logo = str(logos[0]["href"]) if logos and logos[0].get("href") else t.get("logo")
        return Team(
            id=int(t["id"]),
            name=localize(str(t.get("displayName") or t.get("name"))),
            logo=str(logo) if logo else None,
        )

    @staticmethod
    def _phase(slug: str) -> str:
        return _PHASE_PT.get(slug, slug.replace("-", " ").title() if slug else "")

    def _brief(self, ev: dict) -> FixtureBrief:
        comp = ev["competitions"][0]
        comps = comp["competitors"]
        home = next(c for c in comps if c.get("homeAway") == "home")
        away = next(c for c in comps if c.get("homeAway") == "away")
        completed = bool((ev.get("status", {}).get("type", {}) or {}).get("completed"))
        return FixtureBrief(
            fixture_id=int(ev["id"]),
            date=str(ev.get("date", "")),
            round=self._phase(str((ev.get("season") or {}).get("slug", ""))),
            home=self._team(home),
            away=self._team(away),
            status="FT" if completed else "NS",  # finished basta p/ o pipeline
        )

    @staticmethod
    def _clock(disp: str) -> tuple[int, int]:
        m = _CLOCK_RE.search(disp or "")
        if not m:
            return 0, 0
        return int(m.group(1)), int(m.group(2) or 0)

    @staticmethod
    def _event_type(text: str, scoring: bool) -> EventType:
        if scoring:
            return EventType.GOAL
        low = text.lower()
        if "card" in low:
            return EventType.CARD
        if "substitution" in low:
            return EventType.SUBST
        return EventType.OTHER

    def _events(self, summary: dict) -> list[MatchEvent]:
        out: list[MatchEvent] = []
        for ev in summary.get("keyEvents", []) or []:
            period = ((ev.get("period") or {}).get("number")) or 0
            if period >= 5:
                continue  # disputa de pênaltis — não é gol de jogo
            text = str((ev.get("type") or {}).get("text", ""))
            minute, extra = self._clock((ev.get("clock") or {}).get("displayValue", ""))
            team = ev.get("team") or {}
            athletes = ev.get("athletesInvolved") or []
            out.append(
                MatchEvent(
                    minute=minute,
                    extra=extra,
                    team_id=int(team["id"]) if team.get("id") else 0,
                    type=self._event_type(text, bool(ev.get("scoringPlay"))),
                    detail=text,  # ex.: "Goal", "Own Goal", "Penalty - Scored"
                    player=str(athletes[0].get("displayName", "")) if athletes else "",
                )
            )
        return out

    @staticmethod
    def _stats(summary: dict) -> dict[int, TeamMatchStats]:
        out: dict[int, TeamMatchStats] = {}
        for block in (summary.get("boxscore") or {}).get("teams", []) or []:
            tid = int((block.get("team") or {})["id"])
            by = {str(s.get("name")): s.get("displayValue") for s in block.get("statistics", []) or []}

            def num(key: str) -> int | None:
                v = by.get(key)
                if v is None:
                    return None
                try:
                    return int(str(v).replace("%", "").strip())
                except (ValueError, TypeError):
                    return None

            out[tid] = TeamMatchStats(
                team_id=tid,
                shots_total=num("totalShots"),
                shots_on_goal=num("shotsOnTarget"),
                possession_pct=float(num("possessionPct")) if num("possessionPct") is not None else None,
                corners=num("wonCorners"),
                fouls=num("foulsCommitted"),
                yellow_cards=num("yellowCards"),
                red_cards=num("redCards"),
            )
        return out

    @staticmethod
    def _linescore0(c: dict) -> int | None:
        ls = c.get("linescores") or []
        if not ls:
            return None
        v = ls[0].get("displayValue", ls[0].get("value"))
        try:
            return int(v)
        except (ValueError, TypeError):
            return None

    def _match(self, comp: CompetitionConfig, brief: FixtureBrief, summary: dict) -> Match:
        head_comp = summary["header"]["competitions"][0]
        comps = head_comp["competitors"]
        home = next(c for c in comps if c.get("homeAway") == "home")
        away = next(c for c in comps if c.get("homeAway") == "away")
        pen_h, pen_a = home.get("shootoutScore"), away.get("shootoutScore")
        return Match(
            fixture_id=brief.fixture_id,
            date=brief.date,
            competition=comp.key,
            round=brief.round,
            home=self._team(home),
            away=self._team(away),
            home_goals=int(home.get("score") or 0),
            away_goals=int(away.get("score") or 0),
            ht_home=self._linescore0(home),
            ht_away=self._linescore0(away),
            pen_home=int(pen_h) if pen_h is not None else None,
            pen_away=int(pen_a) if pen_a is not None else None,
            events=self._events(summary),
            stats=self._stats(summary),
        )

    # --- DataProvider -------------------------------------------------------
    def list_fixtures(self, comp: CompetitionConfig) -> list[FixtureBrief]:
        url = f"{self.base}/{self._slug(comp)}/scoreboard?dates={comp.season}&limit=400"
        data = self._get(url)
        return [self._brief(ev) for ev in data.get("events", []) or []]

    def get_fixture(self, comp: CompetitionConfig, fixture_id: int) -> FixtureBrief | None:
        return next(
            (b for b in self.list_fixtures(comp) if b.fixture_id == fixture_id), None
        )

    def _summary(self, comp: CompetitionConfig, fixture_id: int) -> dict:
        url = f"{self.base}/{self._slug(comp)}/summary?event={fixture_id}"
        return self._get(url)

    def build_team_tournament(
        self, comp: CompetitionConfig, team_id: int, recent: int | None = None
    ) -> TeamTournamentData:
        played = [
            b
            for b in self.list_fixtures(comp)
            if b.finished and team_id in (b.home.id, b.away.id)
        ]
        played.sort(key=lambda b: b.date)
        if recent is not None:
            played = played[-recent:]
        matches = [self._match(comp, b, self._summary(comp, b.fixture_id)) for b in played]
        team = next(
            (m.home if m.home.id == team_id else m.away for m in matches), None
        ) or Team(id=team_id, name=f"Time {team_id}")
        return TeamTournamentData(team=team, competition=comp.key, matches=matches)

    def get_standings(self, comp: CompetitionConfig) -> dict[int, int]:
        url = f"{self.standings_base}/{self._slug(comp)}/standings?season={comp.season}"
        try:
            data = self._get(url)
        except httpx.HTTPError:
            return {}
        table: dict[int, int] = {}
        for child in data.get("children", []) or []:
            for entry in (child.get("standings") or {}).get("entries", []) or []:
                tid = int((entry.get("team") or {}).get("id") or 0)
                stats = {s.get("name"): s.get("value") for s in entry.get("stats", []) or []}
                rank = stats.get("rank") or stats.get("note")
                if tid and rank is not None:
                    table[tid] = int(rank)
        return table
