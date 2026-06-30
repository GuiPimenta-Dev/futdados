"""Regras do Brasileirão (handoff a partir de 22/jul).

Difere da Copa em três pontos: janela = últimos N jogos; tem tabela (libera as
famílias de MANDO DE CAMPO e G6/Z4); e a nomenclatura de período. A feature
engineering e os LLMs NÃO mudam — só esta peça e o DataProvider (que fornece a
tabela via get_standings) trocam.
"""

from __future__ import annotations

from ..config import BRASILEIRAO_A_2026, CompetitionConfig
from ..models import Fact, Match, Team, TeamTournamentData
from .base import LeagueRules

DEFAULT_WINDOW = 10
G6_CUTOFF = 6  # posições 1..6 = G6
Z4_CUTOFF = 17  # posições 17..20 = Z4 (Série A tem 20 times)


class BrasileiraoRules(LeagueRules):
    def __init__(
        self,
        competition: CompetitionConfig = BRASILEIRAO_A_2026,
        window: int = DEFAULT_WINDOW,
        table_position: dict[int, int] | None = None,
    ) -> None:
        self.competition = competition
        self.window = window
        # team_id -> posição na tabela (1..20). Vazio = tabela desconhecida
        # (pula as famílias G6/Z4, mas mantém mando de campo).
        self.table_position = table_position or {}

    def window_matches(self, data: TeamTournamentData) -> list[Match]:
        return list(data.matches[-self.window :])

    def period_label(self) -> str:
        return f"nos últimos {self.window} jogos"

    def has_table(self) -> bool:
        return True

    def fetch_window(self) -> int | None:
        return self.window

    def extra_facts(self, team: Team, matches: list[Match], period: str) -> list[Fact]:
        facts = self._mando(team, matches, period)
        if self.table_position:
            facts += self._tabela(team, matches, period)
        return facts

    # --- mando de campo (casa/fora) ----------------------------------------
    def _mando(self, team: Team, matches: list[Match], period: str) -> list[Fact]:
        tid, name = team.id, team.name
        out: list[Fact] = []
        splits = (
            ("casa", "Em casa", [m for m in matches if m.is_home(tid)]),
            ("fora", "Fora de casa", [m for m in matches if not m.is_home(tid)]),
        )
        for local, prep, subset in splits:
            if len(subset) < 2:
                continue
            v = sum(1 for m in subset if m.result_for(tid) == "V")
            e = sum(1 for m in subset if m.result_for(tid) == "E")
            d = sum(1 for m in subset if m.result_for(tid) == "D")
            out.append(
                Fact(
                    text=f"{prep} {period}, {name} fez {v}V {e}E {d}D em {len(subset)} jogos.",
                    value=f"{v}V {e}E {d}D ({local})",
                    sample=len(subset),
                    category="mando",
                    kind="contagem",
                    robustness="dura",
                    team=name,
                    key=f"mando:{local}",
                )
            )
        return out

    # --- G6 / Z4 -----------------------------------------------------------
    def _tier(self, opp_id: int) -> str | None:
        pos = self.table_position.get(opp_id)
        if pos is None:
            return None
        if pos <= G6_CUTOFF:
            return "G6"
        if pos >= Z4_CUTOFF:
            return "Z4"
        return None

    def _tabela(self, team: Team, matches: list[Match], period: str) -> list[Fact]:
        tid, name = team.id, team.name
        out: list[Fact] = []

        g6 = [m for m in matches if self._tier(m.opponent(tid).id) == "G6"]
        if g6:
            v = sum(1 for m in g6 if m.result_for(tid) == "V")
            e = sum(1 for m in g6 if m.result_for(tid) == "E")
            d = sum(1 for m in g6 if m.result_for(tid) == "D")
            out.append(
                Fact(
                    text=f"Contra times do G6 {period}, {name} fez {v}V {e}E {d}D em {len(g6)} jogos.",
                    value=f"{v}V {e}E {d}D vs G6",
                    sample=len(g6),
                    category="tabela",
                    kind="contagem",
                    robustness="dura",
                    team=name,
                    key="tabela:g6",
                )
            )
            if v == 0:
                out.append(
                    Fact(
                        text=f"{name} ainda não venceu nenhum adversário do G6 {period} ({len(g6)} jogos).",
                        value="0 vitórias vs G6",
                        sample=len(g6),
                        category="tabela",
                        kind="binario",
                        robustness="dura",
                        team=name,
                        key="tabela:g6_sem_vitoria",
                    )
                )

        z4 = [m for m in matches if self._tier(m.opponent(tid).id) == "Z4"]
        if z4:
            v = sum(1 for m in z4 if m.result_for(tid) == "V")
            gf = sum(m.goals_for(tid) for m in z4)
            out.append(
                Fact(
                    text=f"Contra o Z4 {period}, {name} venceu {v} de {len(z4)} e marcou {gf} gols.",
                    value=f"{v}/{len(z4)} vs Z4",
                    sample=len(z4),
                    category="tabela",
                    kind="contagem",
                    robustness="dura",
                    team=name,
                    key="tabela:z4",
                )
            )
        return out
