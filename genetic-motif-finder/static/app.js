"use strict";
const $ = (id) => document.getElementById(id);
const state = { result: null, selected: null, alphabet: "dna", mode: "parallel", sortKey: null, sortDir: -1, cpus: 1 };

const esc = (s) => String(s).replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const fmt = (n) => Number(n).toLocaleString();
function colorize(seq) {
  if (state.alphabet !== "dna") return esc(seq);
  return [...seq].map((c) => `<span class="${/[ACGT]/.test(c) ? c : ""}">${esc(c)}</span>`).join("");
}
function setStatus(msg, isErr) { const s = $("status"); s.textContent = msg || ""; s.classList.toggle("err", !!isErr); }
function busy(on) { ["runBtn", "benchBtn"].forEach((id) => ($(id).disabled = on)); }

async function api(path, body) {
  const opt = body === undefined ? {} : { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) };
  const res = await fetch(path, opt);
  let data = {};
  try { data = await res.json(); } catch (e) { /* non-JSON error */ }
  if (!res.ok) throw new Error(data.error || `Request failed (${res.status})`);
  return data;
}

function payload() {
  return {
    fasta: $("fasta").value, alphabet: $("alphabet").value,
    kmin: +$("kmin").value, kmax: +$("kmax").value,
    min_occurrences: +$("minOcc").value, min_sequences: +$("minSeq").value,
    sort: $("sort").value, top: +$("top").value, maximal: $("maximal").checked,
    mode: state.mode, workers: +$("workers").value, align: $("align").checked,
  };
}

/* ---------- tabs / theme ---------- */
function showTab(name) {
  document.querySelectorAll("#tabs button").forEach((b) => b.classList.toggle("on", b.dataset.tab === name));
  document.querySelectorAll(".tab").forEach((t) => (t.hidden = t.id !== "tab-" + name));
}
$("tabs").addEventListener("click", (e) => { if (e.target.dataset.tab) showTab(e.target.dataset.tab); });
$("themeBtn").addEventListener("click", () => {
  const root = document.documentElement;
  const dark = root.dataset.theme ? root.dataset.theme === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
  root.dataset.theme = dark ? "light" : "dark";
});
$("modeSeg").addEventListener("click", (e) => {
  if (!e.target.dataset.mode) return;
  state.mode = e.target.dataset.mode;
  document.querySelectorAll("#modeSeg button").forEach((b) => b.classList.toggle("on", b === e.target));
  $("workers").disabled = state.mode === "sequential";
});

/* ---------- input ---------- */
async function loadSample(name) {
  try { $("fasta").value = (await api("/api/sample?name=" + encodeURIComponent(name))).fasta; setStatus(""); }
  catch (err) { setStatus(err.message, true); }
}
$("sample").addEventListener("change", (e) => loadSample(e.target.value));
$("file").addEventListener("change", (e) => {
  const f = e.target.files[0];
  if (!f) return;
  const r = new FileReader();
  r.onload = () => { $("fasta").value = r.result; setStatus(`Loaded ${f.name}`); };
  r.readAsText(f);
});

/* ---------- analysis ---------- */
$("runBtn").addEventListener("click", async () => {
  busy(true); setStatus("Searching motifs...");
  try {
    const data = await api("/api/analyze", payload());
    state.result = data; state.alphabet = data.alphabet; state.selected = data.motifs[0] ? data.motifs[0].motif : null;
    state.sortKey = null;
    render(); setStatus(`Done in ${data.stats.seconds}s (${data.stats.mode}).`);
  } catch (err) { setStatus(err.message, true); }
  busy(false);
});

function render() {
  const d = state.result;
  $("emptyState").hidden = true; $("results").hidden = false;
  const s = d.stats;
  const cards = [["Sequences", fmt(s.sequences)], ["Residues", fmt(s.residues)], ["Alphabet", d.alphabet.toUpperCase()],
    ["Distinct k-mers", fmt(s.distinct_kmers)], ["Motifs reported", fmt(s.motifs_reported)], ["Search time", s.seconds + " s"]];
  $("stats").innerHTML = cards.map(([k, v]) => `<div class="stat"><b>${v}</b><span>${k}</span></div>`).join("") +
    `<div class="stat"><b style="font-size:15px">${esc(s.mode)}</b><span>k = ${s.kmin} to ${s.kmax}</span></div>`;
  renderBars(); renderTable(); renderMap(); renderAlignment();
}

function select(motif) {
  state.selected = motif; renderBars(); renderTable(); renderMap();
}

