"""Frequency analysis, ranking, filtering and reporting of motifs."""
from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List

from multiprocessing_search import MotifIndex
from preprocessing import Sequence


@dataclass
class MotifRecord:
    motif: str
    occurrences: int                 # total (overlapping) occurrences
    sequences: List[str]             # ids of sequences containing the motif
    positions: Dict[str, List[int]]  # id -> 1-based positions

    @property
    def length(self) -> int:
        return len(self.motif)

    @property
    def n_sequences(self) -> int:
        return len(self.sequences)


def total_occurrences(entry: Dict[int, List[int]]) -> int:
    return sum(len(p) for p in entry.values())


def remove_non_maximal(index: MotifIndex) -> MotifIndex:
    """Drop a motif when a one-residue-longer motif has the same count, i.e.
    every occurrence of the short motif extends to the longer one."""
    absorbed = set()
    for motif, entry in index.items():
        occ = total_occurrences(entry)
        for sub in (motif[:-1], motif[1:]):
            if sub in index and total_occurrences(index[sub]) == occ:
                absorbed.add(sub)
    return {m: e for m, e in index.items() if m not in absorbed}


_SORT_KEYS = {
    "occurrences": lambda r: (-r.occurrences, -r.n_sequences, -r.length, r.motif),
    "sequences": lambda r: (-r.n_sequences, -r.occurrences, -r.length, r.motif),
    "length": lambda r: (-r.length, -r.occurrences, -r.n_sequences, r.motif),
}


def build_records(index: MotifIndex, sequences: List[Sequence], min_occurrences: int = 2,
                  min_sequences: int = 2, maximal_only: bool = False,
                  sort_by: str = "occurrences", top: int | None = None) -> List[MotifRecord]:
    """Filter, rank and convert the raw index into report records."""
    if sort_by not in _SORT_KEYS:
        raise ValueError(f"sort_by must be one of {sorted(_SORT_KEYS)}")
    if maximal_only:
        index = remove_non_maximal(index)
    records: List[MotifRecord] = []
    for motif, entry in index.items():
        occ = total_occurrences(entry)
        if occ < min_occurrences or len(entry) < min_sequences:
            continue
        ids = [sequences[i].id for i in sorted(entry)]
        pos = {sequences[i].id: [p + 1 for p in entry[i]] for i in sorted(entry)}
        records.append(MotifRecord(motif, occ, ids, pos))
    records.sort(key=_SORT_KEYS[sort_by])
    return records[:top] if top else records


def summarize_positions(rec: MotifRecord, max_items: int = 6) -> str:
    flat = [f"{sid}:{p}" for sid, ps in rec.positions.items() for p in ps]
    shown = ", ".join(flat[:max_items])
    return shown + (" ..." if len(flat) > max_items else "")


def format_table(records: List[MotifRecord], max_positions: int = 6) -> str:
    """Render records as an aligned text table (positions are 1-based)."""
    if not records:
        return "No motifs matched the selected filters."
    rows = [("Motif", "Occurrences", "Sequences Found", "Positions (seq:pos, 1-based)")]
    rows += [(r.motif, str(r.occurrences), str(r.n_sequences),
              summarize_positions(r, max_positions)) for r in records]
    widths = [max(len(row[c]) for row in rows) for c in range(4)]
    widths = [min(w, 70) if c == 0 else w for c, w in enumerate(widths)]
    fmt = lambda row: "  ".join(cell.ljust(widths[c]) for c, cell in enumerate(row))
    rule = "  ".join("-" * w for w in widths)
    return "\n".join([fmt(rows[0]), rule] + [fmt(r) for r in rows[1:]])


def write_csv(records: List[MotifRecord], path) -> None:
    with open(path, "w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["motif", "length", "occurrences", "sequences_found",
                    "sequence_ids", "positions"])
        for r in records:
            w.writerow([r.motif, r.length, r.occurrences, r.n_sequences,
                        ";".join(r.sequences),
                        ";".join(f"{s}:{p}" for s, ps in r.positions.items() for p in ps)])


def write_json(records: List[MotifRecord], path, meta: dict | None = None) -> None:
    payload = {"meta": meta or {},
               "motifs": [{"motif": r.motif, "length": r.length,
                           "occurrences": r.occurrences,
                           "sequences_found": r.n_sequences,
                           "positions": r.positions} for r in records]}
    Path(path).write_text(json.dumps(payload, indent=2), encoding="utf-8")
