"""Sequential and multiprocessing motif search.

Pipeline:  sequences -> chunk tasks -> (parallel) divide-and-conquer scan
           -> combine -> motif index {motif: {seq_index: [positions]}}
"""
from __future__ import annotations

import multiprocessing as mp
from dataclasses import dataclass
from typing import Dict, Iterable, List, Tuple

from divide_conquer import dc_scan, split_ranges
from motif_search import PositionMap
from preprocessing import Sequence

MotifIndex = Dict[str, Dict[int, List[int]]]
Task = Tuple[int, int, str, int, int, int, int]
# Task = (seq_index, offset, text_slice, chunk_len, kmin, kmax, base_size)


@dataclass(frozen=True)
class SearchConfig:
    kmin: int = 3
    kmax: int = 6
    chunk_size: int = 50_000   # start positions handled by one task
    base_size: int = 5_000     # divide-and-conquer leaf size

    def validate(self) -> None:
        if self.kmin < 1 or self.kmax < self.kmin:
            raise ValueError("Require 1 <= kmin <= kmax")
        if self.chunk_size < 1 or self.base_size < 1:
            raise ValueError("chunk_size and base_size must be >= 1")


def build_tasks(sequences: Iterable[Sequence], cfg: SearchConfig) -> List[Task]:
    """Split each sequence into chunks. A chunk's text slice is extended by
    ``kmax - 1`` residues so k-mers that cross a chunk boundary are still seen
    by the chunk in which they *start*."""
    cfg.validate()
    tasks: List[Task] = []
    for idx, s in enumerate(sequences):
        for offset, chunk_len in split_ranges(len(s.seq), cfg.chunk_size):
            text = s.seq[offset: offset + chunk_len + cfg.kmax - 1]
            tasks.append((idx, offset, text, chunk_len, cfg.kmin, cfg.kmax, cfg.base_size))
    return tasks


def scan_task(task: Task) -> Tuple[int, PositionMap]:
    """Worker: scan one chunk for every k in [kmin, kmax]. Top-level so it can
    be pickled by multiprocessing (required on Windows/macOS 'spawn')."""
    idx, offset, text, chunk_len, kmin, kmax, base_size = task
    merged: PositionMap = {}
    for k in range(kmin, kmax + 1):
        n_starts = min(chunk_len, len(text) - k + 1)
        if n_starts > 0:
            merged.update(dc_scan(text, k, 0, n_starts, base_size, offset))
    return idx, merged  # keys have distinct lengths per k, so update() is safe


def combine(results: Iterable[Tuple[int, PositionMap]]) -> MotifIndex:
    """Combine partial results into one motif index with sorted positions."""
    index: MotifIndex = {}
    for idx, partial in results:
        for kmer, positions in partial.items():
            index.setdefault(kmer, {}).setdefault(idx, []).extend(positions)
    for per_seq in index.values():
        for positions in per_seq.values():
            positions.sort()
    return index


def search_sequential(sequences: List[Sequence], cfg: SearchConfig) -> MotifIndex:
    """Single-process search (baseline for benchmarking)."""
    return combine(scan_task(t) for t in build_tasks(sequences, cfg))


def search_parallel(sequences: List[Sequence], cfg: SearchConfig,
                    workers: int | None = None) -> MotifIndex:
    """Multiprocessing search: tasks are distributed over a process pool."""
    tasks = build_tasks(sequences, cfg)
    workers = max(1, workers or mp.cpu_count())
    if not tasks:
        return {}
    chunksize = max(1, len(tasks) // (workers * 4))
    with mp.Pool(processes=workers) as pool:
        return combine(pool.imap_unordered(scan_task, tasks, chunksize=chunksize))
