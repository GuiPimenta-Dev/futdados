# betstats

Motor de **insights estatísticos orientados a aposta** de futebol que gera **roteiro + pauta** para vídeos de TikTok. V1: **Copa do Mundo 2026**. Posicionamento: **nível B — orientado a mercado, sem profecia** (nomeia o mercado e a tendência; nunca promete resultado). A arquitetura completa e as decisões estão em [`DESIGN.md`](./DESIGN.md).

> Código conta os números **e mapeia o mercado** (determinístico); o LLM julga o que é acionável e escreve. Número e mercado nunca são alucinados — e cada fato só vira dica se passar a porta de amostra.

## Pipeline

```
Coletor (API-Football) → Feature engineering (analistas) → Validação
   → LLM #1 ranqueador → LLM #2 roteirista → roteiro.md
```

## Setup

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # preencha APISPORTS_KEY e ANTHROPIC_API_KEY
```

- **APISPORTS_KEY** — conta gratuita em https://www.api-football.com/ (valide a cobertura da Copa 2026 no free tier).
- **LLM (ranqueador + roteirista):** por padrão usa sua **assinatura** via `claude -p` (`BETSTATS_LLM_BACKEND=claude_cli`) — basta ter o Claude Code instalado e logado; **não precisa de API key**. Para usar a API cobrada, defina `BETSTATS_LLM_BACKEND=api` e preencha `ANTHROPIC_API_KEY`.

## Uso

```bash
# Roda no dataset sintético — funciona OFFLINE, sem nenhuma key.
# Com ANTHROPIC_API_KEY no .env, gera o roteiro completo; sem, mostra os candidatos.
python run.py --demo

# Só os fatos candidatos (sem LLM), em qualquer modo:
python run.py --demo --no-llm

# Jogos reais da Copa (precisa de APISPORTS_KEY):
python run.py --list           # lista os jogos e seus IDs
python run.py --next-round     # só os que ainda não foram disputados
python run.py --fixture 12345  # gera roteiro+pauta para o confronto
```

A saída `.md` vai para `out/`.

## Estrutura

```
src/betstats/
  config.py            # env, modelos de LLM, IDs de competição
  models.py            # contratos de dados normalizados
  data/                # DataProvider (API-Football) + cache + demo offline
  rules/               # LeagueRules: Copa (V1) e Brasileirão (V2, esqueleto)
  features/            # os "analistas" (ataque, defesa, temporal, resultado, anomalias)
  validate.py          # pré-filtro de amostra + dedup
  llm/                 # ranqueador (#1) e roteirista (#2)
  output.py            # render do .md
  pipeline.py          # orquestração ponta a ponta
run.py                 # CLI
```

## Testes

Rodam sem nenhuma dependência (stdlib `unittest`), igual ao núcleo do motor:

```bash
python3 -m unittest discover -s tests -t .
```

Cobrem os helpers de `Match`, cada analista, a validação/dedup e a invariante
de honestidade (todo fato carrega o contexto de amostra).

## Handoff para o Brasileirão (22/jul)

A fonte de dados (`DataProvider`) e as regras de liga (`LeagueRules`) são as únicas peças que mudam — e já estão **implementadas**. `rules/brasileirao.py` faz: janela = últimos N jogos, **mando de campo** (casa/fora) e **G6/Z4** (via `get_standings`). Feature engineering e LLMs ficam iguais.

```bash
# Em 22/jul (exige plano pago p/ a temporada 2026):
python run.py --comp brasileirao --fixture <ID>

# Testar de graça agora, no Brasileirão 2023 (plano grátis cobre):
python run.py --comp brasileirao --season 2023 --list
python run.py --comp brasileirao --season 2023 --fixture 1005658
```

## Backend de LLM

Dois caminhos, escolhidos por `BETSTATS_LLM_BACKEND`:

- **`claude_cli`** (padrão) — usa sua assinatura via `claude -p`. Sem custo de API, sem key. O modelo é o padrão da assinatura (ou `BETSTATS_CLAUDE_MODEL`). O subprocesso roda sem `ANTHROPIC_API_KEY` no ambiente, para garantir auth por assinatura.
- **`api`** — SDK Anthropic com `ANTHROPIC_API_KEY` (cobrado). Usa `messages.parse()` com schema. Padrão `claude-sonnet-4-6`; para caprichar no texto: `export BETSTATS_WRITER_MODEL=claude-opus-4-8`.

Em ambos, o ranqueador escolhe fatos por índice e o roteirista valida via Pydantic — o número nunca é reescrito pelo LLM.
# futdados
