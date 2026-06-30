"""Força de adversário via World Football Elo (eloratings.net).

USO ESTRITAMENTE INTERNO (DESIGN §6-bis, decisões #14/#15): pondera/gate a família
de contraste por qualidade de adversário. NUNCA é emitido como `Fact`, nunca vira
mercado, o roteirista NUNCA o vê — assim "favorito" é estruturalmente impossível de
vazar, não só proibido por prompt. Faixas grosseiras (forte/médio/fraco), não número
fino: em amostra de 3 jogos, peso contínuo finge uma precisão que não existe.

Fonte: `eloratings.net/<season>.tsv` (ratings) + `en.teams.tsv` (código → nome em
inglês). O nome da ESPN chega em PT-BR; cruzamos com o mapa inglês→PT-BR de i18n pra
casar os dois lados. Tudo cacheado em disco (ratings de seleção mudam devagar;
refetch = apagar .cache/). Falha de rede degrada pra tabela vazia → tier None →
o gate trata como neutro (não inventa fraqueza).

`clubelo.com` é o equivalente pra clubes no handoff Brasileirão (mesma mecânica).
"""

from __future__ import annotations

import unicodedata

import httpx

from .. import config
from . import cache
from .i18n import localize

DEFAULT_SEASON = 2026

Tier = str  # "forte" | "medio" | "fraco"
STRONG: Tier = "forte"
MEDIO: Tier = "medio"
FRACO: Tier = "fraco"


def _norm(name: str) -> str:
    """Normaliza pra casar PT-BR e inglês: sem acento, minúsculo, espaços colapsados."""
    s = unicodedata.normalize("NFKD", name or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().split())


def _fetch_tsv(path: str) -> list[list[str]]:
    """GET de um .tsv do eloratings, com cache permanente. [] se a rede falhar."""
    url = f"{config.ELO_BASE}/{path}"
    cached = cache.get(url)
    if cached is not None:
        return cached
    try:
        resp = httpx.get(url, headers={"User-Agent": "betstats/1.0"}, timeout=30.0)
        resp.raise_for_status()
    except httpx.HTTPError:
        return []
    rows = [ln.split("\t") for ln in resp.text.splitlines() if ln.strip()]
    cache.put(url, rows)
    return rows


# norm(nome) -> (elo, rank), memoizado por season.
_tables: dict[int, dict[str, tuple[float, int]]] = {}


def _table(season: int) -> dict[str, tuple[float, int]]:
    cached = _tables.get(season)
    if cached is not None:
        return cached
    # código -> todos os nomes em inglês (primário + aliases) do en.teams.tsv.
    code_names: dict[str, list[str]] = {}
    for row in _fetch_tsv("en.teams.tsv"):
        if len(row) >= 2:
            code_names[row[0]] = [n for n in row[1:] if n]
    out: dict[str, tuple[float, int]] = {}
    for row in _fetch_tsv(f"{season}.tsv"):
        if len(row) < 4:
            continue
        code = row[2]
        try:
            rank, elo = int(row[1]), float(row[3])
        except ValueError:
            continue
        for en in code_names.get(code, []):
            out[_norm(en)] = (elo, rank)  # chave em inglês
            out[_norm(localize(en))] = (elo, rank)  # e em PT-BR (nome que vem da ESPN)
    _tables[season] = out
    return out


def _lookup(team_name: str, season: int) -> tuple[float, int] | None:
    return _table(season).get(_norm(team_name))


def rating(team_name: str, season: int = DEFAULT_SEASON) -> float | None:
    """Elo do time, ou None se desconhecido / rede indisponível."""
    hit = _lookup(team_name, season)
    return hit[0] if hit else None


def rank(team_name: str, season: int = DEFAULT_SEASON) -> int | None:
    """Posição no ranking Elo (1 = melhor), ou None."""
    hit = _lookup(team_name, season)
    return hit[1] if hit else None


def tier(team_name: str, season: int = DEFAULT_SEASON) -> Tier | None:
    """Faixa grosseira de força: 'forte' | 'medio' | 'fraco' (None se desconhecido).

    O chamador (engine.confronto) trata None como neutro — nunca como fraco, pra
    não inventar uma fraqueza que justifique derrubar um contraste.
    """
    elo = rating(team_name, season)
    if elo is None:
        return None
    if elo >= config.ELO_TIER_STRONG:
        return STRONG
    if elo < config.ELO_TIER_WEAK:
        return FRACO
    return MEDIO
