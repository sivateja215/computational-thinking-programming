"""Benchmark sequential vs multiprocessing motif search.

Reports wall-clock time, speedup (T_seq / T_par) and efficiency (speedup / workers)
and verifies that both strategies return identical results.

    python benchmark.py                                  # default synthetic workload
    python benchmark.py --n 100 --length 20000 --kmin 4 --kmax 7
    python benchmark.py --input data/sample_large.fasta  # use your own FASTA
"""
from __future__ import annotations

import argparse
import csv
import multiprocessing as mp
import statistics
import sys
import time
from pathlib import Path

from generate_data import DEFAULT_DNA_MOTIFS, generate_sequences
from multiprocessing_search import SearchConfig, search_parallel, search_sequential
from preprocessing import Sequence, load_dataset

ROOT = Path(__file__).resolve().parent


def timed(fn, repeats: int):
    times, result = [], None
    for _ in range(repeats):
        t0 = time.perf_counter()
        result = fn()
        times.append(time.perf_counter() - t0)
    return statistics.median(times), result


def worker_counts(max_workers: int):
    counts, w = [], 2
    while w < max_workers:
        counts.append(w)
        w *= 2
    return counts + ([max_workers] if max_workers > 1 else [])


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", help="FASTA file (default: generate synthetic DNA)")
    ap.add_argument("--n", type=int, default=40, help="synthetic: number of sequences")
    ap.add_argument("--length", type=int, default=20_000, help="synthetic: sequence length")
    ap.add_argument("--kmin", type=int, default=4)
    ap.add_argument("--kmax", type=int, default=6)
    ap.add_argument("--chunk-size", type=int, default=10_000)
    ap.add_argument("--base-size", type=int, default=2_000)
    ap.add_argument("--max-workers", type=int, default=mp.cpu_count())
    ap.add_argument("--repeats", type=int, default=3, help="runs per setting (median reported)")
    ap.add_argument("--output-dir", default=str(ROOT / "results"))
    a = ap.parse_args(argv)

    if a.input:
        sequences, _ = load_dataset(a.input)
    else:
        seqs = generate_sequences(a.n, a.length, DEFAULT_DNA_MOTIFS)
        sequences = [Sequence(f"seq{i + 1}", s) for i, s in enumerate(seqs)]
    cfg = SearchConfig(a.kmin, a.kmax, a.chunk_size, a.base_size)
    total = sum(len(s) for s in sequences)
    print(f"Workload: {len(sequences)} sequences, {total:,} residues, k={cfg.kmin}-{cfg.kmax}, "
          f"CPU cores={mp.cpu_count()}, repeats={a.repeats} (median)\n")

    t_seq, ref = timed(lambda: search_sequential(sequences, cfg), a.repeats)
    rows = [("sequential", 1, t_seq, 1.0, 1.0)]
    for w in worker_counts(a.max_workers):
        t_par, res = timed(lambda w=w: search_parallel(sequences, cfg, w), a.repeats)
        if res != ref:
            print("ERROR: parallel result differs from sequential result", file=sys.stderr)
            return 1
        speedup = t_seq / t_par
        rows.append((f"multiprocessing", w, t_par, speedup, speedup / w))

    print(f"{'Mode':<16}{'Workers':>8}{'Time (s)':>12}{'Speedup':>10}{'Efficiency':>12}")
    print("-" * 58)
    for mode, w, t, sp, eff in rows:
        print(f"{mode:<16}{w:>8}{t:>12.3f}{sp:>9.2f}x{eff:>11.0%}")
    print("\nResults identical across all modes: OK")

    out = Path(a.output_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(out / "benchmark.csv", "w", newline="") as fh:
        w = csv.writer(fh)
        w.writerow(["mode", "workers", "seconds", "speedup", "efficiency"])
        w.writerows([(m, k, f"{t:.4f}", f"{s:.3f}", f"{e:.3f}") for m, k, t, s, e in rows])
    print(f"Saved {out / 'benchmark.csv'}")

    try:  # optional chart
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        ws = [r[1] for r in rows]
        fig, ax = plt.subplots(1, 2, figsize=(9, 3.6))
        ax[0].plot(ws, [r[3] for r in rows], "o-", label="measured")
        ax[0].plot(ws, ws, "--", color="gray", label="ideal")
        ax[0].set(title="Speedup", xlabel="workers", ylabel="T_seq / T_par"); ax[0].legend()
        ax[1].plot(ws, [r[4] for r in rows], "o-")
        ax[1].set(title="Efficiency", xlabel="workers", ylabel="speedup / workers", ylim=(0, 1.1))
        fig.tight_layout(); fig.savefig(out / "benchmark.png", dpi=130)
        print(f"Saved {out / 'benchmark.png'}")
    except ImportError:
        print("(install matplotlib to also get benchmark.png)")
    return 0


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
