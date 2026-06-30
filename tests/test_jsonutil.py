"""Extração tolerante de JSON da saída do LLM (backend CLI)."""

import unittest

from betstats.llm.jsonutil import extract_json


class TestExtractJson(unittest.TestCase):
    def test_plain(self):
        self.assertEqual(extract_json('{"a": 1}'), {"a": 1})

    def test_fenced_json(self):
        self.assertEqual(extract_json('```json\n{"a": 1}\n```'), {"a": 1})

    def test_fenced_plain(self):
        self.assertEqual(extract_json('```\n{"a": 1}\n```'), {"a": 1})

    def test_prose_around(self):
        text = 'Claro! Aqui está:\n{"a": 1, "b": [2, 3]}\nEspero ter ajudado.'
        self.assertEqual(extract_json(text), {"a": 1, "b": [2, 3]})

    def test_nested_objects(self):
        self.assertEqual(
            extract_json('{"x": {"y": 1}}'), {"x": {"y": 1}}
        )

    def test_raises_when_no_json(self):
        with self.assertRaises(Exception):
            extract_json("sem json aqui")


if __name__ == "__main__":
    unittest.main()
