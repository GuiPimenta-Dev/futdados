"""Contratos de dados normalizados do projeto.

A API-Football (ou qualquer fonte) é normalizada para ESTES tipos. Os módulos
de feature engineering, validação e LLM só conhecem estes — nunca o JSON cru
da API. Isso é o que torna o handoff Copa -> Brasileirão uma troca de adapter.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


@dataclass(frozen=True)
class Team:
    id: int
    name: str
    logo: str | None = None  # URL do escudo (best-effort do provider; usado no vídeo)


class EventType(str, Enum):
    GOAL = "goal"
    CARD = "card"
    SUBST = "subst"
    OTHER = "other"


@dataclass
class MatchEvent:
    """Um evento dentro de um jogo. Para gols, `minute` é o minuto do lance."""

    minute: int
    extra: int  # acréscimos (0 se não houver)
    team_id: int  # time do jogador do evento (atenção: gol contra, ver Match)
    type: EventType
    detail: str = ""  # bruto, ex.: "Normal Goal", "Penalty", "Own Goal"
    player: str = ""

    @property
    def total_minute(self) -> int:
        return self.minute + self.extra

    @property
    def is_goal(self) -> bool:
        return self.type == EventType.GOAL

    @property
    def is_own_goal(self) -> bool:
        return self.type == EventType.GOAL and "own" in self.detail.lower()

    @property
    def is_penalty_goal(self) -> bool:
        return self.type == EventType.GOAL and self.detail.lower() == "penalty"


@dataclass
class TeamMatchStats:
    """Estatísticas agregadas de um time num jogo (quando a API fornece)."""

    team_id: int
    shots_total: int | None = None
    shots_on_goal: int | None = None
    possession_pct: float | None = None
    corners: int | None = None
    fouls: int | None = None
    yellow_cards: int | None = None
    red_cards: int | None = None


@dataclass
class Match:
    """Um jogo já disputado, normalizado.

    Contagens de gols vêm do PLACAR (autoritativo, à prova de gol contra);
    timing fino (minuto do 1º gol etc.) vem dos eventos.
    """

    fixture_id: int
    date: str  # ISO
    competition: str
    round: str
    home: Team
    away: Team
    home_goals: int
    away_goals: int
    ht_home: int | None = None  # placar do 1º tempo
    ht_away: int | None = None
    pen_home: int | None = None  # disputa de pênaltis (mata-mata)
    pen_away: int | None = None
    events: list[MatchEvent] = field(default_factory=list)
    stats: dict[int, TeamMatchStats] = field(default_factory=dict)

    # --- helpers por time --------------------------------------------------
    def is_home(self, team_id: int) -> bool:
        return team_id == self.home.id

    def opponent(self, team_id: int) -> Team:
        return self.away if self.is_home(team_id) else self.home

    def goals_for(self, team_id: int) -> int:
        return self.home_goals if self.is_home(team_id) else self.away_goals

    def goals_against(self, team_id: int) -> int:
        return self.away_goals if self.is_home(team_id) else self.home_goals

    def ht_goals_for(self, team_id: int) -> int | None:
        if self.ht_home is None or self.ht_away is None:
            return None
        return self.ht_home if self.is_home(team_id) else self.ht_away

    def ht_goals_against(self, team_id: int) -> int | None:
        if self.ht_home is None or self.ht_away is None:
            return None
        return self.ht_away if self.is_home(team_id) else self.ht_home

    def second_half_goals_for(self, team_id: int) -> int | None:
        ht = self.ht_goals_for(team_id)
        return None if ht is None else self.goals_for(team_id) - ht

    def second_half_goals_against(self, team_id: int) -> int | None:
        ht = self.ht_goals_against(team_id)
        return None if ht is None else self.goals_against(team_id) - ht

    def result_for(self, team_id: int) -> str:
        gf, ga = self.goals_for(team_id), self.goals_against(team_id)
        if gf > ga:
            return "V"
        if gf < ga:
            return "D"
        return "E"

    def clean_sheet(self, team_id: int) -> bool:
        return self.goals_against(team_id) == 0

    @property
    def decided_by_penalties(self) -> bool:
        return self.pen_home is not None and self.pen_away is not None

    def won_shootout(self, team_id: int) -> bool | None:
        if not self.decided_by_penalties:
            return None
        ph = self.pen_home if self.is_home(team_id) else self.pen_away
        pa = self.pen_away if self.is_home(team_id) else self.pen_home
        return ph > pa

    def goal_minutes_for(self, team_id: int) -> list[int]:
        """Minutos dos gols a favor (com correção de gol contra)."""
        mins: list[int] = []
        for ev in self.events:
            if not ev.is_goal:
                continue
            scored_for = (
                ev.team_id != team_id if ev.is_own_goal else ev.team_id == team_id
            )
            if scored_for:
                mins.append(ev.total_minute)
        return sorted(mins)


@dataclass
class TeamTournamentData:
    """Tudo que sabemos de UM time na competição: o insumo do motor."""

    team: Team
    competition: str
    matches: list[Match]  # ordenados do mais antigo ao mais recente

    @property
    def n(self) -> int:
        return len(self.matches)


# --- Saídas do motor --------------------------------------------------------
@dataclass
class Fact:
    """Um fato candidato emitido por um analista (módulo de código)."""

    text: str  # PT-BR, JÁ com o contexto de amostra embutido
    value: str  # valor curto, ex.: "4/4", "80%", "min 23"
    sample: int  # nº de jogos em que o fato se baseia
    category: str  # ataque | defesa | temporal | resultado | anomalia | aposta | confronto
    kind: str  # binario | taxa | sequencia | contagem
    robustness: str  # dura | fragil
    team: str  # nome do time-sujeito
    key: str  # chave de dedup (categoria + tipo de métrica)
    # --- pivot p/ aposta (nível B): preenchidos por features/markets.py ------
    # Mercado(s) de aposta que ESTE fato ilumina (ex.: ["Ambos marcam"]). Vazio
    # = o fato não passou a porta de elegibilidade (§6) ou não mapeia mercado.
    # O LLM só LÊ isto; nunca inventa um mercado.
    markets: list[str] = field(default_factory=list)
    # Força do sinal pro mercado: "forte" | "moderado" | "" (sem mercado).
    strength: str = ""


@dataclass
class RankedFact:
    fact: Fact
    interest: float  # 0..1, julgado pelo LLM
    rationale: str  # por que entra no vídeo
