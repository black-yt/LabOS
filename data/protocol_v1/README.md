# Lab Protocol Corpus v1

**Generated:** 2026-04-14
**Total passing records:** 5,606 unique protocols
**License:** per-record (see `license` field); majority CC BY / CC BY-NC-ND

## Git snapshot availability

This public repository now keeps the protocol working set that is directly used
by the LabOS benchmark construction pipeline, including:

- `protocol_min_v1.jsonl`
- `protocol_min_v1.stats.json`
- parser code under `pipeline/`
- audit files under `rejected/`
- the smaller per-source record files under `records/`

Two raw source dumps are intentionally not committed because they exceed
GitHub's single-file limit:

- `all.jsonl`
- `records/star.jsonl`

For current LabOS Level 1 construction and evaluation work, the committed
`protocol_min_v1.jsonl` is the canonical local entry point.

## Directory layout

```
corpus_v1/
├── README.md              this file
├── all.jsonl              combined corpus, one protocol per line
├── records/
│   ├── star.jsonl         STAR Protocols    (3,941)
│   ├── bioprot.jsonl      Bio-protocol      (950)
│   ├── oww.jsonl          OpenWetWare       (250)
│   ├── curprot.jsonl      Current Protocols (191)
│   ├── mimb.jsonl         Methods Mol Biol  (142)
│   ├── jove.jsonl         J Vis Exp (JoVE)  (112)
│   └── nprot.jsonl        Nature Protocols  (20)
├── rejected/              records that failed the gate, for audit / re-parse
├── manifest.jsonl         per-id fetch log (source, qc_pass, ts)
├── stats.json             aggregate statistics
├── pipeline/              snapshot of crawler code used to build the corpus
└── docs/
    ├── FEASIBILITY.md     pilot findings + source comparison
    └── SESSION_NOTES.md   build notes + known issues
```

## Schema (each JSONL line)

| field | type | notes |
|---|---|---|
| `id` | str | `{source}:{pmcid-or-doi}`, unique within corpus |
| `source` | str | `star` / `bioprot` / `nprot` / `curprot` / `mimb` / `jove` / `oww` |
| `title`, `doi`, `pmcid`, `pmid` | str | bibliographic ids |
| `license`, `journal`, `pub_year`, `authors` | — | metadata |
| `reagents` | list[{name, vendor, catalog_id, rrid, category}] | **gate: ≥3** |
| `equipment` | list[{name, vendor, model}] | **gate: ≥1 OR materials_raw≥150 chars** |
| `materials_raw` | str | fallback prose |
| `steps` | list[{step_no, text, section, duration}] | **gate: ≥3** |
| `troubleshooting` | list[{problem, solution}] | optional |
| `timing` | str | optional |
| `parser_version` | str | reproducibility key |
| `qc_pass` | bool | always `true` in this file |
| `qc_score` | float 0–1 | weighted completeness |
| `qc_flags` | list[str] | always `[]` for passing; populated on rejected |

See `pipeline/schema.py` for the authoritative dataclass.

## Quality gate

A record is retained only if all of the following hold:
1. `len(reagents) >= 3`
2. `len(equipment) >= 1` OR `len(materials_raw) >= 150`
3. `len(steps) >= 3`
4. non-empty `title`

Records that fail are preserved under `rejected/<source>.jsonl` with `qc_flags` listing the reasons — useful for parser-improvement iterations or downstream LLM rescue.

## License per source

| Source | Predominant license | Redistributable? |
|---|---|---|
| STAR Protocols | CC BY-NC-ND 4.0 | yes with attribution, no derivatives |
| Bio-protocol | CC BY 4.0 | yes |
| Nature Protocols (OA subset) | CC BY 4.0 | yes |
| Current Protocols (OA subset) | CC BY 4.0 | yes |
| Methods Mol Biol (OA subset) | CC BY 4.0 | yes |
| JoVE (OA subset) | CC BY-NC-ND 3.0 | yes with attribution, no derivatives, non-commercial |
| OpenWetWare | CC BY 3.0 | yes |

**Bucketed counts** (from `stats.json`):
- CC BY-NC-ND: 2,929
- CC BY: 1,641
- CC BY-NC: 875
- COVID-19 PMC special permission: 148
- unclassified: 13

## Known caveats

1. **Domain skew.** ~80% of records are molecular/cell biology. Physical/computational/chemical protocols are under-represented.
2. **STAR computational protocols.** 319 STAR articles are computational-only (software + datasets, no wet reagents) and sit in `rejected/star.jsonl` under `reagents<3` — the strict wet-lab gate excludes them by design.
3. **JoVE Table of Materials.** Most JoVE articles ship the ToM as a supplementary PDF that EuroPMC does not mirror. Only 112/2,148 passed; the 2,016 in `rejected/jove.jsonl` are inaccessible without scraping JoVE's own site.
4. **Parser version drift.** `parser_version` is embedded in each record. Re-parsing cached XMLs with a newer parser is supported via `pipeline/reparse.py`.
5. **OpenWetWare coverage.** Only the `Category:Protocol` MediaWiki category was traversed (702 pages). Deeper wiki crawl would add heterogeneous content.

## Reproducing

```bash
cd data/protocol_v1
python -m pipeline.run --source all --limit 10000 --rate 4
python -m pipeline.openwetware --limit 2000 --rate 2
python -m pipeline.reparse --source <name>   # re-run parser over rejected/
python -m pipeline.report                    # print stats table
```

The raw PMC XML cache used during the original crawl is not included in this
Git snapshot. Re-running the full harvest therefore requires access to the
underlying source caches or re-fetching from the upstream sources.
