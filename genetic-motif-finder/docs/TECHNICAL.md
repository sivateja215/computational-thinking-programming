# Technical notes

## Data flow
1. **Preprocessing** (`preprocessing.py`): parse FASTA, upper-case, strip whitespace/digits/gaps,
   reject empty sequences, auto-detect and validate the alphabet.
2. **Chunking** (`multiprocessing_search.build_tasks`): each sequence is cut into chunks of
   `chunk_size` *start positions*. A chunk's text slice is extended by `kmax - 1` residues so
   boundary-crossing k-mers are seen by the chunk where they start.
3. **Parallel divide & conquer** (`scan_task`, `dc_scan`): a worker handles one chunk for every
   k in `[kmin, kmax]`. The start-position range is halved recursively until <= `base_size`,
   scanned directly (hash table of k-mer -> positions) and merged upwards.
4. **Combine** (`combine`): partial maps are merged into `{motif: {sequence: [positions]}}`, positions sorted.
5. **Frequency analysis** (`analysis.build_records`): filter by occurrences / sequences, optional
   maximal-motif filter, rank, export table/CSV/JSON.
6. **DP alignment** (`sequence_alignment.py`): LCS similarity matrix and Smith-Waterman local
   alignment with traceback for the most similar pairs.

## Correctness
* Splitting is over *start positions*, so each k-mer occurrence belongs to exactly one chunk and one
  recursion leaf: no losses at boundaries and no duplicates. Tests compare against a naive scan for
  base sizes 1..10^4 and deliberately tiny chunks (13 residues).
* The parallel result is asserted equal to the sequential result (unit test and every benchmark run).
* `--maximal`: a motif is dropped if its prefix/suffix of length k-1 has the same total count as it
  (every occurrence of the shorter motif extends to the longer one).

## Complexity (N = total residues, K = number of k values, P = workers)
| Step | Time | Memory |
|---|---|---|
| k-mer hashing + D&C | O(K * N) (recursion adds O(log(n/base)) merge depth) | O(distinct k-mers) |
| Parallel search | ~O(K * N / P) + pickling/merge overhead | per-worker partial maps |
| LCS length | O(n*m) | O(min(n,m)) |
| Smith-Waterman | O(n*m) | O(n*m) (hence `--max-align-len`) |

## Design choices and limits
* Python's `dict` is the hash table; k-mers are stored as strings (clear, fast enough in CPython).
* IPC cost: workers return full position maps; this is why small workloads do not speed up.
* Alignment is quadratic, so it is limited to the first `--align-limit` sequences, truncated to `--max-align-len`.
* Smith-Waterman uses linear gaps (match +2, mismatch -1, gap -2). Protein scoring matrices
  (BLOSUM) are not included.

## Web frontend
`server.py` (standard-library `http.server`) serves `static/` and a small JSON API that calls the same
`search_sequential` / `search_parallel`, `build_records` and alignment functions as the CLI, so the UI and
CLI always agree. The page is vanilla HTML/CSS/JS with no CDN, so it works offline. Input is validated
server-side (alphabet, k range, size limits); errors return HTTP 400 with a readable message that the UI
shows in the status line. Results are rendered client-side (bars, table, SVG sequence map, heat map).
