# betstats — Motor de Insights Estatísticos pra Aposta (TikTok)

> Documento de arquitetura. V1 = motor de curiosidades. **Pivot (2026-06-29): de
> curiosidades descritivas → insights estatísticos orientados a aposta, nível B
> (orientado a mercado, SEM profecia).** Idioma do produto: PT-BR.

---

## 1. O que é (e o que NÃO é)

Um motor que **descobre tendências estatísticas verdadeiras** sobre jogos de futebol,
**mapeia cada tendência ao(s) mercado(s) de aposta** que ela ilumina, e transforma isso
num **roteiro de ~1min30 pronto pra narrar no TikTok**.

Posicionamento do canal: *"o perfil que lê os números e mostra o que eles dizem sobre os
mercados — sem prometer resultado"*. O espectador decide a aposta; nós guiamos com
estatística honesta.

**Nível B — orientado a mercado, sem profecia** (escolhido na sessão de grilling de 29/jun):

**É:**
- ✅ Um motor que **conta e valida números** (código determinístico), **anexa o mercado**
  relevante a cada fato (código, determinístico) e **verbaliza com honestidade** (LLM).
- ✅ Fala de **porcentagem, média, taxa e tendência**, sempre com o tamanho de amostra colado.
- ✅ **Nomeia o mercado** ("ambos marcam", "mais de 2,5 gols", "time marca") e **guia** o que
  observar — sem dizer que vai acontecer.

**NÃO é:**
- ❌ Um oráculo que prevê resultados ("vai ganhar", "é favorito", "aposta certa").
- ❌ Uma fonte de probabilidade combinada inventada ("72% de chance de over") — só % que veio
  do engine, jamais um modelo fingido sobre amostra de 3-5 jogos.
- ❌ Uma fonte de odds/cotações (não temos esse dado).

### Princípios que guiam o projeto (não violar)

1. **O LLM só entra no fim.** Calcular, validar e **mapear o mercado** são determinísticos. O
   LLM julga "o que é acionável e prende" e redige — **nunca inventa um número nem um mercado**.
2. **Código conta e mapeia; LLM redige.** Todo número E todo mercado no roteiro veio do engine,
   com fonte rastreável.
3. **Tendência + amostra, sem profecia.** Regra de honestidade inegociável (ver §7).
4. **Amostra é parte da dica.** Um fato só carrega mercado se passar a porta de elegibilidade
   (§6); a amostra anda colada ao mercado, nunca escondida.
5. **Escopo brutalmente enxuto.** A Copa tem relógio correndo; cada decisão otimiza pra
   shippar em dias, não em semanas.

---

## 2. Contexto temporal (por que a V1 é a Copa)

- **Copa do Mundo 2026**: 11/jun–19/jul. Hoje (29/jun) estamos no **mata-mata** — fase mais
  viral. Restam: 32-avos (até 03/jul) → oitavas (04–07) → quartas (09–11) → semis (14–15) →
  final (19/jul).
- **Brasileirão Série A**: **parado** desde 1º/jun, volta **22/jul** (pausa de ~50 dias).
  Não há jogo de clube pra fazer conteúdo até lá.

**Consequência:** as duas realidades **não se sobrepõem no tempo**. Handoff quase poético:
Copa acaba 19/jul → Brasileirão volta 22/jul.

- **V1 (agora):** motor de **fatos da Copa**.
- **V2 (a partir de 22/jul):** trocar a peça e ligar o **Brasileirão** (ver §10).

---

## 3. Decisões travadas

