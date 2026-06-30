"""Interface DataProvider — a peça que se troca no handoff Copa -> Brasileirão.

Qualquer fonte (API-Football hoje; outra amanhã) implementa esta interface.
O resto do pipeline (features, validação, LLMs) não conhece a fonte.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass

from ..config import CompetitionConfig
from ..models import Team, TeamTournamentData

FINISHED_STATUSES = {"FT", "AET", "PEN"}


@dataclass
class FixtureBrief:
    """Resumo de um jogo do calendário (pode ainda não ter sido disputado)."""

    fixture_id: int
    date: str
    round: str
    home: Team
    away: Team
    status: str

    @property
    def finished(self) -> bool:
        return self.status in FINISHED_STATUSES


class DataProvider(ABC):
    @abstractmethod
    def list_fixtures(self, comp: CompetitionConfig) -> list[FixtureBrief]:
        """Todos os jogos da competição (disputados e por disputar)."""

    @abstractmethod
    def get_fixture(self, comp: CompetitionConfig, fixture_id: int) -> FixtureBrief | None:
        """Um jogo específico (para descobrir os dois times de um confronto)."""

    @abstractmethod
    def build_team_tournament(
        self, comp: CompetitionConfig, team_id: int, recent: int | None = None
    ) -> TeamTournamentData:
        """Os jogos JÁ disputados de um time na competição, normalizados.

        `recent`: se definido, busca detalhe (eventos/stats) só dos N jogos mais
        recentes — evita estourar o rate limit em ligas longas (Brasileirão).
        """

    def get_standings(self, comp: CompetitionConfig) -> dict[int, int]:
        """Mapa team_id -> posição (1..N). Default vazio (ex.: Copa não usa)."""
        return {}
