"""Generate synthetic FASTA data with planted motifs (reproducible via --seed).

Example:
    python generate_data.py --n 30 --length 1000 --out data/sample_large.fasta
"""
from __future__ import annotations

import argparse
import random
from pathlib import Path
from typing import List, Sequence as Seq

ALPHABETS = {"dna": "ACGT", "protein": "ACDEFGHIKLMNPQRSTVWY"}
DEFAULT_DNA_MOTIFS = ["ATGCGTAC", "GGATCC", "TATAAT", "CGCGAATT"]
DEFAULT_PROTEIN_MOTIFS = ["KDEL", "RGDSP", "NASTG"]


def generate_sequences(n: int, length: int, motifs: Seq[str], plant_prob: float = 0.7,
                       alphabet: str = "dna", seed: int = 42) -> List[str]:
    """Return ``n`` random sequences; each motif is planted with ``plant_prob``."""
    rng = random.Random(seed)
    letters = ALPHABETS[alphabet]
    out = []
    for _ in range(n):
        s = [rng.choice(letters) for _ in range(length)]
        for motif in motifs:
            if len(motif) < length and rng.random() < plant_prob:
                for _ in range(rng.randint(1, 3)):
                    p = rng.randrange(0, length - len(motif) + 1)
                    s[p:p + len(motif)] = motif
        out.append("".join(s))
    return out


def write_fasta(seqs: Seq[str], path, prefix: str = "seq", width: int = 70) -> None:
    lines = []
    for i, s in enumerate(seqs, 1):
        lines.append(f">{prefix}{i}")
        lines += [s[j:j + width] for j in range(0, len(s), width)]
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--n", type=int, default=30, help="number of sequences")
    ap.add_argument("--length", type=int, default=1000, help="length of each sequence")
    ap.add_argument("--alphabet", choices=ALPHABETS, default="dna")
    ap.add_argument("--motifs", nargs="*", help="motifs to plant (default: built-in set)")
    ap.add_argument("--plant-prob", type=float, default=0.7)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/generated.fasta")
    a = ap.parse_args()
    motifs = a.motifs or (DEFAULT_DNA_MOTIFS if a.alphabet == "dna" else DEFAULT_PROTEIN_MOTIFS)
    write_fasta(generate_sequences(a.n, a.length, motifs, a.plant_prob, a.alphabet, a.seed), a.out)
    print(f"Wrote {a.n} sequences of length {a.length} to {a.out} (planted: {', '.join(motifs)})")


if __name__ == "__main__":
    main()