| # | Decisão | Escolha | Por quê |
|---|---------|---------|---------|
| 1 | Posicionamento | **Insight orientado a mercado, sem profecia (nível B)** | Entrega "guiar o que apostar" sem virar oráculo; protege credibilidade com amostra pequena |
| 2 | Unidade do vídeo | **Confronto, nível time** | Gatilho natural (jogos do mata-mata), dado de time é o mais confiável |
| 3 | Sequenciamento | **Copa → Brasileirão (22/jul)** | Calendário força isso; abstração permite o handoff |
| 4 | Fonte de dados | **API-Football** | Uma integração cobre Copa + Brasileirão, com minuto do gol e stats por jogo |
| 5 | Motor | **Determinístico + 2 LLMs** | Os "analistas" viram módulos de código; LLM só ranqueia e escreve |
| 6 | Entregável | **Roteiro ~1min30 + pauta (texto)** | Build em dias; humano controla a qualidade visual |
| 7 | Janela de dados (Copa) | **Só a Copa atual** | Motor de *fatos do torneio*; simplifica a coleta |
| 8 | Regra de honestidade | **Tendência + mercado + amostra, sem profecia** | Permite nomear mercado e falar de %/média; proíbe profecia, probabilidade inventada e odds (§7) |
| 8b | Mapeamento fato→mercado | **No código (determinístico)** | LLM nunca inventa o vínculo; o mercado vira dado rastreável (§6) |
| 8c | Mercado de confronto | **Por convergência, sem modelo** | BTTS/over só acendem quando os DOIS times apontam pro mesmo lado; nada de Poisson/% combinada |
| 8d | Porta de elegibilidade | **Binário duro n≥3; taxa n≥3** | Mercados acendem desde a fase de grupos; o lean mínimo de 60% + a fala de "amostra curta" seguram o risco (tunável por env) |
| 9 | Base de conhecimento | **Princípios no system prompt** (não RAG) | Enxuto; suficiente pra V1 |
| 10 | Notícias | **Adiadas pra V2** | Subsistema à parte; reintroduz risco de alucinação |
| 11 | Stack | **Python** (CLI) | Melhor ecossistema pra dados + LLM; build rápido |
| 12 | Diferença técnica | **Contraste→mercado (mantém #1), nunca "favorito"** | A diferença técnica vira *contraste estatístico que dá lastro a um mercado*, não predição de vencedor (§6-bis) |
| 13 | Métrica de contraste | **Processo (xG, finalização, domínio, ritmo), não placar** | Processo é estável em amostra de 3 jogos; placar regride e gera "muitos erros" |
| 14 | Ajuste de adversário | **Normalizado por força (Elo), em 3 faixas** | Corta a miragem da zebra (xG inflado vs time fraco); faixa grosseira não finge precisão em n=3 |
| 15 | Fonte de força | **World Football Elo (eloratings/clubelo), só interno** | Contínuo, football-específico, com equivalente de clube pro handoff; **nunca é `Fact`** (§6-bis, travas) |
| 16 | Coesão | **Engine pré-monta ÂNGULOS (bundles), não fatos soltos** | Coesão vira estrutura de dado, não pedido no prompt — conserta "dicas não coesas" |
| 17 | Calibração do limiar | **Mini-backtest único sobre `.cache`** | `CONTRAST_GAP_MIN` sai de acerto-de-mercado×força medido, não do chute (§6-bis) |
| 18 | Conselho de subagentes | **NÃO (adiado)** | Custo/latência altos, retorno baixo: delibera sobre números determinísticos que não pode mudar |

**Itens menores (defaults — ajustáveis):**
- **Timing:** pré-jogo (preview do confronto). Pós-jogo é fast-follow (V2).
- **Backend de LLM:** padrão `claude_cli` — usa a **assinatura** via `claude -p` (sem custo de API). Alternativa `api` (SDK + `ANTHROPIC_API_KEY`, Sonnet 4.6; Opus 4.8 pra caprichar). Em ambos o ranqueador seleciona por índice e a saída é validada com Pydantic.
- **Voz:** analista direto e denso em números; cada frase = um número + o mercado que ele abre;
  sem encher linguiça (sem transições decorativas nem hedging repetido).
- **Catálogo de stats:** ~25-35 fatos candidatos + a família **aposta** (over/under, BTTS, taxa de
  marcar/sofrer) + convergência de confronto. `TOP_N_INSIGHTS=6` (mais mercados por roteiro).
- **Disclaimer:** **removido do roteiro/saída** (decisão do usuário, 29/jun). A regra anti-profecia
  /odds/%-combinada continua valendo — é ela que sustenta a credibilidade.
- **Trigger:** CLI manual no MVP; agendar depois.

---

## 4. Arquitetura — pipeline da V1

```
[Trigger]  python run.py --fixture <id>     (ou --next-round lista o mata-mata)
    │
[1] Coletor (API-Football)
    • o jogo + as 2 seleções
    • pra cada seleção: todos os jogos DELA na Copa 2026 + eventos (gols c/ minuto) + stats por jogo
    • cache local em JSON (economiza rate limit)
    │
[2] Feature Engineering   ← os "analistas" são módulos de código (§6)
    • ataque · defesa · temporal · resultado/forma · anomalias
    → N fatos candidatos: { texto, valor, amostra, categoria, tipo, robustez }
    │
[3] Pré-filtro de validade (código)
    • corta amostra < mínimo · marca sample_size · dedup de redundantes
    │
[4] LLM #1 — Editor de pauta (ranqueador)
    • candidatos válidos dos 2 times + critérios de "interessância" (§6)
    → top-5 ranqueados, com justificativa (JSON)
    │
[5] LLM #2 — Roteirista
    • top-5 + regra de honestidade (§7) + persona PT-BR
    → roteiro ~1min30 (gancho → fatos → fecho/CTA) + título + legenda + hashtags
    │
[Saída]  arquivo .md pronto pra narrar  +  os fatos-fonte com números pra conferir
```

---

## 5. Camada de dados (ESPN grátis · API-Football fallback)

A `DataProvider` isola a fonte. Há **duas implementações**, escolhidas por
`BETSTATS_PROVIDER` (default `espn`):

### Primária (MVP): **ESPN** — API pública gratuita (`data/espn.py`)

> Decidida em 29/jun após pesquisa + validação por chamadas reais. Cobre a Copa 2026
> com a **mesma profundidade** da API-Football, **sem chave e sem custo**: fixtures,
> **minuto dos gols** (gol-contra/pênalti via `keyEvents[].type.text`), **placar do 1º
> tempo** (`linescores[0]`), **disputa de pênaltis** (`shootoutScore`), **estatísticas
> por jogo** (`boxscore` → chutes/posse/escanteios/faltas/cartões) e **tabela de grupos**.

- **Endpoints:** `.../soccer/fifa.world/scoreboard?dates=<season>` (lista os 104 jogos),
  `.../summary?event=<id>` (placar, HT, eventos, stats), `apis/v2/.../standings`.
- **Slug de liga:** Copa = `fifa.world`; Brasileirão = `bra.1`.
- **Sem chave, sem rate limit publicado.** Como o motor só usa jogos **encerrados**
  (dados pré-jogo), o **cache em disco é permanente** — uma quebra de schema da ESPN vira
  conserto de parsing, não perda de dado, e não dependemos de uptime durante a partida.
- ⚠️ **Não-oficial:** sem ToS pública nem garantia de estabilidade. Aceitável pro MVP com
  parsing defensivo; migre pra `api_football` quando precisar de fonte contratual.
- **Validado:** Final 2022 (Argentina x França, event `633850`) gera o catálogo completo,
  inclusive os fatos que dependem de stats e de minuto do gol.

### Fallback robusto: **API-Football** (`data/api_football.py`, `BETSTATS_PROVIDER=api_football`)

> **CONFIRMADO em runtime:** o plano **FREE não cobre a season 2026** (só 2022–2024) e
> limita **~10 req/min**. Para a Copa 2026 é preciso plano pago (~€19/mês). Fonte com
> contrato/SLA — ligar quando o projeto for comercial. Endpoints: `fixtures`,
> `fixtures/events`, `fixtures/statistics`, `standings`, `teams`.

**Cuidado comum:** **cache agressivo** em JSON; puxar dados **pós-jogo** (números finais).
**Atenção:** os IDs de jogo/seleção **diferem entre provedores** (ESPN ≠ API-Football).

---

## 6. Feature Engineering + Ranqueamento

### Os "analistas" = módulos de código (não agentes de IA)

Cada módulo recebe os jogos da seleção na Copa e emite **fatos candidatos**. Cada fato:

```json
{
  "texto": "marcou em todos os jogos da Copa",
  "valor": "4/4",
  "amostra": 4,
  "categoria": "ataque",
  "tipo": "binario | taxa | sequencia | contagem",
  "robustez": "dura | fragil",
  "markets": ["Para o time marcar"],
  "strength": "forte | moderado | \"\" (sem mercado)"
}
```

**Famílias (catálogo, ~25-35 candidatos + família de aposta):**

| Família | Exemplos de fato |
|---------|------------------|
| **Ataque** | total/média de gols · jogos marcando · chutes e chutes no alvo/jogo · conversão · maior goleada |
| **Defesa** | gols sofridos · clean sheets · chutes sofridos/jogo · sequência sem sofrer |
| **Temporal** | % gols 1º vs 2º tempo (feitos/sofridos) · minuto do 1º gol · gols nos minutos finais (75'+) |
| **Resultado/forma** | V-E-D · saldo · jogos decididos por 1 gol · viradas · resultado quando marca primeiro · pênaltis |
| **Anomalias/sequências** | qualquer 100%/0% · sequências perfeitas · ganhou com menos posse · disciplina extrema |
| **Aposta** (`features/betting.py`) | **% jogos com over 2,5 gols** · **% jogos com BTTS (ambos marcam)** · **taxa de marcar** · **taxa de sofrer** — as taxas que os mercados pedem, na faixa 60-90% (não só no extremo) |
| **Confronto** (`engine.confronto`) | mercados do jogo por **convergência**: over/BTTS/time-marca só acendem quando os DOIS times apontam pro mesmo lado |

### Mapeamento fato → mercado (código — `features/markets.py`)

Determinístico. `attach_markets(facts)` olha `key`/`kind`/`sample`/`valor` e anexa `markets` +
`strength`. O LLM **só lê** o mercado; nunca o inventa.

**Porta de elegibilidade (Decisão #8d — o que torna o pivot defensável):**
- **Binário/sequência "duro"** (ex.: "marcou em todos") carrega mercado com **n≥3**
  (`MIN_SAMPLE_MARKET_HARD`); força `forte` se n≥4, senão `moderado`.
- **Taxa (%)** só carrega mercado com **n≥3** (`MIN_SAMPLE_MARKET_RATE`, tunável por env) e
  denominador explícito; força `forte` quando o sinal é extremo (≥80% ou ≤20%, `MARKET_STRONG_PCT`),
  senão `moderado`. Além disso, a taxa precisa de um LADO claro (lean ≥60%); abaixo disso é
  cara-ou-coroa e não vira mercado.
- **Convergência de confronto**: cada lado precisa de **n≥3 e taxa ≥60%** (`MARKET_CONVERGENCE_PCT`)
  pro mercado do jogo (over/BTTS) acender. Nunca cospe probabilidade combinada — só relata as duas
  taxas lado a lado.
- Consequência: mercados de taxa acendem **desde a fase de grupos** (3 jogos). O risco de amostra
  curta é segurado por (a) o lean mínimo de 60%, (b) o rótulo de força e (c) o roteirista verbalizar
  "tendência em só N jogos". Subir `MIN_SAMPLE_MARKET_RATE` torna o motor mais conservador.

### Pré-filtro de validade (código, antes do LLM)

- **Fato "duro" binário** (ex.: "clean sheet em todos os jogos") é válido mesmo com n=3.
- **Taxa** (ex.: "80% dos gols no 2º tempo") só passa com o denominador explícito e amostra mínima.
- **Dedup** de fatos redundantes; cada fato carrega `sample_size`.

### LLM #1 — ranqueamento: "sinal acionável que prende" (Decisão #4 do pivot)

O ranker agora otimiza **utilidade pra aposta sem perder retenção**:
- **Exige mercado:** fato **com `markets`** tem prioridade; fato sem mercado entra no máximo como
  tempero (≤1 no top-5).
- **Força do sinal + robustez:** taxa extrema + amostra que sustenta > coincidência frágil.
- **Diversidade de mercado:** os escolhidos cobrem **mercados diferentes** (não 5 variações de
  "time marca"); se houver um **mercado de confronto** (convergência), priorizar entrá-lo.
- **Retenção/contraste:** critério de ordenação e desempate — o conjunto ainda tem que dar vontade
  de assistir até o fim (é TikTok).
- Saída: top-5 em JSON estruturado, com 1 linha de justificativa por fato.

---

## 6-bis. Contraste técnico + ângulos (pivot de 30/jun — foco Copa)

**Problema diagnosticado (trace `costa-do-marfim-x-noruega`):** o conteúdo soa genérico e "gera
muitos erros" por dois motivos a montante do ranker — (1) **amostra = 3** (todo sinal é uma taxa de
3 jogos que regride: "100%" = "3 de 3"); (2) **fatos mono-temáticos de resultado** (5 variações de
"festival de gols", sem contraste técnico e sem *uma* história). O ranker é raso **por design**
(#5: código conta, LLM redige) — o conserto mora no **engine**, não num conselho de subagentes (#18).

### A família de contraste (evolução de `engine.confronto`)
Hoje `confronto` faz contraste de **resultado** por convergência (#8c) — ruidoso em 3 jogos. A
evolução tem três regras:

1. **Contraste = assimetria, não dois números altos.** Só acende quando a **força de um time
   encontra a fraqueza específica do outro** na mesma dimensão. "Os dois marcam muito" é
   coincidência; "A finaliza 17x/jogo **e** B é quem mais cede finalização" é a diferença técnica
   do confronto. Exige um **gap mínimo** (`CONTRAST_GAP_MIN`, calibrado — ver abaixo).
2. **Processo > resultado** (#13). Dimensões estáveis em amostra curta, cada uma → mercado:

   | Dimensão | Lado A (ataca) | Lado B (cede) | Mercado | Fonte |
   |---|---|---|---|---|
   | **Finalização** | chutes + on-target/jogo | finalizações sofridas/jogo | over / escanteios / A marca | ESPN (hoje) |
   | **Conversão** (`shotPct`) | qualidade de finalização | — | over / A marca | ESPN (hoje) |
   | **Domínio** | posse + escanteios | território cedido | escanteios / pressão | ESPN (hoje) |
   | **Ritmo** | % gols 2ºT | % gols sofridos 2ºT | gol no 2º tempo | ESPN (hoje) |
   | **xG** (premium) | xG criado/jogo | xG concedido/jogo | over / A marca | **API-Football (a verificar)** |
   | **xG vs real** | criou 2.1, fez 0.9 | — | over "atrasado" / A marca | **API-Football (a verificar)** |

   ⚠️ **Correção (30/jun):** o **ESPN não fornece xG de time** (só xG por jogador-líder, não somável;
   sem `boxscore.players`). A espinha de processo roda **hoje em finalização/conversão/posse**, que
   o boxscore do ESPN dá team-level. **xG-de-verdade depende do API-Football** (`/fixtures/statistics`,
   `expected_goals`) — cobertura da WC2026 **a confirmar com 1 chamada live**. Campos `xg`/`xga`
   entram como `float | None` (placeholder); a família degrada pra finalização quando faltarem.

3. **Encoda direção + magnitude** pro roteirista dizer *"um domina, o outro vaza"* — **sem nunca
   dizer "favorito"**. Continua relatando os dois números lado a lado, nunca probabilidade combinada.

### Normalização por adversário (Elo — #14, #15)
xG e finalização inflam contra time fraco. **World Football Elo** (`eloratings`; `clubelo` no
handoff) entra em **3 faixas** (forte/médio/fraco) pra ponderar/gate cada jogo no cálculo do
contraste. **Travas não-negociáveis:**
- **O Elo nunca é um `Fact`.** Entra *só* dentro de `engine.confronto`/`markets`: pondera o jogo e
  rebaixa `strength`. Não é emitido, não mapeia mercado, **o writer nunca o vê** → "favorito" é
  *estruturalmente* impossível de vazar, não só proibido por prompt.
- **Gate, não tempero:** se ≥⅔ da amostra de um contraste vier de adversário "fraco", o contraste
  não acende (ou acende "moderado"). É isso que mata o erro grosseiro da zebra.

### Ângulos = espinha + seleção ancorada (coesão estrutural — #16) ✅
Implementado como **ESPINHA determinística** (`features/angles.py`): o código escolhe a TESE do jogo
— o fato com mercado mais forte, prioridade contraste > confronto > resto, desempate por força e
amostra. O ranker (#4, opção (a)) recebe a espinha apontada e **ancora a seleção nela** (mercados
distintos que conversam com a tese), e `_ensure_spine_first` **garante em código** que a espinha
entra e abre o vídeo — coesão não fica na sorte do LLM. O roteirista abre pela espinha (fato [0]) e
amarra o resto nela. Como `video/props` já usa `ranked[0]` no frame de abertura, o número-choque do
hook passa a ser, automaticamente, o contraste mais forte. (O *pré-agrupamento* dos corroboradores
num struct foi dispensado: a seleção ancorada do ranker já entrega a coesão sem código morto.)

### Calibração do limiar (mini-backtest — #17)
`CONTRAST_GAP_MIN` **não é chutado**. Um script descartável (`scripts/calibrate.py`) faz replay dos
jogos já disputados no `.cache` (computando o sinal só com jogos *anteriores* a cada partida) e mede
**acerto-de-mercado por faixa de força** (não "acertou o vencedor"). "forte" tem que bater bem acima
de moeda-ao-ar, senão o limiar sobe. Calibração única, não infra contínua.

### Ordem de build (relógio da Copa)
1. **Métricas de processo no pipeline** — capturar `shotPct`/`blockedShots` (já no boxscore do ESPN)
   em `TeamMatchStats` + adicionar `xg`/`xga` como `float | None` (placeholder p/ API-Football). A
   família roda em finalização/conversão/posse hoje; xG é upgrade condicionado à verificação.
2. **`data/elo.py`** + faixas (isolado). ✅
3. **`engine.confronto`** → contraste de PROCESSO (finalização + ritmo 2ºT) + gate Elo
   (`_weak_fraction` = fraco/total; ≥⅔ → rebaixa forte→moderado, moderado→não acende). ✅
   Conversão/domínio + xG ficam de enriquecimento; **o bundle de ÂNGULO desce pro passo 5**,
   junto do seu consumidor (ranker/writer) — emitir estrutura sem quem consome é código morto.
4. **`scripts/calibrate.py`** → fixa os limiares de contraste (`CONTRAST_SHOTS_*`, etc.) e valida
   força por acerto-de-mercado — **antes de publicar**.
5. **ranker + writer** ajustados pra ângulos: espinha determinística (`angles.py`) + ranker ancora
   nela (`_ensure_spine_first` garante topo) + writer abre por ela. ✅
6. Gerar 2-3 vídeos das oitavas, comparar com o trace antigo, ajustar.

### Métrica de sucesso
- **Acerto-de-mercado por faixa** no backtest acima de moeda-ao-ar (senão sobe o limiar).
- Qualitativo: o vídeo soa como **análise** ("A domina e cria, B vaza → over e A-marcar com lastro
  de processo"), não 5 stats soltas de 3 jogos.

### NÃO fazer agora (fica pro Brasileirão, onde amostra e paridade são maiores)
Conselho deliberativo de subagentes (#18); Elo/ranking no roteiro; janela estendida/eliminatórias;
normalização contínua fina.

---

## 7. Roteirista (LLM #2) — regras

**Regra de honestidade (LEI — nível B, reescrita no pivot de 29/jun):**

- **Sempre embutir a amostra:** *"nos 4 jogos desta Copa..."*. A amostra é parte da dica, não
  letra miúda — e a **força** do sinal (`forte`/`moderado`) é dita junto ("tendência forte, mas em
  só 4 jogos").
- **PERMITIDO** (descreve tendência/mercado ancorado em amostra):
  - ✅ "marcou em 100% dos 4 jogos → time marca" · "acende o mercado de 'ambos marcam'" ·
    "os números favorecem o mercado X" · "até aqui", "nesta Copa", "no torneio".
- **PROIBIDO** (profecia / falso rigor):
  - ❌ profecia: "vai marcar", "é favorito", "ganha fácil", "aposta certa", "garantido".
  - ❌ probabilidade **combinada inventada** ("72% de chance de over") — só % que veio do engine.
  - ❌ **odds/cotações** (não temos o dado; inventar é alucinação).
- **Nunca** usar um número OU um mercado que não veio do engine. Sem número/mercado → sem afirmação.

**Estilo — "enxuto com calor" (régua travada em 29/jun, sessão de tom):**
- **Regra-mãe:** toda frase carrega **um número OU nomeia um mercado**. Conector vazio ("e não para
  por aí", "agora liga nesse detalhe", "tem mais lenha pra essa fogueira") é PROIBIDO — é tempo de
  tela sem informação. O gancho nunca repete o fato do beat 1.
- **Número → mercado:** o mercado é o **sujeito da frase**, construção SEMPRE variada e direta
  ("acende o gol no 2º tempo", "'Brasil marca' tem lastro"). Nunca "mercado: X" como etiqueta. A
  fórmula em 2ª pessoa ("quem curte um over…") entra **no máximo 1×/vídeo** — é tempero, não padrão.
- **Onde mora o calor:** **verbos vivos** ("a Croácia tranca", "a rede balança") + **1 linha de
  contraste** afiado por vídeo (ataque-de-um × defesa-do-outro). Personalidade sem gastar segundo.
- **Cobrir 4-5 mercados distintos e fortes** — qualidade acima de volume; não entupir com stat banal
  só pra encher. Quem assiste sai com uma lista enxuta e confiável de mercados. (No enxuto o ranker
  entrega `TOP_N_INSIGHTS=5` fatos; cada fato extra ≈ +9s de vídeo narrado.)
- **Força do sinal dita junto, em 1-2 palavras** (LEI): "forte" → tom de confiança; "moderado" →
  uma palavra de cautela ("tendência leve"). Proibido frase-disclaimer ("trato como inclinação, não
  certeza").

**Duração ELÁSTICA orientada por sinal (decisão de 30/jun — substitui o ~55s fixo):**
A duração não é fixa: ela é escolhida **em código** (princípio #5) pelo **tipo da espinha** (`ranked[0]`),
via `angles.is_deep_spine`. Não se monetiza vídeo raso — só os jogos com contraste técnico real ganham
o formato longo (faixa monetizável do TikTok, >1min); jogos magros ficam curtos e crescem por retenção.

| Formato | Gatilho (espinha) | `TOP_N` | Palavras | Duração | Monetiza |
|---|---|---|---|---|---|
| **ENXUTO** | `confronto:*` / taxa solta (sem mecanismo a abrir) | `TOP_N_INSIGHTS=5` | `WRITER_WORDS_LEAN` (110-140) | ~55s | não |
| **PROFUNDO** | `contraste:*` de processo (carrega o "por quê") | `TOP_N_DEEP=7` | `WRITER_WORDS_DEEP` (150-190) | ~70-85s | sim |

**Estrutura:**
1. **Gancho** (0-3s, igual nos dois): o **número-choque primeiro**, seco, zero aquecimento — o dado
   mais extremo é a primeira coisa dita; contexto e mercado vêm logo depois.
2. **Corpo:**
   - ENXUTO: 3-4 beats (nunca mais que 4), um por estatística+mercado, do sinal mais forte ao mais fraco.
   - PROFUNDO: a espinha de contraste é **desdobrada em 2 beats** (lado que ataca × lado que cede, cada
     um com SEU número) + 2-3 corroboradores → até ~6 beats. A profundidade vem de **abrir a tese**, não
     de raspar mais mercado fraco. Trava: só cita números que já estão no texto do fato-espinha.
3. **Fecho/CTA**: UMA frase — amarra 2-3 mercados acesos **+ pergunta ANCORADA na tensão do jogo**
   (dilema A-ou-B derivado da espinha; nunca o "Qual você pega?" fixo). Força o espectador a escolher um
   lado → debate → comentário, o sinal de algoritmo mais forte do TikTok.
4. Entrega também: **título**, **legenda** (listando os mercados) e **hashtags**.

**Tom:** analista que manja, denso em número mas vivo — "enxuto com calor"; PT-BR; sem
sensacionalismo, sem empolgação de influencer, sem achismo.

**Disclaimer:** **fora do roteiro e da saída** (decisão do usuário, 29/jun). A LEI anti-profecia
acima permanece — é ela, não o disclaimer, que protege a credibilidade.

**Saída (arquivo .md por confronto):**
- Cabeçalho (jogo, fase, data) + seção "Mercados iluminados".
- Os fatos-fonte com números, amostra, **mercado e força** (pra você conferir).
- O roteiro com marcação de beats/tempo.
- Título + legenda + hashtags.

---

## 7-bis. Camada de vídeo + empacotamento (deliverable real)

O entregável final **não é mais o .md** — é um **vídeo 9:16 + thumbnail + texto de publicação**,
empacotados por jogo. O `.md` (roteiro) vira referência dentro da pasta. Tudo orquestrado por
`run.py --video` (decisões travadas nas sessões de 29/jun).

**Pipeline do vídeo** (`src/betstats/video/`):
1. **`tts.py`** — `ScriptOutput` (hook+beats+cta) → narração única → ElevenLabs `convert_with_timestamps`
   → mp3 + **timing por palavra** (voz Daniel, PT-BR, `apply_text_normalization=on`, speed 1.06).
2. **`props.py`** — fatia as palavras por segmento, monta blocos de legenda (~4 palavras), liga cada
   beat ao seu `Fact` (via **`ScriptOutput.beat_facts`** → card de número/mercado/força), injeta SFX
   sintéticos (`sfx.py`) e escreve **`props.json`** (determinístico) em `out/.work/<slug>/`.
3. **Remotion** (`video/`, React) — consome `props.json`:
   - `Background` (verde brandado), `Crests` (escudos via URL do provider, fallback inicial),
     `StatCard` (card por beat + **slam no gancho**), `Captions` (bloco com palavra ativa acesa),
     `Branding` (selo fonte+amostra + **logo FutDados**). Composição `BetVideo` (vídeo) e `Thumbnail` (still).
   - Render config: **png + yuv420p** (compatibilidade universal — NÃO usar jpeg/yuvj).
4. **`run.py`** orquestra: render `BetVideo` → **`loudnorm`** (ffmpeg, I=-14 LUFS, TP=-1.5, 48kHz
   estéreo, faststart) → render still `Thumbnail` → empacota.

**Tom calibrado pro vídeo:** duração **elástica** pelo tipo de espinha (ver §7) — enxuto (`TOP_N_INSIGHTS=5`
→ hook + ~4 beats + cta, ~55s) ou profundo (`TOP_N_DEEP=7` → hook + espinha desdobrada + corroboradores,
~70-85s monetizável). A fala **alonga os números** ("100%"→"cem por cento"), por isso o alvo de
palavras-escritas é 110-140 (enxuto) / 150-190 (profundo).

**Marca (FutDados):** a logo fonte (`logo.png`, fundo preto) é convertida pra **transparente** por
luminance-key do ffmpeg (`publish.ensure_brand` → `video/public/logo.png`); usada como watermark no
vídeo e na thumbnail. Áudio/SFX são **sintéticos** (`sfx.py`, stdlib) — zero licença; trocar `bed.wav`
por trilha real é só substituir o arquivo.

**Empacotamento** (`publish.py` → `package_match`): cada jogo vira a pasta
`out/<Time A x Time B>/` com:
- `video.mp4` · `thumbnail.png` · `publicacao.txt` (legenda + hashtags, pronto pra colar) · `roteiro.md` (referência).
- Hashtags = **base de alcance fixa** (`config.BASE_HASHTAGS`) + **times derivados** (sem acento) +
  **tags de mercado do LLM** → dedupe, corte em `MAX_HASHTAGS`.
- Frase-soco da thumbnail = campo **`thumb_hook`** do roteirista.
- Intermediários (props.json, mp3, raw) ficam em `out/.work/<slug>/`.

---

## 8. Plano de build (sprint)

- [ ] **Passo 0 — Destravar dados.** Criar API key; validar cobertura da Copa 2026 (1 request de `fixtures`).
- [ ] **Passo 1 — Coletor.** `DataProvider` (impl. API-Football): fixtures + jogos da seleção + eventos + stats. Cache JSON. Testar com 1 jogo real.
- [ ] **Passo 2 — Feature engineering.** Módulos por família → candidatos. Imprimir candidatos de uma seleção.
- [ ] **Passo 3 — Pré-filtro + dedup.**
- [ ] **Passo 4 — LLM #1 (ranker).** Prompt + JSON schema dos critérios.
- [ ] **Passo 5 — LLM #2 (roteirista).** Prompt + regra de honestidade + persona.
- [ ] **Passo 6 — Glue CLI + saída .md.** Rodar ponta-a-ponta num confronto real do mata-mata.
- [ ] **Passo 7 — Iterar qualidade.** Ajustar critérios/voz com base em saídas reais.

---

## 9. Riscos & mitigações

| Risco | Mitigação |
|-------|-----------|
| Amostra minúscula no início do mata-mata → roteiro magro | Aceitar fatos binários "duros"; volume melhora nas fases finais |
| ESPN (não-oficial) quebrar schema/sair do ar | Cache permanente de jogos encerrados; parsing defensivo; fallback API-Football (`BETSTATS_PROVIDER`) |
| Dado parcial em jogo ao vivo | Só usamos jogos encerrados (dados pré-jogo) |
| Ranker subjetivo | Iterar critérios com exemplos reais |
| Relógio da Copa | Escopo enxuto; nada de feature nova até o ponta-a-ponta rodar |

---

## 10. Abstração para o handoff (22/jul → Brasileirão)

O que muda do WC pro Brasileirão deve ficar isolado em **duas peças**:

- **`DataProvider` (interface):** `get_fixtures`, `get_team_matches`, `get_match_events`,
  `get_match_statistics`, `get_standings`. A mesma impl. API-Football serve os dois.
- **`LeagueRules` (estratégia por competição):**

  | | Copa 2026 | Brasileirão A |
  |--|-----------|----------------|
  | Janela | todos os jogos do torneio | últimos N jogos (ex.: 10) |
  | Modo | mata-mata | liga |
  | Tabela (G6/Z4) | não | **sim** (liga novas famílias de fato) |
  | Nomenclatura | "nesta Copa" | "nesta edição do Brasileirão" / "nos últimos 10 jogos" |

Feature engineering e os 2 LLMs ficam **iguais**; muda só de onde vêm os jogos e quais
famílias extra (tabela, G6/Z4, casa/fora) ligam.

**Pivot de aposta no handoff:** o mapeamento de mercado (`features/markets.py`) e a família de
aposta (`features/betting.py`) são **agnósticos de competição** — o Brasileirão herda os mercados
de graça. O que NÃO sai no pivot agora (foco = Copa): recorte **casa/fora dos mercados** (taxa de
BTTS/over em casa vs. fora), altíssimo valor pro apostador de liga. Fica no backlog pra antes de
22/jul (ver §11).

**Status: implementado.** `BrasileiraoRules` está completa (janela últimos-N, mando de
campo, G6/Z4 via `get_standings`), com `extra_facts` no motor e o flag `--comp brasileirao`
no CLI. As regras têm testes; a liga (71), a cobertura e o parsing da tabela foram
validados no Brasileirão **2023** (plano grátis). Em 22/jul, é só rodar sem `--season`
(exige plano pago da API para a temporada 2026). Pra testar de graça agora:
`python run.py --comp brasileirao --season 2023 --list`.

---

## 11. Backlog (V2+)

- **Recorte casa/fora dos mercados de aposta** (BTTS/over/taxa de marcar em casa vs. fora) — alto
  valor no Brasileirão; ligar antes de 22/jul, usando o mando que `BrasileiraoRules` já carrega.
- **Jogador-level** (artilheiro em sequência, goleiro sem sofrer há X min) — exige dado de evento por jogador.
- **Notícias** (gancho editorial, lesão/escalação) — manual primeiro, depois automático.
- **xG** — empilhar/trocar fonte (SportMonks, iSports) se fizer falta.
- **Histórico / H2H em Copas** — se reabrir a decisão "só a Copa atual".
- **TTS** (ElevenLabs PT-BR) → remove a gravação.
- **Vídeo automático** (template com números na tela + b-roll) — projeto maior.
- **Pós-jogo** (reação aos números) · **perfil de seleção** (single-team).
- **Agendamento** (jogos do dia → dispara) · **multi-liga**.

---

## 12. Ações pendentes do usuário

1. ~~Criar conta + API key na API-Football~~ — **não bloqueia mais o MVP.** A fonte
   primária é a **ESPN gratuita** (sem chave). A API-Football vira fallback pago: só criar
   conta se/quando precisar de fonte com contrato (`BETSTATS_PROVIDER=api_football`).
2. **Validar a ESPN ao vivo na Copa 2026** quando o torneio começar (rodar `--list` sem
   `--season`; confirmar slug `fifa.world` e a profundidade dos dados de 2026).
3. *(Opcional)* Definir nome/identidade do canal.
