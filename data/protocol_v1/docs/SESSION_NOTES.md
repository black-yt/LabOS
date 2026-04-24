# Lab Protocol Collection — Session Notes

**Date:** 2026-04-14
**Working dir:** `/data/wuyc/protocol/pilot`

## Goal
Build a structured corpus of high-quality lab protocols that each contain:
- Complete reagent/materials list
- Equipment/instrument list
- Step-by-step procedure

## Final Results

| Source | Unique passing | Rejected | Med reagents | Med equipment | Med steps | Avg QC |
|---|---|---|---|---|---|---|
| **STAR Protocols** | **3,928** | 727 | 25 | 13 | 63 | 0.92 |
| **Bio-protocol** | **931** | 66 | 43 | 10 | 39 | 0.84 |
| **Nature Protocols (OA)** | **20** | 8 | 25 | 24 | 58 | 0.87 |
| **TOTAL** | **4,879** | 801 | — | — | — | — |

All records: CC-BY licensed, redistributable. ~4.9k high-quality protocols.

## Pipeline architecture (`crawler/`)

```
crawler/
├── schema.py         Unified Protocol dataclass + validate() hard gate
├── europepmc.py      EuroPMC client: search (cursorMark) + fullTextXML + gzip + retry + rate-limit + disk cache
├── parsers/
│   ├── base.py       strip_tags (+ HTML unescape), extract_sec (balanced nesting), extract_meta, parse_list_items, parse_table, extract_troubleshooting
│   ├── star.py       STAR: Key Resources Table → reagents+equipment; nested sub-secs for Step-by-step
│   ├── bioprot.py    Bio-protocol v0.2: prose; flat <p> with "N." numbering; letter-prefix ("A. Section") as sub-headings
│   └── nprot.py      Nature Protocols: Reagents/Equipment/Reagent setup/Equipment setup/Procedure/Timing/Troubleshooting
├── pipeline.py       Search → fetch → parse → validate → store; SOURCE_QUERIES map
├── storage.py        Append-only JSONL per source (parsed/ vs rejected/) + manifest.jsonl for resume
├── run.py            CLI: python -m crawler.run --source star --limit 10000 --rate 10
└── report.py         Per-source stats table
```

## Hard gate (`schema.py::validate`)

A protocol passes only if:
- `len(reagents) >= 3`
- `len(equipment) >= 1` OR `len(materials_raw) >= 150`
- `len(steps) >= 3`
- has title
- has doi or pmcid

Plus a QC score (weighted completeness, 0–1).

## Data layout

```
data/
├── raw/              Per-PMC XML cache (530 MB, 5000+ files)
├── parsed/{star,bioprot,nprot}.jsonl    Passing records
├── rejected/{...}.jsonl                  Failed records (for audit)
└── manifest.jsonl    Every save appends one line (id, source, qc_pass, ts) — used for resume + stats
```

Total disk: 838 MB. Raw XML cache can be deleted; records are self-contained in JSONL.

## Key implementation findings

1. **Europe PMC `fullTextXML` is the single best entry point.** No auth, covers STAR/Bio-protocol/Nat Protoc/JoVE/Current Protocols. Free, generous rate limit.
2. **STAR Protocols has perfect structure**: `Key Resources Table` is a real HTML table with vendor/Cat#/RRID columns → trivial structured extraction. 100% of articles have KRT + Step-by-step.
3. **Bio-protocol is prose-based**: no tables, but uses `<p>` tags with "N. " numbering. Initial parser got 1/100; fixed with numbered-paragraph heuristic → 93/100.
4. **Nat Protoc OA is tiny (33 total)** — the other 3,871 are paywalled. Would need Springer TDM to go further.
5. **Section `<sec>` nesting must be balanced** when extracting — naive regex with `.*?` silently truncates when sub-secs exist.
6. **Parse is CPU-bound, not network-bound.** Per-process throughput ~1 protocol/s because STAR articles have 100+ list-items + 100+ table rows. Adding more CPU processes scales almost linearly.

## Runtime observations

- First full run at `--rate 10` with 3 concurrent processes achieved only ~2 protocols/s total. Shading this by year bumped STAR to ~7–13/s.
- **Sharding race condition**: when `shard_star.py` (PUB_YEAR) and `shard_star_month.py` (PUB_YEAR + FIRST_PDATE half) ran in parallel, both hit the same PMC IDs, and each process's `seen()` only checks its own in-memory cache. Result: **39% duplicate rows** in `star.jsonl` (3,133 of 8,011 pass lines are dupes). Unique count is accurate; the duplication just wasted parse time. Lesson: shard by strictly disjoint PMC ID ranges, not by overlapping queries.
- Final STAR total (4,325 OA claimed by EuroPMC) → we got 3,928 unique pass + 727 fail = 4,655. Missing ~670 are likely: (a) articles where fulltextXML 404s, (b) articles where our parser failed catastrophically (caught exception, not stored).

