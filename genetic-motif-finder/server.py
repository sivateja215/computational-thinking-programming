"""Web frontend server for the Genetic Sequence Motif Finder.

Starts a small local HTTP server (standard library only) that serves the UI in
``static/`` and exposes a JSON API backed by the same engine used by the CLI.

    python server.py                 # opens http://127.0.0.1:8000 in your browser
    python server.py --port 9000 --no-browser

Endpoints
    GET  /api/info        CPU count and limits
    GET  /api/samples     bundled FASTA files in data/
    GET  /api/sample?name sample file contents
    POST /api/analyze     run motif search (+ optional DP alignment)
    POST /api/benchmark   sequential vs multiprocessing timing
"""
from __future__ import annotations

import argparse
import json
import multiprocessing as mp
import statistics
import sys
import time
import webbrowser
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from analysis import build_records
from benchmark import worker_counts
from multiprocessing_search import SearchConfig, search_parallel, search_sequential
from preprocessing import (SequenceError, detect_alphabet, parse_fasta,
                           validate_sequences)
from sequence_alignment import similarity_matrix, smith_waterman

ROOT = Path(__file__).resolve().parent
STATIC = ROOT / "static"
DATA = ROOT / "data"
MAX_BODY = 25 * 1024 * 1024
MAX_RESIDUES = 5_000_000
MAX_BENCH_RESIDUES = 1_500_000
CONTENT_TYPES = {".html": "text/html; charset=utf-8", ".css": "text/css",
                 ".js": "application/javascript", ".svg": "image/svg+xml"}


class ApiError(ValueError):
    """A problem with the request that should be shown to the user (HTTP 400)."""


def _int(p: dict, key: str, default: int, lo: int, hi: int) -> int:
    try:
        v = int(p.get(key, default))
    except (TypeError, ValueError):
        raise ApiError(f"'{key}' must be an integer")
    if not lo <= v <= hi:
        raise ApiError(f"'{key}' must be between {lo} and {hi}")
    return v


def prepare(p: dict, residue_limit: int = MAX_RESIDUES):
    """Parse and validate the request; return (sequences, alphabet, cfg, workers)."""
    text = p.get("fasta", "")
    if not isinstance(text, str) or not text.strip():
        raise ApiError("Please paste or load some FASTA sequences first.")
    try:
        sequences = parse_fasta(text)
        if not sequences:
            raise ApiError("No sequences found in the input.")
        alphabet = p.get("alphabet", "auto")
        if alphabet not in ("auto", "dna", "protein"):
            raise ApiError("alphabet must be auto, dna or protein")
        if alphabet == "auto":
            alphabet = detect_alphabet(sequences)
        validate_sequences(sequences, alphabet)
    except SequenceError as exc:
        raise ApiError(str(exc))
    total = sum(len(s) for s in sequences)
    if total > residue_limit:
        raise ApiError(f"Input has {total:,} residues; the UI limit is {residue_limit:,}. "
                       "Use the command line for larger datasets.")
    kmin = _int(p, "kmin", 3, 1, 30)
    kmax = _int(p, "kmax", 6, 1, 12)
    if kmax < kmin:
        raise ApiError("k max must be >= k min")
    cfg = SearchConfig(kmin, kmax, chunk_size=20_000, base_size=2_000)
    workers = _int(p, "workers", mp.cpu_count(), 1, 64)
    return sequences, alphabet, cfg, workers


def run_alignment(sequences, limit: int, max_len: int):
    subset = sequences[:limit]
    if len(subset) < 2:
        return None
    texts = [s.seq[:max_len] for s in subset]
    ids = [s.id for s in subset]
    matrix = similarity_matrix(texts)
    pairs = sorted(((matrix[i][j], i, j) for i in range(len(ids))
                    for j in range(i + 1, len(ids))), reverse=True)[:3]
    out = []
    for sim, i, j in pairs:
        a = smith_waterman(texts[i], texts[j])
        mid = "".join("|" if x == y and x != "-" else " "
                      for x, y in zip(a.aligned_a, a.aligned_b))
        out.append({"a": ids[i], "b": ids[j], "lcs_similarity": round(sim, 4),
                    "score": a.score, "identity": round(a.identity, 4),
                    "aligned_a": a.aligned_a, "aligned_b": a.aligned_b, "match_line": mid,
                    "range_a": [a.start_a + 1, a.end_a], "range_b": [a.start_b + 1, a.end_b]})
    return {"ids": ids, "matrix": [[round(v, 4) for v in row] for row in matrix],
            "truncated": any(len(s.seq) > max_len for s in subset), "max_len": max_len,
            "pairs": out}


