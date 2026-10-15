"""Tests for the web API layer (no HTTP needed). Run: python -m unittest discover -s tests"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import server

FASTA = ">Sequence_1\nATGCGTACGATGCGT\n>Sequence_2\nCGATGCGTACCTAGC\n>Sequence_3\nTTATGCGTGGATGCGT\n"


class ApiTests(unittest.TestCase):
    def payload(self, **kw):
        base = {"fasta": FASTA, "kmin": 3, "kmax": 6, "mode": "sequential", "workers": 1,
                "align": True, "top": 10}
        base.update(kw)
        return base

    def test_analyze_matches_brief_example(self):
        res = server.analyze(self.payload())
        top = {m["motif"]: m for m in res["motifs"]}
        self.assertEqual(top["ATGCGT"]["occurrences"], 5)
        self.assertEqual(top["ATGCGT"]["sequences_found"], 3)
        self.assertEqual(top["ATGCGT"]["positions"]["Sequence_1"], [1, 10])
        self.assertEqual(res["alphabet"], "dna")
        self.assertEqual(len(res["alignment"]["matrix"]), 3)
        self.assertEqual(len(res["alignment"]["pairs"]), 3)

    def test_parallel_mode_gives_same_motifs(self):
        a = server.analyze(self.payload())
        b = server.analyze(self.payload(mode="parallel", workers=2))
        self.assertEqual(a["motifs"], b["motifs"])

    def test_validation_errors(self):
        for bad in (self.payload(fasta=""), self.payload(fasta=">a\nACGZ\n", alphabet="dna"),
                    self.payload(kmin=7, kmax=3), self.payload(kmin="x"), self.payload(sort="bogus")):
            with self.assertRaises(server.ApiError):
                server.analyze(bad)

    def test_benchmark_rows(self):
        res = server.benchmark(self.payload())
        self.assertEqual(res["rows"][0]["mode"], "sequential")
        self.assertTrue(res["identical"])
        self.assertGreaterEqual(len(res["rows"]), 2)

    def test_samples_listed(self):
        names = [s["name"] for s in server.list_samples()]
        self.assertIn("sequences.fasta", names)


if __name__ == "__main__":
    unittest.main()
