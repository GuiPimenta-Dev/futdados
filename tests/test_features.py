"""Cada analista produz os fatos certos a partir de dados conhecidos."""

import unittest

from betstats.features import anomalies, attack, defense, results, temporal
from betstats.models import Team
from tests.builders import by_key, goal, make_match

ALFA = Team(1, "Alfa")
PERIOD = "nesta Copa"


class TestAttack(unittest.TestCase):
    def test_marcou_em_todos_e_goleada(self):
        ms = [make_match(1, 2, gf=3, ga=1, mins_for=(10, 55, 89), mins_against=(33,))]
        facts = attack.analyze(ALFA, ms, PERIOD)
        self.assertEqual(by_key(facts, "ataque:gols_total").value, "3 gols")
        self.assertIsNotNone(by_key(facts, "ataque:marcou_todos"))  # 1/1
        self.assertIsNotNone(by_key(facts, "ataque:maior_goleada"))  # 3-1, diff 2

    def test_nao_marcou_em_todos(self):
        ms = [make_match(fid=1, gf=1), make_match(fid=2, gf=0)]
        facts = attack.analyze(ALFA, ms, PERIOD)
        self.assertIsNone(by_key(facts, "ataque:marcou_todos"))

    def test_conversao(self):
        ms = [make_match(1, 2, gf=2, ga=0, sog_for=8)]
        conv = by_key(attack.analyze(ALFA, ms, PERIOD), "ataque:conversao")
        self.assertEqual(conv.value, "25%")  # 2 gols / 8 chutes no alvo
        self.assertEqual(conv.kind, "taxa")

    def test_sequencia_marcando(self):
        # Branco no 1º jogo, depois marca em 3 seguidos -> corrida parcial de 3.
        ms = [make_match(fid=1, gf=0), make_match(fid=2, gf=1),
              make_match(fid=3, gf=2), make_match(fid=4, gf=1)]
        seq = by_key(attack.analyze(ALFA, ms, PERIOD), "ataque:sequencia_marcando")
        self.assertEqual(seq.value, "3 jogos")

    def test_sem_sequencia_parcial_quando_marcou_em_todos(self):
        ms = [make_match(fid=i, gf=1) for i in range(4)]  # marcou nos 4
        facts = attack.analyze(ALFA, ms, PERIOD)
        self.assertIsNone(by_key(facts, "ataque:sequencia_marcando"))
        self.assertIsNotNone(by_key(facts, "ataque:marcou_todos"))


class TestDefense(unittest.TestCase):
    def test_clean_sheets_e_sequencia(self):
        ms = [make_match(fid=1, gf=1, ga=0), make_match(fid=2, gf=2, ga=0)]
        facts = defense.analyze(ALFA, ms, PERIOD)
        self.assertIsNotNone(by_key(facts, "defesa:clean_sheet_todos"))  # 2/2
        self.assertEqual(by_key(facts, "defesa:gols_sofridos").value, "0 sofridos")
        self.assertEqual(by_key(facts, "defesa:sequencia_sem_sofrer").value, "2 jogos")

    def test_sofreu_gol_quebra_clean_all(self):
        ms = [make_match(fid=1, gf=1, ga=0), make_match(fid=2, gf=1, ga=2)]
        facts = defense.analyze(ALFA, ms, PERIOD)
        self.assertIsNone(by_key(facts, "defesa:clean_sheet_todos"))


class TestTemporal(unittest.TestCase):
    def test_percentual_segundo_tempo(self):
        ms = [
            make_match(fid=1, gf=2, ga=0, ht_for=0, ht_against=0, mins_for=(50, 80)),
            make_match(fid=2, gf=2, ga=0, ht_for=0, ht_against=0, mins_for=(60, 85)),
        ]
        facts = temporal.analyze(ALFA, ms, PERIOD)
        self.assertEqual(by_key(facts, "temporal:gols_por_tempo").value, "100% no 2ºT")

    def test_minuto_primeiro_gol(self):
        ms = [
            make_match(fid=1, gf=1, ga=0, mins_for=(10,)),
            make_match(fid=2, gf=1, ga=0, mins_for=(20,)),
        ]
        facts = temporal.analyze(ALFA, ms, PERIOD)
        self.assertEqual(by_key(facts, "temporal:minuto_primeiro_gol").value, "min 15")


class TestResults(unittest.TestCase):
    def test_campanha_e_um_gol(self):
        ms = [
            make_match(fid=1, gf=2, ga=1),  # V, diff 1
            make_match(fid=2, gf=0, ga=1),  # D, diff 1
            make_match(fid=3, gf=3, ga=3),  # E, diff 0
        ]
        facts = results.analyze(ALFA, ms, PERIOD)
        self.assertEqual(by_key(facts, "resultado:campanha").value, "1V 1E 1D")
        self.assertEqual(by_key(facts, "resultado:um_gol").value, "2/3 por 1 gol")

    def test_viradas(self):
        # Esteve atrás (gol do adversário primeiro) e venceu, em 2 jogos.
        m = lambda fid: make_match(  # noqa: E731
            fid=fid, gf=2, ga=1,
            events=[goal(10, 2), goal(20, 1), goal(80, 1)],
        )
        facts = results.analyze(ALFA, [m(1), m(2)], PERIOD)
        self.assertEqual(by_key(facts, "resultado:viradas").value, "2 viradas/buscas")

    def test_penaltis(self):
        ms = [make_match(fid=1, gf=1, ga=1, pen_for=4, pen_against=2)]
        pen = by_key(results.analyze(ALFA, ms, PERIOD), "resultado:penaltis")
        self.assertEqual(pen.value, "1/1 nos pênaltis")


class TestAnomalies(unittest.TestCase):
    def test_venceu_todos(self):
        ms = [make_match(fid=1, gf=2, ga=0), make_match(fid=2, gf=1, ga=0)]
        self.assertIsNotNone(by_key(anomalies.analyze(ALFA, ms, PERIOD), "anomalia:venceu_todos"))

    def test_invicto_sem_vencer_todos(self):
        ms = [make_match(fid=1, gf=2, ga=0), make_match(fid=2, gf=1, ga=1)]  # V, E
        facts = anomalies.analyze(ALFA, ms, PERIOD)
        self.assertIsNone(by_key(facts, "anomalia:venceu_todos"))
        self.assertIsNotNone(by_key(facts, "anomalia:invicto"))

    def test_tudo_um_gol(self):
        ms = [make_match(fid=1, gf=2, ga=1), make_match(fid=2, gf=0, ga=1)]
        self.assertIsNotNone(by_key(anomalies.analyze(ALFA, ms, PERIOD), "anomalia:tudo_um_gol"))

    def test_vermelhos(self):
        ms = [make_match(fid=1, gf=1, ga=0, reds_for=1), make_match(fid=2, gf=1, ga=0, reds_for=1)]
        red = by_key(anomalies.analyze(ALFA, ms, PERIOD), "anomalia:vermelhos")
        self.assertEqual(red.value, "2 vermelhos")


if __name__ == "__main__":
    unittest.main()
