"""Dynamic-programming sequence comparison.

* LCS (Longest Common Subsequence)      - global similarity, O(n*m) time
* Smith-Waterman local alignment        - conserved regions, O(n*m) time/space
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import List


def lcs_length(a: str, b: str) -> int:
    """Length of the LCS using two rolling rows (O(min(n, m)) memory)."""
    if len(b) > len(a):
        a, b = b, a
    prev = [0] * (len(b) + 1)
    for ca in a:
        curr = [0]
        for j, cb in enumerate(b, 1):
            curr.append(prev[j - 1] + 1 if ca == cb else max(prev[j], curr[j - 1]))
        prev = curr
    return prev[-1]


def lcs_string(a: str, b: str) -> str:
    """Return one LCS of ``a`` and ``b`` (full table + traceback)."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            dp[i][j] = (dp[i - 1][j - 1] + 1 if a[i - 1] == b[j - 1]
                        else max(dp[i - 1][j], dp[i][j - 1]))
    out, i, j = [], n, m
    while i and j:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1]); i -= 1; j -= 1
        elif dp[i - 1][j] >= dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(out))


def lcs_similarity(a: str, b: str) -> float:
    """Normalised similarity in [0, 1]: 2*LCS / (len(a) + len(b))."""
    if not a and not b:
        return 1.0
    return 2.0 * lcs_length(a, b) / (len(a) + len(b))


@dataclass
class Alignment:
    score: int
    aligned_a: str
    aligned_b: str
    start_a: int  # 0-based, inclusive
    end_a: int    # exclusive
    start_b: int
    end_b: int

    @property
    def matches(self) -> int:
        return sum(x == y and x != "-" for x, y in zip(self.aligned_a, self.aligned_b))

    @property
    def identity(self) -> float:
        n = len(self.aligned_a)
        return self.matches / n if n else 0.0


def smith_waterman(a: str, b: str, match: int = 2, mismatch: int = -1,
                   gap: int = -2) -> Alignment:
    """Best local alignment of ``a`` and ``b`` (Smith-Waterman, linear gaps)."""
    n, m = len(a), len(b)
    H = [[0] * (m + 1) for _ in range(n + 1)]
    best, bi, bj = 0, 0, 0
    for i in range(1, n + 1):
        ai, row, up = a[i - 1], H[i], H[i - 1]
        for j in range(1, m + 1):
            diag = up[j - 1] + (match if ai == b[j - 1] else mismatch)
            val = max(0, diag, up[j] + gap, row[j - 1] + gap)
            row[j] = val
            if val > best:
                best, bi, bj = val, i, j
    ra, rb, i, j = [], [], bi, bj
    while i > 0 and j > 0 and H[i][j] > 0:
        s = match if a[i - 1] == b[j - 1] else mismatch
        if H[i][j] == H[i - 1][j - 1] + s:
            ra.append(a[i - 1]); rb.append(b[j - 1]); i -= 1; j -= 1
        elif H[i][j] == H[i - 1][j] + gap:
            ra.append(a[i - 1]); rb.append("-"); i -= 1
        else:
            ra.append("-"); rb.append(b[j - 1]); j -= 1
    return Alignment(best, "".join(reversed(ra)), "".join(reversed(rb)), i, bi, j, bj)


def format_alignment(aln: Alignment, width: int = 60) -> str:
    """Pretty-print an alignment with a match line (| = match)."""
    mid = "".join("|" if x == y and x != "-" else " "
                  for x, y in zip(aln.aligned_a, aln.aligned_b))
    lines: List[str] = []
    for s in range(0, len(mid), width):
        lines += [f"  A {aln.aligned_a[s:s + width]}",
                  f"    {mid[s:s + width]}",
                  f"  B {aln.aligned_b[s:s + width]}"]
    return "\n".join(lines) if lines else "  (no local similarity found)"


def similarity_matrix(seqs: List[str]) -> List[List[float]]:
    """Symmetric matrix of LCS similarities."""
    n = len(seqs)
    mat = [[1.0] * n for _ in range(n)]
    for i in range(n):
        for j in range(i + 1, n):
            mat[i][j] = mat[j][i] = lcs_similarity(seqs[i], seqs[j])
    return mat
