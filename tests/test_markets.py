"""Pivot nível B: família de aposta, mapeamento fato->mercado e convergência.

Protege a PORTA DE ELEGIBILIDADE (DESIGN #8d): é ela que impede um "4 de 4"
frágil de virar dica de aposta.
"""

import unittest

from betstats import config
from betstats.features import betting, engine, markets
from betstats.models import Fact, Team, TeamTournamentData
from betstats.rules.world_cup import WorldCupRules
from tests.builders import by_key, make_match

ALFA = Team(1, "Alfa")
BETA = Team(2, "Beta")
PERIOD = "nesta Copa"


def _fact(key, kind, value, sample):
    return Fact(
        text=f"{key} {PERIOD}", value=value, sample=sample, category="x",
        kind=kind, robustness="fragil", team="Alfa", key=key,
    )


class TestBettingAnalyst(unittest.TestCase):
    def test_emite_taxas_de_mercado(self):
        ms = [make_match(fid=i, gf=2, ga=1) for i in range(4)]  # total 3 = over 2,5, BTTS
        facts = betting.analyze(ALFA, ms, PERIOD)
        self.assertEqual(by_key(facts, "aposta:over25").value, "100%")
        self.assertEqual(by_key(facts, "aposta:btts").value, "100%")
        self.assertEqual(by_key(facts, "aposta:sofre_taxa").value, "100%")

    def test_marca_taxa_so_quando_parcial(self):
        # Marcou em todos -> sem taxa parcial (o binário do ataque cobre).
        ms = [make_match(fid=i, gf=1, ga=0) for i in range(4)]
        self.assertIsNone(by_key(betting.analyze(ALFA, ms, PERIOD), "aposta:marca_taxa"))
        # Marcou em 3 de 4 -> taxa parcial aparece.
        ms2 = [make_match(fid=1, gf=0), make_match(fid=2, gf=1),
               make_match(fid=3, gf=1), make_match(fid=4, gf=1)]
        self.assertEqual(by_key(betting.analyze(ALFA, ms2, PERIOD), "aposta:marca_taxa").value, "75%")


class TestAttachMarkets(unittest.TestCase):
    def test_binario_duro_carrega_mercado_acima_da_porta(self):
        f4 = _fact("ataque:marcou_todos", "binario", "4/4", 4)
        f3 = _fact("ataque:marcou_todos", "binario", "3/3", 3)
        f2 = _fact("ataque:marcou_todos", "binario", "2/2", 2)
        markets.attach_markets([f4, f3, f2])
        self.assertEqual(f4.markets, ["Para Alfa marcar"])
        self.assertEqual(f4.strength, "forte")     # n>=4
        self.assertEqual(f3.strength, "moderado")  # n==3
        self.assertEqual(f2.markets, [])           # abaixo da porta (n<3)

    def test_taxa_respeita_amostra_minima(self):
        rate = config.MIN_SAMPLE_MARKET_RATE
        forte = _fact("aposta:over25", "taxa", "85%", rate)      # exatamente na porta
        pouca = _fact("aposta:over25", "taxa", "85%", rate - 1)  # abaixo da porta
        markets.attach_markets([forte, pouca])
        self.assertEqual(forte.markets, ["Mais de 2,5 gols no jogo"])
        self.assertEqual(forte.strength, "forte")
        self.assertEqual(pouca.markets, [])

    def test_taxa_forca_e_lado(self):
        moderado = _fact("aposta:btts", "taxa", "65%", 6)
        coin = _fact("aposta:btts", "taxa", "55%", 6)   # sem lado claro
        baixo = _fact("aposta:btts", "taxa", "10%", 6)  # lado "não"
        markets.attach_markets([moderado, coin, baixo])
        self.assertEqual(moderado.markets, ["Ambos marcam"])
        self.assertEqual(moderado.strength, "moderado")
        self.assertEqual(coin.markets, [])              # cara-ou-coroa: sem mercado
        self.assertEqual(baixo.markets, ["Ambos não marcam"])
        self.assertEqual(baixo.strength, "forte")       # 10% é extremo


class TestConfrontoConvergencia(unittest.TestCase):
    def _data(self, team, opp_id, n=6, gf=2, ga=2):
        ms = [make_match(team_id=team.id, opp_id=opp_id, gf=gf, ga=ga, fid=i) for i in range(n)]
        return TeamTournamentData(team=team, competition="wc2026", matches=ms)

    def test_acende_quando_os_dois_convergem(self):
        data_a = self._data(ALFA, 2)
        data_b = self._data(BETA, 1)
        facts = engine.confronto(data_a, data_b, WorldCupRules())
        over = by_key(facts, "confronto:over25")
        btts = by_key(facts, "confronto:btts")
        self.assertIsNotNone(over)
        self.assertEqual(over.markets, ["Mais de 2,5 gols no jogo"])
        self.assertIsNotNone(btts)
        # Regra de honestidade: até os fatos de confronto embutem a amostra.
        for f in facts:
            self.assertIn(PERIOD, f.text)

    def test_nao_acende_com_amostra_pequena(self):
        below = config.MIN_SAMPLE_MARKET_RATE - 1  # abaixo da porta de taxa
        data_a = self._data(ALFA, 2, n=below)
        data_b = self._data(BETA, 1, n=below)
        self.assertEqual(engine.confronto(data_a, data_b, WorldCupRules()), [])


if __name__ == "__main__":
    unittest.main()
