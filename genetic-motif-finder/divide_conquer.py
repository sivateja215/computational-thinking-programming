"""Divide-and-conquer k-mer scanning.

The range of k-mer *start positions* is split in half recursively until a
region is small enough (``base_size``) to scan directly. The partial results
are then merged on the way back up. Because the split is over start positions
(not over the text itself) a k-mer that straddles the midpoint is found by
exactly one half - nothing is missed and nothing is counted twice.

    T(n) = 2 T(n/2) + O(n)  ->  O(n log(n / base_size))  with the merge cost
"""
from __future__ import annotations

from typing import Iterator, Tuple

from motif_search import PositionMap, scan_kmers


def merge_position_maps(left: PositionMap, right: PositionMap) -> PositionMap:
    """Merge two maps; every position in ``left`` precedes those in ``right``."""
    if len(left) < len(right):  # extend into the bigger dict
        merged = dict(right)
        for kmer, pos in left.items():
            merged[kmer] = pos + merged[kmer] if kmer in merged else pos
        return merged
    merged = dict(left)
    for kmer, pos in right.items():
        if kmer in merged:
            merged[kmer] = merged[kmer] + pos
        else:
            merged[kmer] = pos
    return merged


def dc_scan(text: str, k: int, start: int, end: int, base_size: int = 5000,
            offset: int = 0) -> PositionMap:
    """Divide-and-conquer scan of k-mer start positions in ``[start, end)``."""
    if base_size < 1:
        raise ValueError("base_size must be >= 1")
    if end - start <= base_size:
        return scan_kmers(text, k, start, end, offset)  # conquer (base case)
    mid = (start + end) // 2  # divide
    left = dc_scan(text, k, start, mid, base_size, offset)
    right = dc_scan(text, k, mid, end, base_size, offset)
    return merge_position_maps(left, right)  # combine


def split_ranges(length: int, chunk_size: int) -> Iterator[Tuple[int, int]]:
    """Yield ``(offset, chunk_len)`` pairs that tile ``range(length)``."""
    if chunk_size < 1:
        raise ValueError("chunk_size must be >= 1")
    for offset in range(0, length, chunk_size):
        yield offset, min(chunk_size, length - offset)
