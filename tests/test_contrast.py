"""Família de contraste técnico de processo (DESIGN §6-bis, passo 3).

Hermético: zera a tabela de Elo (sem rede) e a semeia por teste quando precisa do
gate. Cobre (1) finalização acende na assimetria, (2) não acende sem volume dos
dois lados, (3) o gate de adversário fraco rebaixa/suprime, (4) ritmo no 2ºT.
"""

import unittest

from betstats.data import elo
from betstats.features import engine
from betstats.models import Team, TeamTournamentData
from betstats.rules.world_cup import WorldCupRules

from .builders import by_key, make_match

ALFA = Team(1, "Alfa")
BETA = Team(2, "Beta")
RULES = WorldCupRules()


def _data(team, opp_id, n, **mk):
    ms = [make_match(team_id=team.id, opp_id=opp_id, fid=i, **mk) for i in range(n)]
    return TeamTournamentData(team=team, competition="wc2026", matches=ms)


class TestContrastFinalizacao(unittest.TestCase):
    def setUp(self):
        elo._tables[2026] = {}  # adversários desconhecidos → neutro, sem rede

    def tearDown(self):
        elo._tables.pop(2026, None)

    def test_acende_forte_na_assimetria(self):
        # Alfa finaliza muito (16/jogo); Beta cede muito (16/jogo) → forte.
        da = _data(ALFA, 9, 4, shots_for=16, gf=2, ga=1)
        db = _data(BETA, 8, 4, shots_against=16, gf=1, ga=2)
        f = by_key(engine.confronto(da, db, RULES), "contraste:finalizacao_a")
        self.assertIsNotNone(f)
        self.assertEqual(f.markets, ["Para Alfa marcar"])
        self.assertEqual(f.strength, "forte")
        self.assertIn("nesta Copa", f.text)  # regra de honestidade: amostra no texto

    def test_nao_acende_sem_volume_dos_dois_lados(self):
        # Alfa finaliza muito, mas Beta cede pouco (8/jogo) → sem assimetria real.
        da = _data(ALFA, 9, 4, shots_for=18, gf=2, ga=1)
        db = _data(BETA, 8, 4, shots_against=8, gf=1, ga=2)
        self.assertIsNone(by_key(engine.confronto(da, db, RULES), "contraste:finalizacao_a"))

    def test_amostra_curta_nao_acende(self):
        da = _data(ALFA, 9, 2, shots_for=16, gf=2, ga=1)
        db = _data(BETA, 8, 2, shots_against=16, gf=1, ga=2)
        self.assertIsNone(by_key(engine.confronto(da, db, RULES), "contraste:finalizacao_a"))


class TestContrastEloGate(unittest.TestCase):
    def tearDown(self):
        elo._tables.pop(2026, None)

    def test_gate_rebaixa_forte_para_moderado_contra_fraco(self):
        # Todos os adversários de Alfa (opp_id=9 → "T9") são 'fraco' no Elo.
        elo._tables[2026] = {"t9": (1400.0, 95)}  # < ELO_TIER_WEAK → fraco
        da = _data(ALFA, 9, 4, shots_for=16, gf=2, ga=1)
        db = _data(BETA, 8, 4, shots_against=16, gf=1, ga=2)
        f = by_key(engine.confronto(da, db, RULES), "contraste:finalizacao_a")
        self.assertIsNotNone(f)
        self.assertEqual(f.strength, "moderado")  # forte rebaixado pela miragem da zebra

    def test_gate_nao_pune_amostra_majoritariamente_forte(self):
        # 1 de 4 jogos fraco (<⅔) → não rebaixa.
        elo._tables[2026] = {}
        da = TeamTournamentData(
            team=ALFA, competition="wc2026",
            matches=[
                make_match(team_id=1, opp_id=9, fid=0, shots_for=16, gf=2, ga=1),
                make_match(team_id=1, opp_id=9, fid=1, shots_for=16, gf=2, ga=1),
                make_match(team_id=1, opp_id=9, fid=2, shots_for=16, gf=2, ga=1),
                make_match(team_id=1, opp_id=7, fid=3, shots_for=16, gf=2, ga=1),
            ],
        )
        elo._tables[2026] = {"t7": (1400.0, 95)}  # só 1 dos 4 é fraco
        db = _data(BETA, 8, 4, shots_against=16, gf=1, ga=2)
        f = by_key(engine.confronto(da, db, RULES), "contraste:finalizacao_a")
        self.assertEqual(f.strength, "forte")


class TestContrastRitmo(unittest.TestCase):
    def setUp(self):
        elo._tables[2026] = {}

    def tearDown(self):
        elo._tables.pop(2026, None)

    def test_ritmo_2h_acende(self):
        # Alfa faz 100% dos gols no 2ºT (ht 0, final 2); Beta sofre 100% no 2ºT.
        da = _data(ALFA, 9, 4, gf=2, ga=0, ht_for=0, ht_against=0)
        db = _data(BETA, 8, 4, gf=0, ga=2, ht_for=0, ht_against=0)
        f = by_key(engine.confronto(da, db, RULES), "contraste:ritmo_a")
        self.assertIsNotNone(f)
        self.assertEqual(f.markets, ["Gol no 2º tempo"])


if __name__ == "__main__":
    unittest.main()