def analyze(p: dict) -> dict:
    sequences, alphabet, cfg, workers = prepare(p)
    mode = p.get("mode", "parallel")
    parallel = mode == "parallel" and workers > 1
    t0 = time.perf_counter()
    index = (search_parallel(sequences, cfg, workers) if parallel
             else search_sequential(sequences, cfg))
    elapsed = time.perf_counter() - t0
    sort_by = p.get("sort", "occurrences")
    if sort_by not in ("occurrences", "sequences", "length"):
        raise ApiError("invalid sort option")
    records = build_records(index, sequences, _int(p, "min_occurrences", 2, 1, 10**9),
                            _int(p, "min_sequences", 2, 1, 10**9), bool(p.get("maximal")),
                            sort_by, _int(p, "top", 30, 1, 200))
    result = {
        "alphabet": alphabet,
        "stats": {"sequences": len(sequences), "residues": sum(len(s) for s in sequences),
                  "distinct_kmers": len(index), "motifs_reported": len(records),
                  "seconds": round(elapsed, 4),
                  "mode": f"multiprocessing ({workers} workers)" if parallel else "sequential",
                  "kmin": cfg.kmin, "kmax": cfg.kmax},
        "sequences": [{"id": s.id, "length": len(s)} for s in sequences[:200]],
        "sequences_truncated": len(sequences) > 200,
        "motifs": [{"motif": r.motif, "length": r.length, "occurrences": r.occurrences,
                    "sequences_found": r.n_sequences, "sequence_ids": r.sequences,
                    "positions": r.positions} for r in records],
        "alignment": None,
    }
    if p.get("align"):
        result["alignment"] = run_alignment(sequences, _int(p, "align_limit", 6, 2, 10),
                                            _int(p, "max_align_len", 600, 50, 2000))
    return result


def benchmark(p: dict) -> dict:
    sequences, _, cfg, _ = prepare(p, MAX_BENCH_RESIDUES)
    repeats = _int(p, "repeats", 1, 1, 3)
    cpus = mp.cpu_count()

    def timed(fn):
        times, res = [], None
        for _ in range(repeats):
            t0 = time.perf_counter()
            res = fn()
            times.append(time.perf_counter() - t0)
        return statistics.median(times), res

    t_seq, ref = timed(lambda: search_sequential(sequences, cfg))
    rows = [{"mode": "sequential", "workers": 1, "seconds": round(t_seq, 4),
             "speedup": 1.0, "efficiency": 1.0}]
    for w in worker_counts(max(cpus, 2)):
        t_par, res = timed(lambda w=w: search_parallel(sequences, cfg, w))
        if res != ref:
            raise RuntimeError("parallel result differs from sequential result")
        sp = t_seq / t_par
        rows.append({"mode": "multiprocessing", "workers": w, "seconds": round(t_par, 4),
                     "speedup": round(sp, 3), "efficiency": round(sp / w, 3)})
    return {"cpus": cpus, "rows": rows, "identical": True,
            "residues": sum(len(s) for s in sequences), "kmin": cfg.kmin, "kmax": cfg.kmax}


def list_samples():
    out = []
    for f in sorted(DATA.glob("*")):
        if f.suffix.lower() in (".fasta", ".fa", ".txt"):
            text = f.read_text(encoding="utf-8", errors="replace")
            out.append({"name": f.name, "sequences": text.count(">"), "bytes": f.stat().st_size})
    return out


class Handler(BaseHTTPRequestHandler):
    server_version = "MotifFinder/1.0"

    def log_message(self, fmt, *args):
        sys.stderr.write("[%s] %s\n" % (self.log_date_time_string(), fmt % args))

    def _send(self, code: int, body: bytes, ctype: str) -> None:
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(body)

    def _json(self, code: int, obj) -> None:
        self._send(code, json.dumps(obj).encode("utf-8"), "application/json")

    def do_GET(self):
        url = urlparse(self.path)
        try:
            if url.path == "/api/info":
                return self._json(200, {"cpus": mp.cpu_count(), "max_residues": MAX_RESIDUES})
            if url.path == "/api/samples":
                return self._json(200, list_samples())
            if url.path == "/api/sample":
                name = Path(parse_qs(url.query).get("name", [""])[0]).name
                f = DATA / name
                if not name or not f.is_file():
                    return self._json(404, {"error": "sample not found"})
                return self._json(200, {"name": name, "fasta": f.read_text(encoding="utf-8")})
            rel = "index.html" if url.path in ("/", "") else url.path.lstrip("/")
            f = (STATIC / rel).resolve()
            if STATIC.resolve() not in f.parents and f != STATIC.resolve() or not f.is_file():
                return self._json(404, {"error": "not found"})
            self._send(200, f.read_bytes(), CONTENT_TYPES.get(f.suffix, "application/octet-stream"))
        except Exception as exc:  # pragma: no cover
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})

    def do_POST(self):
        routes = {"/api/analyze": analyze, "/api/benchmark": benchmark}
        fn = routes.get(urlparse(self.path).path)
        if fn is None:
            return self._json(404, {"error": "not found"})
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length > MAX_BODY:
                raise ApiError("Request too large.")
            payload = json.loads(self.rfile.read(length) or b"{}")
            if not isinstance(payload, dict):
                raise ApiError("JSON object expected.")
            self._json(200, fn(payload))
        except (ApiError, json.JSONDecodeError) as exc:
            self._json(400, {"error": str(exc)})
        except Exception as exc:
            self._json(500, {"error": f"{type(exc).__name__}: {exc}"})


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description="Motif Finder web UI")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8000)
    ap.add_argument("--no-browser", action="store_true", help="do not open the browser")
    a = ap.parse_args(argv)
    # Single-threaded server: requests run one at a time, which also keeps
    # multiprocessing.Pool safe (no fork from a multi-threaded process).
    try:
        httpd = HTTPServer((a.host, a.port), Handler)
    except OSError as exc:
        print(f"Cannot start on {a.host}:{a.port}: {exc}\nTry: python server.py --port 8001",
              file=sys.stderr)
        return 1
    url = f"http://{a.host}:{a.port}"
    print(f"Motif Finder UI running at {url}  (press Ctrl+C to stop)")
    if not a.no_browser:
        webbrowser.open(url)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nStopped.")
    return 0


if __name__ == "__main__":
    mp.freeze_support()
    sys.exit(main())
