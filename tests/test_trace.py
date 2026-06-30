"""Trace de execução: serializa candidatos + metadados em JSON."""

import json
import os
import tempfile
import unittest

from betstats.models import Fact
from betstats.pipeline import PipelineResult
from betstats.trace import build_payload, slugify, write_trace


def _fact(key="k"):
    return Fact(
        text="t", value="v", sample=3, category="ataque", kind="contagem",
        robustness="dura", team="Alfa", key=key,
    )


class TestTrace(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(slugify("Argentina x França"), "argentina-x-fran-a")

    def test_payload_captura_candidatos(self):
        result = PipelineResult(
            matchup="Alfa x Beta", phase="Final", candidates=[_fact("a"), _fact("b")]
        )
        payload = build_payload(result, {"source": "test"})
        self.assertEqual(payload["source"], "test")
        self.assertEqual(payload["matchup"], "Alfa x Beta")
        self.assertEqual(payload["n_candidates"], 2)
        self.assertEqual([c["key"] for c in payload["candidates"]], ["a", "b"])
        self.assertIsNone(payload["ranked"])  # --no-llm
        self.assertIsNone(payload["script"])
        self.assertIn("generated_at", payload)

    def test_write_trace_cria_arquivo(self):
        result = PipelineResult(matchup="Alfa x Beta", phase="Final", candidates=[_fact()])
        with tempfile.TemporaryDirectory() as d:
            path = write_trace(result, {"source": "test"}, out_dir=d)
            self.assertTrue(os.path.exists(path))
            data = json.load(open(path, encoding="utf-8"))
            self.assertEqual(data["candidates"][0]["key"], "k")


if __name__ == "__main__":
    unittest.main()
