"""Espinha do confronto (coesão estrutural — DESIGN §6-bis, passo 5)."""

import unittest

from betstats.features import angles
from betstats.llm.ranker import _ensure_spine_first
from betstats.models import Fact, RankedFact


def _f(key, strength="", sample=4, markets=("Mercado X",)):
    return Fact(
        text=f"fato {key}", value="x", sample=sample, category=key.split(":")[0],
        kind="taxa", robustness="fragil", team="T", key=key,
        markets=list(markets) if markets else [], strength=strength,
    )


class TestPickSpine(unittest.TestCase):
    def test_contraste_vence_confronto_e_base(self):
        facts = [
            _f("aposta:over25", "forte"),
            _f("confronto:btts", "forte"),
            _f("contraste:finalizacao_a", "moderado"),  # família vence força
        ]
        self.assertEqual(angles.pick_spine(facts).key, "contraste:finalizacao_a")

    def test_desempate_por_forca_depois_amostra(self):
        facts = [
            _f("confronto:over25", "moderado", sample=6),
            _f("confronto:btts", "forte", sample=3),  # forte ganha
        ]
        self.assertEqual(angles.pick_spine(facts).key, "confronto:btts")

    def test_sem_mercado_sem_espinha(self):
        facts = [_f("ataque:gols_total", "", markets=())]
        self.assertIsNone(angles.pick_spine(facts))


class TestEnsureSpineFirst(unittest.TestCase):
    def test_insere_espinha_ausente_no_topo(self):
        spine = _f("contraste:finalizacao_a", "forte")
        facts = [spine, _f("aposta:over25", "forte")]
        ranked = [RankedFact(fact=facts[1], interest=0.9, rationale="r")]  # LLM esqueceu a espinha
        out = _ensure_spine_first(ranked, facts, spine, top_n=5)
        self.assertIs(out[0].fact, spine)
        self.assertEqual(len(out), 2)

    def test_move_espinha_para_o_topo(self):
        spine = _f("contraste:finalizacao_a", "forte")
        other = _f("aposta:over25", "forte")
        facts = [spine, other]
        ranked = [
            RankedFact(fact=other, interest=0.95, rationale="r1"),
            RankedFact(fact=spine, interest=0.5, rationale="r2"),
        ]
        out = _ensure_spine_first(ranked, facts, spine, top_n=5)
        self.assertIs(out[0].fact, spine)  # apesar do interest menor, abre o vídeo
        self.assertIs(out[1].fact, other)

    def test_respeita_top_n(self):
        spine = _f("contraste:finalizacao_a", "forte")
        facts = [spine] + [_f(f"aposta:m{i}", "forte") for i in range(6)]
        ranked = [RankedFact(fact=f, interest=0.9, rationale="r") for f in facts[1:]]
        out = _ensure_spine_first(ranked, facts, spine, top_n=5)
        self.assertEqual(len(out), 5)
        self.assertIs(out[0].fact, spine)


if __name__ == "__main__":
    unittest.main()
