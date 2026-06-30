"""Invariantes que protegem a marca, rodadas sobre o dataset completo da demo.

A principal: TODO fato carrega o contexto de amostra (o rótulo de período),
que é a regra de honestidade do projeto.
"""

import unittest

from betstats.data.demo import demo_matchup
from betstats.features import engine
from betstats.rules.world_cup import WorldCupRules

CATEGORIES = {"ataque", "defesa", "temporal", "resultado", "anomalia", "aposta"}
KINDS = {"binario", "taxa", "sequencia", "contagem"}


class TestInvariants(unittest.TestCase):
    def setUp(self):
        rules = WorldCupRules()
        data_a, data_b, _, _ = demo_matchup()
        self.period = rules.period_label()
        self.facts = engine.run(data_a, rules) + engine.run(data_b, rules)

    def test_demo_produces_facts(self):
        self.assertGreater(len(self.facts), 10)

    def test_every_fact_embeds_sample_context(self):
        # Regra de honestidade: o período aparece no texto de todo fato.
        for f in self.facts:
            self.assertIn(self.period, f.text, msg=f"sem amostra: {f.text!r}")

    def test_field_domains(self):
        for f in self.facts:
            self.assertIn(f.category, CATEGORIES)
            self.assertIn(f.kind, KINDS)
            self.assertIn(f.robustness, {"dura", "fragil"})
            self.assertGreaterEqual(f.sample, 1)
            self.assertTrue(f.key)
            self.assertTrue(f.value)

    def test_no_predictive_language_in_facts(self):
        # Os fatos descrevem o passado; nada de profecia já na camada de dados.
        banned = ["vai ganhar", "será campeão", "favorito", "deve vencer"]
        for f in self.facts:
            low = f.text.lower()
            for term in banned:
                self.assertNotIn(term, low)


if __name__ == "__main__":
    unittest.main()
