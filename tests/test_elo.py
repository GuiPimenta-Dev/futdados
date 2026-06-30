"""Força de adversário via Elo (uso interno; DESIGN §6-bis).

Hermético: semeia a tabela em memória (sem rede). Testa as faixas, a normalização
PT-BR/inglês com acento, e o None neutro pra time desconhecido.
"""

import unittest

from betstats.data import elo


class TestEloTiers(unittest.TestCase):
    def setUp(self):
        # (elo, rank) por nome normalizado — como _table() produziria.
        elo._tables[2026] = {
            "noruega": (1918.0, 9),
            "norway": (1918.0, 9),
            "costa do marfim": (1743.0, 35),
            "ivory coast": (1743.0, 35),
            "curacao": (1438.0, 91),
        }

    def tearDown(self):
        elo._tables.pop(2026, None)

    def test_tier_bands(self):
        self.assertEqual(elo.tier("Noruega"), elo.STRONG)   # 1918 >= 1900
        self.assertEqual(elo.tier("Costa do Marfim"), elo.MEDIO)  # 1700..1900
        self.assertEqual(elo.tier("Curaçao"), elo.FRACO)    # < 1700

    def test_matches_ptbr_and_english(self):
        self.assertEqual(elo.rating("Norway"), 1918.0)
        self.assertEqual(elo.rating("Noruega"), 1918.0)
        self.assertEqual(elo.rank("Ivory Coast"), 35)

    def test_accent_insensitive(self):
        # "Curaçao" (com cedilha) casa com a chave normalizada "curacao".
        self.assertEqual(elo.tier("Curaçao"), elo.FRACO)

    def test_unknown_is_neutral_none(self):
        # Desconhecido NUNCA é tratado como fraco — retorna None (neutro).
        self.assertIsNone(elo.rating("Time Inexistente"))
        self.assertIsNone(elo.tier("Time Inexistente"))


if __name__ == "__main__":
    unittest.main()
