"""Helpers de Match: placar, tempos, clean sheet, pênaltis, gol contra."""

import unittest

from betstats.models import Team
from tests.builders import goal, make_match


class TestMatchHelpers(unittest.TestCase):
    def test_goals_and_result(self):
        m = make_match(1, 2, gf=2, ga=1)
        self.assertEqual(m.goals_for(1), 2)
        self.assertEqual(m.goals_against(1), 1)
        self.assertEqual(m.result_for(1), "V")
        self.assertEqual(m.result_for(2), "D")
        self.assertFalse(m.clean_sheet(1))
        self.assertEqual(m.opponent(1).id, 2)

    def test_away_perspective(self):
        # Time 1 jogando fora: gf/ga continuam na perspectiva do time 1.
        m = make_match(1, 2, gf=0, ga=3, is_home=False)
        self.assertEqual(m.goals_for(1), 0)
        self.assertEqual(m.goals_against(1), 3)
        self.assertEqual(m.home_goals, 3)  # o mandante (time 2) fez 3
        self.assertEqual(m.result_for(1), "D")

    def test_half_splits(self):
        m = make_match(1, 2, gf=2, ga=1, ht_for=1, ht_against=0)
        self.assertEqual(m.ht_goals_for(1), 1)
        self.assertEqual(m.second_half_goals_for(1), 1)
        self.assertEqual(m.ht_goals_against(1), 0)
        self.assertEqual(m.second_half_goals_against(1), 1)

    def test_half_splits_none_when_missing_ht(self):
        m = make_match(1, 2, gf=1, ga=0)  # sem HT
        self.assertIsNone(m.ht_goals_for(1))
        self.assertIsNone(m.second_half_goals_for(1))

    def test_penalty_shootout(self):
        m = make_match(1, 2, gf=1, ga=1, pen_for=4, pen_against=2)
        self.assertTrue(m.decided_by_penalties)
        self.assertTrue(m.won_shootout(1))
        self.assertFalse(m.won_shootout(2))

    def test_clean_sheet(self):
        self.assertTrue(make_match(1, 2, gf=2, ga=0).clean_sheet(1))
        self.assertFalse(make_match(1, 2, gf=2, ga=1).clean_sheet(1))

    def test_goal_minutes_own_goal_credits_opponent(self):
        # Único gol é contra, marcado por jogador do time 2 -> conta PARA o time 1.
        m = make_match(1, 2, gf=1, ga=0, events=[goal(30, 2, own=True)])
        self.assertEqual(m.goal_minutes_for(1), [30])
        self.assertEqual(m.goal_minutes_for(2), [])


if __name__ == "__main__":
    unittest.main()
