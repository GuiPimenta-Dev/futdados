"""Regras da Copa do Mundo (V1): só os jogos do torneio atual, sem tabela."""

from __future__ import annotations

from ..config import WORLD_CUP_2026, CompetitionConfig
from ..models import Match, TeamTournamentData
from .base import LeagueRules


class WorldCupRules(LeagueRules):
    def __init__(self, competition: CompetitionConfig = WORLD_CUP_2026) -> None:
        self.competition = competition

    def window_matches(self, data: TeamTournamentData) -> list[Match]:
        # "Só a Copa atual": todos os jogos da seleção no torneio.
        return list(data.matches)

    def period_label(self) -> str:
        return "nesta Copa"

    def has_table(self) -> bool:
        return False
