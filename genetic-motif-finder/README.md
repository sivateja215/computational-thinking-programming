# Genetic Sequence Motif Finder

Finds recurring motifs (short repeated k-mers) in DNA or protein collections and compares
sequences. It combines **hashing**, **divide-and-conquer**, **multiprocessing** and
**dynamic programming** (LCS and Smith-Waterman), and includes a sequential-vs-parallel benchmark.

Pure Python standard library, Python 3.9+, no installation needed. It ships with both a
**command-line tool** and a **web dashboard** (`python server.py`).

## Quick start (VS Code)

1. Unzip and open the folder: **File > Open Folder...** -> `genetic-motif-finder`.
2. Install the *Python* extension if prompted (recommended in `.vscode/extensions.json`).
3. Open the integrated terminal (**Ctrl+`**) and run:

**Web dashboard (recommended for demos):**

```bash
python server.py                    # opens http://127.0.0.1:8000 in your browser
```

Choose a sample (or paste/upload FASTA), set the k range, press **Find motifs**. The UI shows
summary cards, top-motif bars, a sortable/filterable motif table (CSV/JSON download), a
**sequence map** of where a chosen motif sits in every sequence, the **LCS similarity heat map** with
Smith-Waterman alignments, and a **benchmark** tab (sequential vs multiprocessing). A light/dark
theme toggle is in the header. Stop the server with Ctrl+C. Use `--port 8001` if 8000 is busy,
`--no-browser` to skip auto-opening.

Nice demo settings: sample `sample_large.fasta`, k 4-8, *Maximal motifs only* on, *Sort by* Length,
*Min sequences* 10 - the planted motifs `ATGCGTAC` and `CGCGAATT` rise to the top.

**Command line:**

```bash
python main.py                      # bundled 3-sequence example from the project brief
python main.py --align              # also run DP alignment of the sequences
python main.py --input data/sample_large.fasta --kmin 4 --kmax 8 --maximal
python main.py --input data/sample_protein.fasta --kmin 3 --kmax 5
python benchmark.py                 # sequential vs multiprocessing
python -m unittest discover -s tests -v
```

Use `python3` instead of `python` on macOS/Linux if needed. Or press **F5** and pick a
ready-made configuration (`.vscode/launch.json`); tests appear in the VS Code **Testing** panel.
Optional: `pip install -r requirements-optional.txt` adds a speedup/efficiency chart.

## Project layout

```
genetic-motif-finder/
├── main.py                    CLI entry point (search, report, optional alignment)
├── preprocessing.py           FASTA parsing, cleaning, DNA/protein validation
├── motif_search.py            k-mer hashing primitives
├── divide_conquer.py          recursive divide-and-conquer scan + merge
├── multiprocessing_search.py  chunking, process pool, sequential baseline, combine
├── sequence_alignment.py      LCS and Smith-Waterman (dynamic programming)
├── analysis.py                frequency analysis, ranking, filters, CSV/JSON/table
├── benchmark.py               sequential vs parallel timing, speedup, efficiency
├── generate_data.py           synthetic FASTA generator with planted motifs
├── server.py                  web dashboard backend (stdlib http.server + JSON API)
├── static/                    web UI: index.html, style.css, app.js (no external CDN)
├── data/                      sequences.fasta, sample_large.fasta, sample_protein.fasta
├── tests/                     20 unit tests (engine + web API)
├── docs/TECHNICAL.md          design, complexity, correctness notes
└── .vscode/                   launch, settings, extensions
```

## How it works

```
FASTA -> preprocessing -> split into chunks -> [process 1..N: divide & conquer k-mer hashing]
      -> combine -> frequency analysis -> recurring motifs -> DP alignment (LCS / Smith-Waterman)
```

| Technique | Where |
|---|---|
| Hashing | `dict` keyed by k-mer string collects positions in O(1) per k-mer (`motif_search.py`) |
| Divide & conquer | k-mer start positions are halved recursively, results merged (`divide_conquer.py`) |
| Multiprocessing | each (sequence, chunk) is an independent task in a `multiprocessing.Pool` |
| Dynamic programming | LCS similarity matrix; Smith-Waterman local alignment with traceback |
| Frequency analysis | total occurrences, number of sequences, ranking, `--maximal` filtering |

## Command-line options (`main.py`)

| Option | Default | Meaning |
|---|---|---|
| `--input, -i` | `data/sequences.fasta` | FASTA file (plain one-sequence-per-line also works) |
| `--kmin / --kmax` | 3 / 6 | motif length range |
| `--min-occurrences` | 2 | minimum total occurrences |
| `--min-sequences` | 2 | minimum number of sequences containing the motif |
| `--sort` | occurrences | `occurrences`, `sequences` or `length` |
| `--top` | 20 | rows shown/saved (0 = all) |
| `--maximal` | off | hide motifs absorbed by a longer motif with the same count |
| `--workers, -w` | CPU count | worker processes (`--sequential` disables multiprocessing) |
| `--chunk-size / --base-size` | 50000 / 5000 | parallel task size / divide-and-conquer leaf size |
| `--align` | off | LCS matrix + Smith-Waterman for the most similar pairs |
| `--output-dir`, `--no-save` | `results/` | CSV and JSON output location |

Results are written to `results/motifs.csv` and `results/motifs.json`.

## Example output

`python main.py` on the three sequences from the project brief:

```
Motif   Occurrences  Sequences Found  Positions (seq:pos, 1-based)
------  -----------  ---------------  ------------------------------------------------------
ATGCGT  5            3                Sequence_1:1, Sequence_1:10, Sequence_2:3, Sequence_3:3, Sequence_3:11
GCGT    5            3                Sequence_1:3, Sequence_1:12, Sequence_2:5, Sequence_3:5, Sequence_3:13
ATG     5            3                Sequence_1:1, Sequence_1:10, Sequence_2:3, Sequence_3:3, Sequence_3:11
GATG    3            3                Sequence_1:9, Sequence_2:2, Sequence_3:10
```

Note: *Occurrences* is the **total** number of (overlapping) hits across all sequences and
*Sequences Found* is how many sequences contain the motif. The brief's example figures
(e.g. "ATGCGT -> 3") correspond to the *Sequences Found* column. Positions are **1-based**.

## Benchmark

`python benchmark.py` runs the same tasks sequentially and with 2, 4, ... workers, verifies the
results are identical, and prints time, speedup (`T_seq / T_par`) and efficiency
(`speedup / workers`) to `results/benchmark.csv` (and `benchmark.png` with matplotlib).

Parallel speedup depends on your core count. Worker processes must pickle their partial
results back to the parent, so short sequences or small k ranges can run *slower* in parallel
than sequentially; increase `--n`, `--length` or `--kmax` to see the benefit.
Time includes process-pool start-up for honest end-to-end numbers.

## Input format

Standard FASTA (multi-line sequences allowed). DNA (`ACGTUN`) or protein (20 amino acids plus
`BXZJUO*`) is auto-detected; override with `--alphabet`. Digits, spaces and `-` are stripped.
Create test data with `python generate_data.py --n 50 --length 2000 --out data/mine.fasta`.

## Web API (used by the dashboard)

| Endpoint | Purpose |
|---|---|
| `GET /api/info`, `/api/samples`, `/api/sample?name=` | CPU count, bundled datasets |
| `POST /api/analyze` | JSON: `fasta, kmin, kmax, min_occurrences, min_sequences, sort, top, maximal, mode, workers, align` |
| `POST /api/benchmark` | same inputs; returns timing rows with speedup and efficiency |

The server is single-threaded on purpose (one job at a time) so `multiprocessing` stays safe.
UI limit: 5,000,000 residues per request (1,500,000 for benchmark); use the CLI for larger files.

## Troubleshooting

* `Cannot start on 127.0.0.1:8000` - the port is busy; run `python server.py --port 8001`.
* The dashboard shows a speedup below 1x - normal on 1-2 core machines or small inputs (process start-up cost).
* `Error: Input file not found` - check the `--input` path (relative to the terminal's folder).
* `invalid dna symbols` - the file has non-nucleotide letters; use `--alphabet protein` if it is protein.
* Large `--kmax` on huge data uses a lot of memory (every distinct k-mer is stored); raise `--min-occurrences`
  only affects reporting, so reduce the k range instead.
* On Windows/macOS, multiprocessing uses *spawn*; always run via `python main.py` (the script guards
  `if __name__ == "__main__"`).
