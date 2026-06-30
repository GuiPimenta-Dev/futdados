"""Ângulo do confronto: a ESPINHA (DESIGN §6-bis, decisão #16 — coesão estrutural).

O problema que isto conserta: o ranker escolhia os top-N fatos melhores INDIVIDUALMENTE
→ uma salada de 5 vencedores soltos, sem uma história. Aqui o código escolhe, de
forma DETERMINÍSTICA, a TESE do jogo (o contraste/mercado mais forte). O ranker passa
a ancorar a seleção nela e o roteirista abre por ela — então o vídeo conta UMA história,
não 5. Coesão vira estrutura de dado, não um pedido no prompt (que é o que falhava).

A espinha é sempre um fato COM MERCADO. Prioridade: contraste de processo > confronto
por convergência > demais mercados; desempate por força e amostra.
"""

from __future__ import annotations

from ..models import Fact

# Prioridade de família (menor = mais forte como tese do jogo).
_FAMILY_RANK = {"contraste": 0, "confronto": 1}
_STRENGTH_RANK = {"forte": 0, "moderado": 1, "": 2}


def _family_priority(f: Fact) -> int:
    return _FAMILY_RANK.get(f.key.split(":", 1)[0], 2)


def _sort_key(f: Fact) -> tuple[int, int, int]:
    # família, força, amostra (negada → maior amostra primeiro).
    return (_family_priority(f), _STRENGTH_RANK.get(f.strength, 2), -f.sample)


def pick_spine(facts: list[Fact]) -> Fact | None:
    """A tese do confronto: o fato COM MERCADO mais forte (contraste > confronto > resto).

    None se nenhum fato carrega mercado (nada acionável pra ancorar)."""
    market_facts = [f for f in facts if f.markets]
    if not market_facts:
        return None
    return min(market_facts, key=_sort_key)


def is_deep_spine(fact: Fact | None) -> bool:
    """A espinha carrega MECANISMO → o vídeo merece o formato PROFUNDO (DESIGN §7).

    Só o contraste de PROCESSO (`contraste:*`, ex.: "A finaliza 17x, B cede 18")
    traz o "por quê" do confronto, que se desdobra em beats de profundidade e
    justifica honestamente os segundos extras (faixa monetizável). Convergência
    (`confronto:*`) e taxa solta não têm mecanismo a abrir → ficam no enxuto.
    Decisão em CÓDIGO (princípio #5): a duração não fica na sorte do LLM."""
    return fact is not None and fact.key.startswith("contraste:")