function renderBars() {
  const top = state.result.motifs.slice().sort((a, b) => b.occurrences - a.occurrences).slice(0, 10);
  const max = Math.max(1, ...top.map((m) => m.occurrences));
  $("bars").innerHTML = top.length ? top.map((m) =>
    `<div class="bar ${m.motif === state.selected ? "sel" : ""}" data-m="${esc(m.motif)}">
       <span class="motif">${colorize(m.motif)}</span>
       <div class="track"><div class="fill" style="width:${(100 * m.occurrences / max).toFixed(1)}%"></div></div>
       <span class="val">${fmt(m.occurrences)}</span></div>`).join("")
    : '<p class="hint">No motifs matched the filters. Try lowering the minimums.</p>';
}
$("bars").addEventListener("click", (e) => { const b = e.target.closest(".bar"); if (b) select(b.dataset.m); });

function posPreview(m) {
  const flat = [];
  outer: for (const [id, ps] of Object.entries(m.positions)) for (const p of ps) { flat.push(`${id}:${p}`); if (flat.length >= 8) break outer; }
  return flat.join(", ") + (m.occurrences > 8 ? " ..." : "");
}
function renderTable() {
  const q = $("filter").value.trim().toUpperCase();
  let rows = state.result.motifs.filter((m) => !q || m.motif.includes(q));
  if (state.sortKey) rows = rows.slice().sort((a, b) => (a[state.sortKey] > b[state.sortKey] ? 1 : -1) * state.sortDir);
  const th = (k, t) => `<th data-k="${k}">${t}${state.sortKey === k ? (state.sortDir > 0 ? " &#9650;" : " &#9660;") : ""}</th>`;
  $("motifTable").innerHTML = `<thead><tr>${th("motif", "Motif")}${th("length", "Length")}${th("occurrences", "Occurrences")}${th("sequences_found", "Sequences found")}<th>Positions (seq:pos, 1-based)</th></tr></thead><tbody>` +
    rows.map((m) => `<tr data-m="${esc(m.motif)}" class="${m.motif === state.selected ? "sel" : ""}"><td class="motif">${colorize(m.motif)}</td><td>${m.length}</td><td>${fmt(m.occurrences)}</td><td>${m.sequences_found}</td><td class="pos">${esc(posPreview(m))}</td></tr>`).join("") + "</tbody>";
}
$("motifTable").addEventListener("click", (e) => {
  const th = e.target.closest("th[data-k]");
  if (th) { state.sortDir = state.sortKey === th.dataset.k ? -state.sortDir : -1; state.sortKey = th.dataset.k; return renderTable(); }
  const tr = e.target.closest("tr[data-m]"); if (tr) select(tr.dataset.m);
});
$("filter").addEventListener("input", () => state.result && renderTable());

function download(name, text, type) {
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([text], { type })); a.download = name; a.click(); URL.revokeObjectURL(a.href);
}
$("jsonBtn").addEventListener("click", () => state.result && download("motifs.json", JSON.stringify({ stats: state.result.stats, motifs: state.result.motifs }, null, 2), "application/json"));
$("csvBtn").addEventListener("click", () => {
  if (!state.result) return;
  const lines = ["motif,length,occurrences,sequences_found,sequence_ids,positions"];
  for (const m of state.result.motifs) {
    const pos = Object.entries(m.positions).flatMap(([id, ps]) => ps.map((p) => `${id}:${p}`)).join(";");
    lines.push([m.motif, m.length, m.occurrences, m.sequences_found, `"${m.sequence_ids.join(";")}"`, `"${pos}"`].join(","));
  }
  download("motifs.csv", lines.join("\n"), "text/csv");
});

/* ---------- sequence map ---------- */
function renderMap() {
  const d = state.result, sel = $("mapMotif");
  sel.innerHTML = d.motifs.map((m) => `<option ${m.motif === state.selected ? "selected" : ""}>${esc(m.motif)}</option>`).join("");
  const m = d.motifs.find((x) => x.motif === state.selected);
  if (!m) { $("mapBox").innerHTML = ""; $("mapHint").textContent = "No motif selected."; return; }
  const seqs = d.sequences.slice(0, 40), maxLen = Math.max(...seqs.map((s) => s.length));
  const L = 120, W = 820, rowH = 20, scale = W / maxLen;
  let svg = `<svg width="${L + W + 10}" height="${seqs.length * rowH + 30}" role="img" aria-label="Positions of ${esc(m.motif)}">`;
  seqs.forEach((s, i) => {
    const y = i * rowH + 8, hits = m.positions[s.id] || [];
    svg += `<text x="${L - 8}" y="${y + 11}" text-anchor="end" font-size="11" fill="var(--muted)">${esc(s.id.slice(0, 16))}</text>`;
    svg += `<rect x="${L}" y="${y + 3}" width="${s.length * scale}" height="10" rx="3" fill="var(--line)" opacity="${hits.length ? 1 : .45}"/>`;
    hits.forEach((p) => { svg += `<rect x="${L + (p - 1) * scale}" y="${y}" width="${Math.max(2.5, m.length * scale)}" height="16" rx="2" fill="var(--accent)"><title>${esc(s.id)}: ${p}-${p + m.length - 1}</title></rect>`; });
  });
  $("mapBox").innerHTML = svg + "</svg>";
  $("mapHint").innerHTML = `<b class="motif">${colorize(m.motif)}</b> occurs ${fmt(m.occurrences)} times in ${m.sequences_found} of ${d.stats.sequences} sequences.` +
    (d.sequences.length > 40 || d.sequences_truncated ? " Showing the first 40 sequences." : "") + " Grey tracks without green marks do not contain the motif.";
}
$("mapMotif").addEventListener("change", (e) => select(e.target.value));

