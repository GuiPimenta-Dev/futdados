"""Localização de nomes de seleções (EN -> PT-BR)."""

import unittest

from betstats.data.i18n import localize


class TestLocalize(unittest.TestCase):
    def test_known_nations(self):
        self.assertEqual(localize("France"), "França")
        self.assertEqual(localize("South Korea"), "Coreia do Sul")
        self.assertEqual(localize("Croatia"), "Croácia")
        self.assertEqual(localize("USA"), "Estados Unidos")
        self.assertEqual(localize("England"), "Inglaterra")

    def test_unknown_passes_through(self):
        # Clubes (Brasileirão) e nomes fora do mapa ficam inalterados.
        self.assertEqual(localize("Flamengo"), "Flamengo")
        self.assertEqual(localize("Grêmio"), "Grêmio")


if __name__ == "__main__":
    unittest.main()
