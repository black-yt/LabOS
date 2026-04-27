# Level 2 Task Pipeline

This directory contains the LabOS Level 2 data-construction and evaluation
pipeline for long-horizon experimental planning.

Each Level 2 item is built from one protocol segment. The task input contains:

- an experiment background
- a concrete sub-goal
- a set of constraints
- a finite action pool written as Python function definitions
- a list of raw input variables that the model may reference

The target output is a Python program that composes the provided functions into
the correct multi-step procedure.

## Inputs

The current Level 2 constructor reads:

- `data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl`
- `data/assets_actions/autobio_labutopia_assets_actions.md`

The builder scans protocol steps, selects a high-value contiguous window, maps
that window to a normalized action pool, and then uses an OpenRouter model to
write one planning item plus its gold Python program.

The action pool follows the `SGI-WetExperiment` idea of a finite action pool,
but the output format is native Python instead of SGI's custom text structure.
Repeated operations must reuse the same function name instead of inventing new
aliases.

## Builder

The constructor auto-loads `pipeline/level-2/.env`, `pipeline/level-1/.env`,
and the repo-root `.env` when present. A local ignored file can contain:

```dotenv
OPENROUTER_API_KEY="..."
OPENROUTER_MODEL="openai/gpt-5.4"
```

Typical commands:

```bash
conda activate agent
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-2/build_level2_tasks.py --count 20
```

Harder construction mode:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-2/build_level2_tasks.py --count 20 --hardness hard --min-steps 8 --max-steps 12
```

Inspect candidate jobs without calling the API:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-2/build_level2_tasks.py --count 20 --dry-run
```

The builder keeps append-style checkpoints. If the output path is
`foo.json`, the script also writes `foo.partial.jsonl` and restores completed
tasks on rerun.

The current formal setting is:

- `--hardness hard`
- protocol-level action pools by default
- low-level manipulate / rotor-loading actions only when the source steps
  explicitly require them
- repeated `mix / incubate / centrifuge / wash / transfer` chains are
  prioritized

## Evaluator

The evaluator parses the model output as Python rather than JSON. It prefers a
```python fenced block``` when present, but it can also fall back to the first
parsable code segment in a free-form response.

Automatic scoring follows the two-part `SGI-Bench` logic, but on Python AST:

1. `Action Sequence Similarity`
   - if the predicted step count differs from the gold step count, this metric
     is `0`
   - otherwise it uses a Kendall tau style order similarity over the action
     sequence

2. `Parameter Accuracy`
   - compares action names, parameter key sets, literal values, raw-input
     references, and generated-variable dependencies
   - later variable references are checked through a predicted-to-gold output
     mapping instead of direct variable-name matching

The current evaluator reports both `strict` and `relaxed` metrics:

- `strict`
  - keeps the current SGI-like high bar
  - step-count mismatch still drives sequence score to `0`
  - parameter checking stays step-level and exact

- `relaxed`
  - `Relaxed Action Sequence Similarity`:
    fraction of step positions whose action names match, normalized by the
    longer program length
  - `Relaxed Parameter Accuracy`:
    parameters are compared on action-aligned steps, and numeric literals allow
    a uniform `10%` relative tolerance
  - `Relaxed Final Score`:
    average of the two relaxed metrics

Run evaluation with:

```bash
conda activate agent
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-2/evaluate_level2_accuracy.py \
  --questions pipeline/level-2/generated/level2_tasks_20.json \
  --model openai/gpt-5.4
```

The evaluator also supports append-style checkpoints through
`foo.partial.jsonl`, and it reuses completed valid rows while retrying previous
invalid rows.

## Outputs

Outputs are written to `pipeline/level-2/generated/`:

- `level2_tasks_20.json`
- `level2_tasks_20.jsonl`
- `level2_tasks_20.metadata.json`
- `level2_tasks_20.eval.<model>.json`
- `level2_tasks_20.eval.<model>.jsonl`

Formal files currently committed:

- `level2_tasks_200_hard_formal.json`
- `level2_tasks_200_hard_formal.jsonl`
- `level2_tasks_200_hard_formal.metadata.json`
- `level2_tasks_200_hard_formal.eval.openai_gpt-5.4.json`
- `level2_tasks_200_hard_formal.eval.anthropic_claude-opus-4.7.json`
- `level2_tasks_200_hard_formal.eval.google_gemini-3.1-pro-preview.json`

Intermediate smoke, baseline, and `.partial.jsonl` files are local recovery
artifacts and should not be kept in the committed formal set.

Current formal-set summary:

- `200` tasks
- `105` unique protocols
- average gold step count `10.85`
- gold step range `8-13`

Current formal evaluation summary:

- `openai/gpt-5.4`
  - `Strict Final Score = 0.032144100997042166`
  - `Relaxed Action Sequence Similarity = 0.3580599313608028`
  - `Relaxed Parameter Accuracy = 0.3784040783844986`
  - `Relaxed Final Score = 0.36823200487265045`
- `anthropic/claude-opus-4.7`
  - `Strict Final Score = 0.03424404761904762`
  - `Relaxed Action Sequence Similarity = 0.3692846995890867`
  - `Relaxed Parameter Accuracy = 0.3690825400186904`
  - `Relaxed Final Score = 0.36918361980388853`
- `google/gemini-3.1-pro-preview`
  - `Strict Final Score = 0.06177366485638545`
  - `Relaxed Action Sequence Similarity = 0.40570601448849536`
  - `Relaxed Parameter Accuracy = 0.38419150516954326`
  - `Relaxed Final Score = 0.3949487598290191`

## Checks

Useful local checks:

```bash
PYTHONDONTWRITEBYTECODE=1 python -c "import ast, pathlib; ast.parse(pathlib.Path('pipeline/level-2/build_level2_tasks.py').read_text(encoding='utf-8'))"
PYTHONDONTWRITEBYTECODE=1 python -c "import ast, pathlib; ast.parse(pathlib.Path('pipeline/level-2/evaluate_level2_accuracy.py').read_text(encoding='utf-8'))"
git diff --check -- pipeline/level-2 AGENTS.md
```