/* ---------- alignment ---------- */
function renderAlignment() {
  const a = state.result.alignment;
  if (!a) { $("alignHint").textContent = "Alignment was not run. Tick 'DP alignment' and run again (needs at least 2 sequences)."; $("heat").innerHTML = ""; $("pairs").innerHTML = ""; return; }
  $("alignHint").textContent = `2 x LCS / (|A| + |B|), darker = more similar. First ${a.ids.length} sequences` + (a.truncated ? `, truncated to ${a.max_len} residues for the O(n x m) DP.` : ".");
  const cell = (v) => `<td style="background:rgba(26,163,154,${(0.15 + 0.85 * v).toFixed(2)})">${v.toFixed(2)}</td>`;
  $("heat").innerHTML = `<table class="heat"><tr><th></th>${a.ids.map((i) => `<th>${esc(i)}</th>`).join("")}</tr>` +
    a.matrix.map((row, i) => `<tr><th>${esc(a.ids[i])}</th>${row.map(cell).join("")}</tr>`).join("") + "</table>";
  $("pairs").innerHTML = a.pairs.map((p) => {
    const w = 70, chunks = [];
    for (let i = 0; i < p.match_line.length; i += w)
      chunks.push(`A ${colorize(p.aligned_a.slice(i, i + w))}\n  ${esc(p.match_line.slice(i, i + w))}\nB ${colorize(p.aligned_b.slice(i, i + w))}`);
    return `<div class="panel pair"><h3>${esc(p.a)} vs ${esc(p.b)}</h3>
      <div class="meta">LCS similarity ${p.lcs_similarity.toFixed(2)} &middot; Smith-Waterman score ${p.score} &middot; identity ${(100 * p.identity).toFixed(0)}% &middot; ${esc(p.a)}[${p.range_a.join("-")}] / ${esc(p.b)}[${p.range_b.join("-")}]</div>
      <pre class="aln">${chunks.join("\n\n") || "(no local similarity found)"}</pre></div>`;
  }).join("");
}

/* ---------- benchmark ---------- */
$("benchBtn").addEventListener("click", async () => {
  busy(true); setStatus("Benchmarking (runs the search several times)...");
  try {
    const b = await api("/api/benchmark", payload());
    const max = Math.max(...b.rows.map((r) => r.seconds));
    $("benchHint").textContent = `${fmt(b.residues)} residues, k = ${b.kmin} to ${b.kmax}, ${b.cpus} CPU core(s) detected. Parallel and sequential results were verified identical.`;
    $("benchOut").innerHTML = b.rows.map((r) =>
      `<div class="bench-row"><b>${r.mode === "sequential" ? "Sequential" : r.workers + " workers"}</b>
        <div><div class="fill ${r.mode === "sequential" ? "seq" : ""}" style="width:${(100 * r.seconds / max).toFixed(1)}%"></div></div>
        <span>${r.seconds.toFixed(3)} s &middot; ${r.speedup.toFixed(2)}x &middot; ${(100 * r.efficiency).toFixed(0)}%</span></div>`).join("") +
      `<div class="note">Speedup = T<sub>seq</sub> / T<sub>par</sub>; efficiency = speedup / workers. Process start-up and result transfer have a cost, so small inputs (or a machine with few cores) can show speedup below 1x. Use a larger dataset or larger k range to see the benefit.</div>`;
    showTab("bench"); setStatus("Benchmark finished.");
  } catch (err) { setStatus(err.message, true); }
  busy(false);
});

/* ---------- init ---------- */
(async function init() {
  try {
    const [info, samples] = await Promise.all([api("/api/info"), api("/api/samples")]);
    state.cpus = info.cpus; $("cpuPill").textContent = `CPU cores: ${info.cpus}`;
    $("workers").value = Math.max(2, Math.min(info.cpus, 8));
    $("sample").innerHTML = samples.map((s) => `<option value="${esc(s.name)}">${esc(s.name)} (${s.sequences} seq)</option>`).join("");
    if (samples.length) await loadSample(samples[0].name);
  } catch (err) { setStatus("Could not reach the server: " + err.message, true); }
})();
