"""Regras do Brasileirão: janela, mando de campo e G6/Z4 (handoff de jul)."""

import unittest

from betstats.models import Team, TeamTournamentData
from betstats.rules.brasileirao import BrasileiraoRules
from tests.builders import by_key, make_match

FLU = Team(1, "Fluminense")


def _m(opp_id, gf, ga, home, fid):
    return make_match(1, opp_id, gf=gf, ga=ga, is_home=home, fid=fid)


class TestWindow(unittest.TestCase):
    def test_window_period_fetch(self):
        rules = BrasileiraoRules(window=5)
        self.assertEqual(rules.period_label(), "nos últimos 5 jogos")
        self.assertEqual(rules.fetch_window(), 5)
        self.assertTrue(rules.has_table())
        data = TeamTournamentData(FLU, "brasileirao_a", [_m(9, 1, 0, True, i) for i in range(8)])
        self.assertEqual(len(rules.window_matches(data)), 5)


class TestMandoEG6Z4(unittest.TestCase):
    def setUp(self):
        # opp -> posição: 2=1º,3=5º,4=3º (G6); 5=18º,6=20º (Z4); 7=10º (meio)
        self.table = {2: 1, 3: 5, 4: 3, 5: 18, 6: 20, 7: 10}
        self.matches = [
            _m(2, 2, 0, True, 1),   # casa, V, vs G6
            _m(3, 0, 1, False, 2),  # fora, D, vs G6
            _m(4, 1, 1, True, 3),   # casa, E, vs G6
            _m(5, 3, 0, True, 4),   # casa, V, vs Z4
            _m(6, 2, 1, False, 5),  # fora, V, vs Z4
            _m(7, 1, 0, False, 6),  # fora, V, meio
        ]
        self.rules = BrasileiraoRules(table_position=self.table)
        self.period = self.rules.period_label()
        self.facts = self.rules.extra_facts(FLU, self.matches, self.period)

    def test_mando_casa_e_fora(self):
        self.assertEqual(by_key(self.facts, "mando:casa").value, "2V 1E 0D (casa)")
        self.assertEqual(by_key(self.facts, "mando:fora").value, "2V 0E 1D (fora)")

    def test_g6(self):
        g6 = by_key(self.facts, "tabela:g6")
        self.assertEqual(g6.value, "1V 1E 1D vs G6")
        self.assertEqual(g6.sample, 3)
        # venceu 1 jogo contra o G6, então NÃO dispara o "sem vitória".
        self.assertIsNone(by_key(self.facts, "tabela:g6_sem_vitoria"))

    def test_z4(self):
        z4 = by_key(self.facts, "tabela:z4")
        self.assertEqual(z4.value, "2/2 vs Z4")  # marcou 5 gols

    def test_honestidade_periodo_em_todos(self):
        for f in self.facts:
            self.assertIn(self.period, f.text)


class TestSemTabelaEsemVitoria(unittest.TestCase):
    def test_sem_tabela_so_mando(self):
        rules = BrasileiraoRules(table_position=None)
        matches = [_m(2, 1, 0, True, 1), _m(3, 0, 0, True, 2)]
        facts = rules.extra_facts(FLU, matches, rules.period_label())
        self.assertIsNotNone(by_key(facts, "mando:casa"))
        self.assertIsNone(by_key(facts, "tabela:g6"))

    def test_g6_sem_vitoria(self):
        rules = BrasileiraoRules(table_position={2: 1, 3: 4})
        matches = [_m(2, 0, 1, True, 1), _m(3, 1, 1, True, 2)]  # D e E vs G6
        facts = rules.extra_facts(FLU, matches, rules.period_label())
        sem = by_key(facts, "tabela:g6_sem_vitoria")
        self.assertEqual(sem.value, "0 vitórias vs G6")


if __name__ == "__main__":
    unittest.main()
