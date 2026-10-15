"""Unit tests. Run with:  python -m unittest discover -s tests -v   (or pytest)."""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from analysis import build_records, remove_non_maximal
from divide_conquer import dc_scan, merge_position_maps, split_ranges
from motif_search import find_kmers, find_motif_positions
from multiprocessing_search import (SearchConfig, build_tasks, search_parallel,
                                    search_sequential)
from preprocessing import (Sequence, SequenceError, clean_sequence, detect_alphabet,
                           parse_fasta, validate_sequences)
from sequence_alignment import lcs_length, lcs_similarity, lcs_string, smith_waterman

EXAMPLE = ["ATGCGTACGATGCGT", "CGATGCGTACCTAGC", "TTATGCGTGGATGCGT"]


def seqs(texts):
    return [Sequence(f"s{i + 1}", t) for i, t in enumerate(texts)]


class PreprocessingTests(unittest.TestCase):
    def test_parse_multiline_fasta(self):
        recs = parse_fasta(">a desc\nACGT\nacgt\n>b\nTTTT\n")
        self.assertEqual([(r.id, r.seq) for r in recs], [("a", "ACGTACGT"), ("b", "TTTT")])
        self.assertEqual(recs[0].description, "desc")

    def test_plain_lines_and_duplicate_ids(self):
        self.assertEqual([r.seq for r in parse_fasta("ACGT\nTTAA\n")], ["ACGT", "TTAA"])
        self.assertEqual([r.id for r in parse_fasta(">x\nAC\n>x\nGT\n")], ["x", "x_2"])

    def test_clean_and_validate(self):
        self.assertEqual(clean_sequence(" ac-gt 12\n"), "ACGT")
        with self.assertRaises(SequenceError):
            validate_sequences(seqs(["ACGZ"]), "dna")
        self.assertEqual(detect_alphabet(seqs(["ACGT"])), "dna")
        self.assertEqual(detect_alphabet(seqs(["MKVL"])), "protein")

    def test_empty_sequence_rejected(self):
        with self.assertRaises(SequenceError):
            parse_fasta(">a\n>b\nACGT\n")


class DivideConquerTests(unittest.TestCase):
    def test_matches_naive_for_many_base_sizes(self):
        rng = random.Random(1)
        text = "".join(rng.choice("ACGT") for _ in range(500))
        for k in (1, 3, 6):
            expected = find_kmers(text, k)
            for base in (1, 7, 50, 10_000):
                self.assertEqual(dc_scan(text, k, 0, len(text) - k + 1, base), expected)

    def test_merge_and_ranges(self):
        self.assertEqual(merge_position_maps({"A": [1]}, {"A": [5], "C": [6]}),
                         {"A": [1, 5], "C": [6]})
        self.assertEqual(list(split_ranges(10, 4)), [(0, 4), (4, 4), (8, 2)])

    def test_find_motif_positions_overlapping(self):
        self.assertEqual(find_motif_positions("AAAA", "AA"), [0, 1, 2])


class SearchTests(unittest.TestCase):
    def test_chunk_boundaries_do_not_lose_or_duplicate(self):
        rng = random.Random(7)
        data = seqs(["".join(rng.choice("ACGT") for _ in range(400)) for _ in range(3)])
        reference = search_sequential(data, SearchConfig(3, 5, chunk_size=10**9, base_size=10**9))
        tiny = SearchConfig(3, 5, chunk_size=13, base_size=4)
        self.assertGreater(len(build_tasks(data, tiny)), 50)
        self.assertEqual(search_sequential(data, tiny), reference)

    def test_parallel_equals_sequential(self):
        data = seqs(EXAMPLE * 3)
        cfg = SearchConfig(3, 6, chunk_size=8, base_size=3)
        self.assertEqual(search_parallel(data, cfg, 2), search_sequential(data, cfg))

    def test_example_from_spec(self):
        data = seqs(EXAMPLE)
        idx = search_sequential(data, SearchConfig(3, 6))
        recs = {r.motif: r for r in build_records(idx, data, 2, 2)}
        self.assertEqual(recs["ATGCGT"].occurrences, 5)
        self.assertEqual(recs["ATGCGT"].sequences, ["s1", "s2", "s3"])
        self.assertEqual(recs["ATGCGT"].positions["s1"], [1, 10])  # 1-based
        self.assertEqual(recs["GCGT"].occurrences, 5)

    def test_maximal_filter(self):
        data = seqs(EXAMPLE)
        idx = search_sequential(data, SearchConfig(3, 6))
        kept = remove_non_maximal(idx)
        self.assertIn("ATGCGT", kept)
        self.assertNotIn("GCGT", kept)
        self.assertNotIn("TGCG", kept)

    def test_filters(self):
        data = seqs(["AAAA", "CCCC"])
        idx = search_sequential(data, SearchConfig(2, 2))
        self.assertEqual(build_records(idx, data, 2, 2), [])  # no motif in both
        self.assertEqual({r.motif for r in build_records(idx, data, 2, 1)}, {"AA", "CC"})


class AlignmentTests(unittest.TestCase):
    def test_lcs(self):
        self.assertEqual(lcs_length("ATGCGT", "ATGCTT"), 5)
        self.assertEqual(len(lcs_string("ATGCGT", "ATGCTT")), 5)
        self.assertEqual(lcs_length("", "ACGT"), 0)
        self.assertAlmostEqual(lcs_similarity("ACGT", "ACGT"), 1.0)

    def test_smith_waterman_finds_embedded_region(self):
        aln = smith_waterman("TTTTGATTACATTTT", "CCCGATTACACCC")
        self.assertEqual(aln.aligned_a.replace("-", ""), "GATTACA")
        self.assertEqual(aln.score, 14)
        self.assertEqual(aln.identity, 1.0)

    def test_smith_waterman_no_similarity(self):
        aln = smith_waterman("AAAA", "CCCC")
        self.assertEqual((aln.score, aln.aligned_a), (0, ""))


if __name__ == "__main__":
    unittest.main()
