"""Core k-mer (motif) scanning primitives.

Hashing: a Python ``dict`` keyed by the k-mer string is a hash table, so
identifying recurring candidates is O(1) per k-mer.
"""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, List

PositionMap = Dict[str, List[int]]  # k-mer -> sorted start positions (0-based)


def scan_kmers(text: str, k: int, start: int, end: int, offset: int = 0) -> PositionMap:
    """Hash every k-mer whose *start index* lies in ``[start, end)``.

    ``offset`` is added to each position so that results found in a slice of a
    longer sequence are reported in global coordinates.
    """
    end = min(end, len(text) - k + 1)
    found: Dict[str, List[int]] = defaultdict(list)
    for i in range(max(start, 0), end):
        found[text[i:i + k]].append(i + offset)
    return dict(found)


def find_kmers(text: str, k: int) -> PositionMap:
    """Reference implementation: all k-mers of a whole sequence (no splitting)."""
    return scan_kmers(text, k, 0, len(text) - k + 1)


def find_motif_positions(text: str, motif: str) -> List[int]:
    """All (possibly overlapping) 0-based positions of ``motif`` in ``text``."""
    positions, i = [], text.find(motif)
    while i != -1:
        positions.append(i)
        i = text.find(motif, i + 1)
    return positions
