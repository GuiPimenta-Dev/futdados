"""Configuração central: env vars, modelos de LLM e constantes do motor.

Tudo que muda entre ambientes ou que você pode querer ajustar vive aqui.
"""

from __future__ import annotations

import os
from dataclasses import dataclass


# --- LLM (Claude) -----------------------------------------------------------
# Backend: "claude_cli" usa a ASSINATURA via `claude -p` (padrão — sem crédito
# de API); "api" usa o SDK Anthropic com ANTHROPIC_API_KEY (cobrado por uso).
LLM_BACKEND = os.getenv("BETSTATS_LLM_BACKEND", "claude_cli")

# Backend "claude_cli":
CLAUDE_BIN = os.getenv("BETSTATS_CLAUDE_BIN", "claude")
# Modelo passado ao `claude -p` (vazio = default da sua assinatura).
CLAUDE_CLI_MODEL = os.getenv("BETSTATS_CLAUDE_MODEL", "")

# Backend "api": Sonnet 4.6 nos dois (rápido/barato). Para caprichar no texto,
# troque WRITER_MODEL por "claude-opus-4-8".
RANKER_MODEL = os.getenv("BETSTATS_RANKER_MODEL", "claude-sonnet-4-6")
WRITER_MODEL = os.getenv("BETSTATS_WRITER_MODEL", "claude-sonnet-4-6")

# Pensamento adaptativo (só backend "api") ajuda no julgamento e na escrita.
USE_ADAPTIVE_THINKING = os.getenv("BETSTATS_THINKING", "1") != "0"

RANKER_MAX_TOKENS = 4000
WRITER_MAX_TOKENS = 4000


# --- Fonte de dados ---------------------------------------------------------
# "espn"  = API pública e GRATUITA da ESPN (sem chave; padrão do MVP).
# "api_football" = API-Football (paga p/ a season 2026; fallback robusto).
DATA_PROVIDER = os.getenv("BETSTATS_PROVIDER", "espn")
# Base da API pública da ESPN (não-oficial; ver DESIGN §5).
ESPN_BASE = os.getenv("BETSTATS_ESPN_BASE", "https://site.api.espn.com/apis/site/v2/sports/soccer")
ESPN_STANDINGS_BASE = os.getenv(
    "BETSTATS_ESPN_STANDINGS_BASE", "https://site.api.espn.com/apis/v2/sports/soccer"
)


# --- API-Football -----------------------------------------------------------
APISPORTS_KEY = os.getenv("APISPORTS_KEY", "")
# Rate limit: o plano grátis limita ~10 req/min. Em 429, espera e tenta de novo.
API_MAX_RETRIES = int(os.getenv("BETSTATS_API_MAX_RETRIES", "5"))
API_RATE_WAIT = int(os.getenv("BETSTATS_API_RATE_WAIT", "61"))  # segundos
VIA_RAPIDAPI = os.getenv("API_FOOTBALL_VIA_RAPIDAPI", "") == "1"
API_FOOTBALL_HOST = os.getenv(
    "API_FOOTBALL_HOST",
    "api-football-v1.p.rapidapi.com" if VIA_RAPIDAPI else "v3.football.api-sports.io",
)


# --- Motor de insights ------------------------------------------------------
# Quantos insights o roteirista recebe (top-N do ranqueador). Calibrado pro
# vídeo de ~55s: 5 fatos → hook (1) + ~4 beats → ~6 cenas. Subir aqui ALONGA o
# vídeo (cada fato extra ≈ +9s narrado); descer encurta.
TOP_N_INSIGHTS = 5
# Duração ELÁSTICA orientada por sinal (DESIGN §7): a espinha de CONTRASTE de
# processo carrega o "por quê" (o mecanismo do confronto) → merece o formato
# PROFUNDO (mais corroboradores + teto de palavras maior → ~70-85s, faixa
# monetizável do TikTok). Espinha de convergência/taxa não tem mecanismo a
# desdobrar → fica no enxuto. O tipo da espinha (ranked[0]) escolhe o perfil em
# CÓDIGO (princípio #5) — ver angles.is_deep_spine. NÃO se monetiza vídeo raso.
TOP_N_DEEP = 7
WRITER_WORDS_LEAN = (110, 140)  # enxuto (~55s)
WRITER_WORDS_DEEP = (150, 190)  # profundo (~70-85s)
# Amostra mínima para um fato de TAXA (%) ser considerado válido.
# Fatos binários "duros" (ex.: clean sheet em todos os jogos) passam mesmo abaixo.
MIN_SAMPLE_FOR_RATE = 3

