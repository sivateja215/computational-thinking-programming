"""Sequence loading, cleaning and validation.

Reads FASTA (or one-sequence-per-line plain text) files, normalises the
residues and checks them against a DNA or protein alphabet.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

DNA_ALPHABET = frozenset("ACGTUN")
PROTEIN_ALPHABET = frozenset("ACDEFGHIKLMNPQRSTVWYBXZJUO*")

_CLEAN_RE = re.compile(r"[\s\d\-]+")  # whitespace, digits, alignment gaps


class SequenceError(ValueError):
    """Raised when the input data is missing, empty or invalid."""


@dataclass(frozen=True)
class Sequence:
    """A single biological sequence."""

    id: str
    seq: str
    description: str = ""

    def __len__(self) -> int:
        return len(self.seq)


def clean_sequence(raw: str) -> str:
    """Upper-case a raw sequence and drop whitespace, digits and gap characters."""
    return _CLEAN_RE.sub("", raw).upper()


def _unique_id(candidate: str, seen: set) -> str:
    if candidate not in seen:
        return candidate
    n = 2
    while f"{candidate}_{n}" in seen:
        n += 1
    return f"{candidate}_{n}"


def parse_fasta(text: str) -> List[Sequence]:
    """Parse FASTA text. Falls back to one-sequence-per-line if no '>' headers."""
    records: List[Sequence] = []
    seen: set = set()

    def add(header: str, seq: str) -> None:
        if not seq:
            raise SequenceError(f"Sequence '{header}' is empty.")
        parts = header.split(None, 1)
        sid = _unique_id(parts[0], seen)
        seen.add(sid)
        records.append(Sequence(sid, seq, parts[1] if len(parts) > 1 else ""))

    lines = [ln.strip() for ln in text.splitlines()]
    lines = [ln for ln in lines if ln and not ln.startswith(";")]

    if not any(ln.startswith(">") for ln in lines):  # plain text fallback
        for i, ln in enumerate(lines, 1):
            add(f"seq{i}", clean_sequence(ln))
        return records

    header, chunks = None, []
    for ln in lines:
        if ln.startswith(">"):
            if header is not None:
                add(header, clean_sequence("".join(chunks)))
            header, chunks = (ln[1:].strip() or f"seq{len(records) + 1}"), []
        else:
            chunks.append(ln)
    if header is not None:
        add(header, clean_sequence("".join(chunks)))
    return records


def read_sequences(path) -> List[Sequence]:
    """Read sequences from a FASTA file."""
    p = Path(path)
    if not p.is_file():
        raise SequenceError(f"Input file not found: {p}")
    records = parse_fasta(p.read_text(encoding="utf-8"))
    if not records:
        raise SequenceError(f"No sequences found in {p}")
    return records


def detect_alphabet(sequences: List[Sequence]) -> str:
    """Return 'dna' if every residue is a DNA/RNA symbol, otherwise 'protein'."""
    residues = set().union(*(set(s.seq) for s in sequences))
    return "dna" if residues <= DNA_ALPHABET else "protein"


def validate_sequences(sequences: List[Sequence], alphabet: str) -> None:
    """Raise SequenceError if a sequence contains symbols outside the alphabet."""
    allowed = DNA_ALPHABET if alphabet == "dna" else PROTEIN_ALPHABET
    for s in sequences:
        bad = sorted(set(s.seq) - allowed)
        if bad:
            raise SequenceError(
                f"Sequence '{s.id}' has invalid {alphabet} symbols: {' '.join(bad)}"
            )


def load_dataset(path, alphabet: str = "auto"):
    """Read, validate and return (sequences, alphabet)."""
    sequences = read_sequences(path)
    if alphabet == "auto":
        alphabet = detect_alphabet(sequences)
    validate_sequences(sequences, alphabet)
    return sequences, alphabet
