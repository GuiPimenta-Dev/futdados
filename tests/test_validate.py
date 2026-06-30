"""Pré-filtro de amostra + dedup."""

import unittest

from betstats.models import Fact
from betstats.validate import validate


def fact(key, kind="contagem", sample=5, team="Alfa", robustness="dura"):
    return Fact(
        text=f"fato {key}",
        value="x",
        sample=sample,
        category="ataque",
        kind=kind,
        robustness=robustness,
        team=team,
        key=key,
    )


class TestValidate(unittest.TestCase):
    def test_drops_small_sample_rate(self):
        facts = [fact("a", kind="taxa", sample=2)]  # < MIN_SAMPLE_FOR_RATE (3)
        self.assertEqual(validate(facts), [])

    def test_keeps_rate_at_min_sample(self):
        facts = [fact("a", kind="taxa", sample=3)]
        self.assertEqual(len(validate(facts)), 1)

    def test_keeps_hard_binary_even_with_tiny_sample(self):
        facts = [fact("a", kind="binario", sample=1)]
        self.assertEqual(len(validate(facts)), 1)

    def test_dedup_by_team_and_key(self):
        facts = [fact("a"), fact("a")]
        self.assertEqual(len(validate(facts)), 1)

    def test_same_key_different_team_kept(self):
        facts = [fact("a", team="Alfa"), fact("a", team="Beta")]
        self.assertEqual(len(validate(facts)), 2)


if __name__ == "__main__":
    unittest.main()
