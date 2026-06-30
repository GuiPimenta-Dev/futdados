"""LeagueRules — o que muda de uma competição para outra.

A feature engineering e os LLMs são IGUAIS entre Copa e Brasileirão. O que
muda é: quais jogos entram na janela, como o período é nomeado no roteiro, e
se há tabela (G6/Z4). Trocar a regra = trocar a peça.
"""

from __future__ import annotations

from abc import ABC, abstractmethod

from ..config import CompetitionConfig
from ..models import Fact, Match, Team, TeamTournamentData


class LeagueRules(ABC):
    competition: CompetitionConfig

    @abstractmethod
    def window_matches(self, data: TeamTournamentData) -> list[Match]:
        """Quais jogos do time entram no cálculo das estatísticas."""

    @abstractmethod
    def period_label(self) -> str:
        """Como o período é dito no roteiro, ex.: 'nesta Copa'."""

    @abstractmethod
    def has_table(self) -> bool:
        """Se a competição tem tabela (libera famílias G6/Z4, casa/fora)."""

    def extra_facts(self, team: Team, matches: list[Match], period: str) -> list[Fact]:
        """Fatos específicos da liga, além dos analistas padrão (default: nenhum)."""
        return []

    def fetch_window(self) -> int | None:
        """Quantos jogos recentes buscar em detalhe (None = todos).

        Copa busca todos (poucos jogos); ligas longas limitam para não estourar
        o rate limit baixando 38 rodadas.
        """
        return None
