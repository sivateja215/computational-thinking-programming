"""Genetic Sequence Motif Finder - command line entry point.

Examples:
    python main.py                                   # run on the bundled 3-sequence example
    python main.py --input data/sample_large.fasta --kmin 4 --kmax 8 --maximal
    python main.py --input data/sample_protein.fasta --kmin 3 --kmax 5
    python main.py --align                           # add DP alignment of sequence pairs
"""
from __future__ import annotations

import argparse
import multiprocessing as mp
import sys
import time
from pathlib import Path

from analysis import build_records, format_table, write_csv, write_json
from multiprocessing_search import SearchConfig, search_parallel, search_sequential
from preprocessing import SequenceError, load_dataset
from sequence_alignment import format_alignment, lcs_string, similarity_matrix, smith_waterman

ROOT = Path(__file__).resolve().parent


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Find recurring motifs in DNA/protein sequences.",
                                formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    p.add_argument("--input", "-i", default=str(ROOT / "data" / "sequences.fasta"), help="FASTA file")
    p.add_argument("--alphabet", choices=["auto", "dna", "protein"], default="auto")
    p.add_argument("--kmin", type=int, default=3, help="shortest motif length")
    p.add_argument("--kmax", type=int, default=6, help="longest motif length")
    p.add_argument("--min-occurrences", type=int, default=2, help="min total occurrences")
    p.add_argument("--min-sequences", type=int, default=2, help="min number of sequences containing the motif")
    p.add_argument("--top", type=int, default=20, help="rows to display/save (0 = all)")
    p.add_argument("--sort", choices=["occurrences", "sequences", "length"], default="occurrences")
    p.add_argument("--maximal", action="store_true", help="hide motifs fully contained in a longer motif with equal count")
    p.add_argument("--workers", "-w", type=int, default=mp.cpu_count(), help="worker processes")
    p.add_argument("--sequential", action="store_true", help="disable multiprocessing")
    p.add_argument("--chunk-size", type=int, default=50_000, help="start positions per parallel task")
    p.add_argument("--base-size", type=int, default=5_000, help="divide-and-conquer leaf size")
    p.add_argument("--positions-shown", type=int, default=6, help="positions printed per motif")
    p.add_argument("--align", action="store_true", help="run DP alignment (LCS + Smith-Waterman)")
    p.add_argument("--align-limit", type=int, default=6, help="max sequences used for alignment")
    p.add_argument("--max-align-len", type=int, default=1000, help="truncate sequences to this length for alignment")
    p.add_argument("--output-dir", default=str(ROOT / "results"))
    p.add_argument("--no-save", action="store_true", help="do not write CSV/JSON files")
    return p


def run_alignment(sequences, limit: int, max_len: int) -> None:
    subset = sequences[:limit]
    texts = [s.seq[:max_len] for s in subset]
    if any(len(s.seq) > max_len for s in subset):
        print(f"(sequences truncated to {max_len} residues for the O(n*m) DP alignment)")
    ids = [s.id for s in subset]

    print("\nLCS similarity matrix (2*LCS / (|A|+|B|)):")
    mat = similarity_matrix(texts)
    w = max(len(i) for i in ids + ["id"]) + 1
    print("".ljust(w) + "".join(i.rjust(w) for i in ids))
    for i, row in enumerate(mat):
        print(ids[i].ljust(w) + "".join(f"{v:{w}.2f}" for v in row))

    pairs = sorted(((mat[i][j], i, j) for i in range(len(ids)) for j in range(i + 1, len(ids))),
                   reverse=True)[:3]
    for sim, i, j in pairs:
        aln = smith_waterman(texts[i], texts[j])
        print(f"\nSmith-Waterman local alignment {ids[i]} vs {ids[j]} "
              f"(LCS sim {sim:.2f}, score {aln.score}, identity {aln.identity:.0%}, "
              f"{ids[i]}[{aln.start_a + 1}-{aln.end_a}] / {ids[j]}[{aln.start_b + 1}-{aln.end_b}])")
        print(format_alignment(aln))
        if len(texts[i]) <= 300 and len(texts[j]) <= 300:
            print(f"  Longest common subsequence: {lcs_string(texts[i], texts[j])}")


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    cfg = SearchConfig(args.kmin, args.kmax, args.chunk_size, args.base_size)
    try:
        cfg.validate()
        sequences, alphabet = load_dataset(args.input, args.alphabet)
    except (SequenceError, ValueError) as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 2

    total = sum(len(s) for s in sequences)
    print(f"Loaded {len(sequences)} {alphabet} sequences ({total:,} residues) from {args.input}")
    use_parallel = not args.sequential and args.workers > 1
    mode = f"multiprocessing ({args.workers} workers)" if use_parallel else "sequential"
    print(f"Searching motifs of length {cfg.kmin}-{cfg.kmax} using {mode} ...")

    t0 = time.perf_counter()
    index = (search_parallel(sequences, cfg, args.workers) if use_parallel
             else search_sequential(sequences, cfg))
    elapsed = time.perf_counter() - t0
    print(f"Indexed {len(index):,} distinct k-mers in {elapsed:.3f}s")

    records = build_records(index, sequences, args.min_occurrences, args.min_sequences,
                            args.maximal, args.sort, args.top or None)
    print(f"\nRecurring motifs ({len(records)} shown, ranked by {args.sort}):\n")
    print(format_table(records, args.positions_shown))

    if not args.no_save and records:
        out = Path(args.output_dir)
        out.mkdir(parents=True, exist_ok=True)
        meta = {"input": str(args.input), "alphabet": alphabet, "kmin": cfg.kmin,
                "kmax": cfg.kmax, "mode": mode, "seconds": round(elapsed, 4)}
        write_csv(records, out / "motifs.csv")
        write_json(records, out / "motifs.json", meta)
        print(f"\nSaved {out / 'motifs.csv'} and {out / 'motifs.json'}")

    if args.align:
        run_alignment(sequences, args.align_limit, args.max_align_len)
    return 0


if __name__ == "__main__":
    mp.freeze_support()  # needed for frozen Windows executables
    sys.exit(main())