# --- Porta de elegibilidade de MERCADO de aposta (pivot nível B, DESIGN §6) -
# Um fato só CARREGA mercado se passar estas barras. É o que torna o pivot
# defensável: impede que um "4 de 4" frágil vire dica irresponsável.
# Binário/sequência "duro" (ex.: "marcou em todos") pode carregar mercado já com:
MIN_SAMPLE_MARKET_HARD = int(os.getenv("BETSTATS_MIN_SAMPLE_MARKET_HARD", "3"))
# Taxa (%) só carrega mercado com amostra >= isto. Default 3: mercados de taxa
# já acendem desde a fase de grupos (3 jogos), mantendo o lean mínimo de 60%.
MIN_SAMPLE_MARKET_RATE = int(os.getenv("BETSTATS_MIN_SAMPLE_MARKET_RATE", "3"))
# Sinal "forte": distância do 50/50 >= isto (>=80% ou <=20%); senão "moderado".
MARKET_STRONG_PCT = float(os.getenv("BETSTATS_MARKET_STRONG_PCT", "80"))
# Convergência de confronto: cada lado precisa desta taxa pro mercado do jogo
# (over/BTTS) acender. NUNCA vira probabilidade combinada — só as duas taxas.
MARKET_CONVERGENCE_PCT = float(os.getenv("BETSTATS_MARKET_CONVERGENCE_PCT", "60"))

# --- Força de adversário (Elo — DESIGN §6-bis, decisões #14/#15) -------------
# Fonte: World Football Elo (eloratings.net). Usado SÓ INTERNAMENTE pra ponderar
# /gate a família de contraste por qualidade de adversário. NUNCA é um Fact, nunca
# vira mercado, o roteirista nunca o vê. Faixas grosseiras (não número fino) — em
# amostra de 3 jogos, peso contínuo finge precisão que não existe.
ELO_BASE = os.getenv("BETSTATS_ELO_BASE", "https://www.eloratings.net")
# Faixas por rating: forte se Elo >= STRONG; fraco se Elo < WEAK; senão médio.
# Defaults pra seleções (top ~20 ≈ 1900+; cauda < 1700). Tunáveis / calibráveis.
ELO_TIER_STRONG = float(os.getenv("BETSTATS_ELO_TIER_STRONG", "1900"))
ELO_TIER_WEAK = float(os.getenv("BETSTATS_ELO_TIER_WEAK", "1700"))

# --- Família de contraste técnico (DESIGN §6-bis, decisão #13/#16) -----------
# Contraste = ASSIMETRIA (força de um × fraqueza do outro), não dois números altos.
# Roda em métricas de PROCESSO (estáveis em amostra curta). Limiares são defaults
# sensatos — serão FIXADOS pelo mini-backtest do passo 4, não pelo chute.
CONTRAST_MIN_SAMPLE = int(os.getenv("BETSTATS_CONTRAST_MIN_SAMPLE", "3"))
# Finalização: chutes/jogo pra "volume alto" (acende) e pra "forte".
CONTRAST_SHOTS_HIGH = float(os.getenv("BETSTATS_CONTRAST_SHOTS_HIGH", "12"))
CONTRAST_SHOTS_STRONG = float(os.getenv("BETSTATS_CONTRAST_SHOTS_STRONG", "15"))
# Ritmo: % de gols (feitos de um lado, sofridos do outro) no 2º tempo pra acender.
CONTRAST_2H_HIGH = float(os.getenv("BETSTATS_CONTRAST_2H_HIGH", "60"))
# Gate de adversário fraco (Elo): se a fração da amostra contra time 'fraco' for
# >= isto, o sinal cai um nível (forte→moderado, moderado→não acende). Mata a
# miragem da zebra (goleou time fraco → "domínio" que não existe).
CONTRAST_WEAK_FRAC = float(os.getenv("BETSTATS_CONTRAST_WEAK_FRAC", "0.67"))

# Disclaimer obrigatório (garantido pelo código — ver output.py). Sempre presente.
DISCLAIMER = (
    "Conteúdo informativo e estatístico — não é recomendação de aposta. +18. "
    "Aposte com responsabilidade. Estatística passada não garante resultado futuro."
)

# Hashtags — camada de ALCANCE fixa, sempre injetada (vídeo é da Copa). Os times
# e as tags de mercado (do LLM) entram por cima; ver video/publish.py.
BASE_HASHTAGS = ["futebol", "copadomundo", "copa2026", "apostasesportivas"]
MAX_HASHTAGS = 10  # corte final após dedupe (alcance + times primeiro)

# Diretórios
CACHE_DIR = os.getenv("BETSTATS_CACHE_DIR", ".cache")
OUT_DIR = os.getenv("BETSTATS_OUT_DIR", "out")
# Trace por execução (candidatos + ranqueamento + roteiro + metadados).
TRACE_DIR = os.getenv("BETSTATS_TRACE_DIR", "traces")


@dataclass(frozen=True)
class CompetitionConfig:
    """Identificadores de uma competição na API-Football.

    Os IDs são o ponto de partida — confirme na primeira chamada (ver §5 do
    DESIGN.md). A Copa 2026 (league=1, season=2026) veio da documentação da API.
    """

    key: str
    league_id: int
    season: int
    label: str


# Copa do Mundo 2026 — V1.
WORLD_CUP_2026 = CompetitionConfig(
    key="wc2026", league_id=1, season=2026, label="Copa do Mundo 2026"
)

# Brasileirão Série A 2026 — V2 (a partir de 22/jul). league_id=71 a confirmar.
BRASILEIRAO_A_2026 = CompetitionConfig(
    key="brasileirao_a", league_id=71, season=2026, label="Brasileirão Série A 2026"
)

COMPETITIONS = {c.key: c for c in (WORLD_CUP_2026, BRASILEIRAO_A_2026)}
