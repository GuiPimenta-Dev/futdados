"""Orquestração ponta a ponta: coletor -> features -> validação -> LLMs -> saída.

Cada estágio é determinístico até os LLMs. `use_llm=False` para na validação
(útil offline / sem ANTHROPIC_API_KEY).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from . import validate
from .config import CompetitionConfig
from .data.provider import DataProvider
from .features import engine, markets
from .models import Fact, RankedFact, Team, TeamTournamentData
from .rules.base import LeagueRules

if TYPE_CHECKING:  # importar os LLMs só sob type-checking — mantém o caminho
    from .llm.writer import ScriptOutput  # offline (--no-llm) sem deps de LLM.


@dataclass
class PipelineResult:
    matchup: str
    phase: str
    candidates: list[Fact]
    ranked: list[RankedFact] | None = None
    script: "ScriptOutput | None" = None
    team_a: Team | None = None  # time mandante (subjeito de data_a) — p/ escudo no vídeo
    team_b: Team | None = None


def run_matchup(
    data_a: TeamTournamentData,
    data_b: TeamTournamentData,
    matchup: str,
    phase: str,
    rules: LeagueRules,
    use_llm: bool,
) -> PipelineResult:
    facts = (
        engine.run(data_a, rules)
        + engine.run(data_b, rules)
        + engine.confronto(data_a, data_b, rules)  # mercados do jogo por convergência
    )
    markets.attach_markets(facts)  # anexa mercado + força (porta de elegibilidade)
    candidates = validate.validate(facts)
    result = PipelineResult(
        matchup=matchup,
        phase=phase,
        candidates=candidates,
        team_a=data_a.team,
        team_b=data_b.team,
    )
    if use_llm and candidates:
        from .llm import ranker, writer  # import tardio: só quando há LLM

        result.ranked = ranker.rank(matchup, candidates)
        result.script = writer.write_script(matchup, phase, result.ranked)
    return result


def run_fixture(
    provider: DataProvider,
    comp: CompetitionConfig,
    rules: LeagueRules,
    fixture_id: int,
    use_llm: bool,
) -> PipelineResult:
    brief = provider.get_fixture(comp, fixture_id)
    if brief is None:
        raise ValueError(f"Jogo {fixture_id} não encontrado em {comp.label}.")
    recent = rules.fetch_window()
    data_a = provider.build_team_tournament(comp, brief.home.id, recent=recent)
    data_b = provider.build_team_tournament(comp, brief.away.id, recent=recent)
    matchup = f"{brief.home.name} x {brief.away.name}"
    return run_matchup(data_a, data_b, matchup, brief.round or comp.label, rules, use_llm)