## How to resume / extend

```bash
cd /data/wuyc/protocol/pilot
# Resume (skips manifest IDs, re-uses cached XMLs)
python3 -m crawler.run --source star --limit 10000 --rate 10
# Stats only
python3 -m crawler.report
# Custom source: edit SOURCE_QUERIES in pipeline.py + add parser in parsers/
```

## Additional sources surveyed (not yet crawled)

| Source | EuroPMC OA volume | Recommendation |
|---|---|---|
| **JoVE** (J Vis Exp) | 2,148 | HIGH value; needs custom parser (Table of Materials is inside `<table-wrap>` with figure-like markup) |
| **Current Protocols** | 217 | MEDIUM; structure close to Nat Protoc, can reuse nprot parser |
| **Methods in Molecular Biology** | 380 | MEDIUM; two-section Materials/Methods, bioprot parser with light tuning |
| **Nature Methods** | 1,260 | MEDIUM; only "Protocol Update" / "Brief Comm." subset are protocols — needs title filter |
| **F1000Research (titled 'protocol')** | 221 | LOW–MEDIUM |
| **Scientific Reports (titled 'protocol')** | 370 | LOW |
| **Cold Spring Harb Protoc / Methods Enzymol / BMC Methods** | ≤30 each | SKIP (too small) |
| **PLOS ONE methods sections** | 325,526 papers | SKIP for now — methods are a section, not a protocol; LLM-cost prohibitive |

### Non-EuroPMC sources

- **protocols.io** — 10k+ public protocols, needs free OAuth app (5-min registration). Returns structured JSON directly. Would roughly 3× corpus size.
- **Nature Protocols paywalled (3,871)** — needs Springer TDM API (institutional agreement).
- **Addgene Protocols** — narrow domain (plasmid/virus), HTML scrape.
- **OpenWetWare** — 220+ community wiki pages, heterogeneous quality.

## Known issues / tech debt

1. **Duplicate rows in `data/parsed/star.jsonl`** — 3,133 duplicates from shard race. Dedup on load is trivial (`dict` keyed by `id`); fixing at write time would require file locking or a per-ID flock. Left as post-processing step.
2. **JoVE parser missing** — current JoVE run would return 0 results because section names differ from the three covered sources.
3. **No license-aware filtering on output** — we happen to have only CC-BY now, but future Nat Protoc TDM content may have varying licenses; `license` field is stored but not enforced.
4. **Parser version bump not propagated through manifest** — if we improve `bioprot-0.2 → 0.3`, manifest-based skip means old records stay at 0.2. Would need a `parser_version` check in `seen()`.
5. **Retry-only on 5xx/429**: some PMCs returned 404 for fulltextXML; those are correctly surfaced as "no_full_text" errors and skipped (logged in run output).

## Commands / CLI quick reference

```bash
# Run one source
python3 -m crawler.run --source star --limit 10000 --rate 10

# Run shard by year
python3 shard_star.py 2024   # uses PUB_YEAR:2024 filter

# Print report
python3 -m crawler.report

# Stats from manifest
python3 -m crawler.run --stats

# Check a parsed record
python3 -c "import json; print(json.dumps(json.loads(open('data/parsed/star.jsonl').readline()), indent=2))"
```

## Process hygiene

- All crawlers launched via `nohup ... & disown` → survive SSH disconnect and Claude Code exit
- PIDs written to `/tmp/crawl_logs/pids.txt`, per-shard logs in `/tmp/crawl_logs/*.log`
- `manifest.jsonl` appends are POSIX O_APPEND atomic under 4KB, safe across processes (though `seen()` cache does NOT dedupe across processes, hence the race bug)

## Recommended next steps

1. **Dedup `star.jsonl`** (one-liner, trivial) → confirm final 3,928 unique count.
2. **Register protocols.io OAuth app** → biggest corpus expansion (10k+).
3. **Write JoVE parser** → +1,500 with structured Table of Materials.
4. **Fix sharding**: offset-based splits (e.g. cursor-based page ranges) instead of query-based, to eliminate duplicate work.
5. **Add dataset export**: parquet schema-versioned + manifest with hashes for reproducible redistribution.
