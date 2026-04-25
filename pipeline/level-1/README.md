# Level 1 Question Pipeline

This directory contains the data-construction pipeline for LabOS Level 1:
Asset Understanding. It builds multiple-choice questions that pair three-view
asset images with protocol-grounded experimental operations.

The generated benchmark item asks a model to inspect one laboratory asset or
asset family, understand the current experimental context, and choose the best
next protocol operation. The item also stores reference reasoning steps and the
single-letter answer used by Level 1 evaluation.

Generated question text, options, reasoning steps, and protocol-alignment
explanations are English-only.

## Inputs

The script reads only local repository data:

- `data/benchmark_inventory/files/`
- `data/benchmark_inventory/multiview_manifest.json`
- `data/benchmark_inventory/benchmark_core_inventory.json`
- `data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl`
- `data/protocol_v1/protocol_min_v1.jsonl`
- `data/benchmark_inventory/level-1-demo.md`

The pipeline selects one inventory entry with rendered multiview images, chooses
three available views, finds a matched protocol and relevant procedure steps,
then asks an OpenRouter chat model to produce a strict JSON question object.
The prompt now also includes nearby protocol steps as distractor material and
explicit asset-affordance guardrails so the generated question is less likely to
leak the asset identity or invent unrealistic options.
Known low-confidence entries such as `autobio_centrifuge_plate_60well` are
excluded from the default candidate pool because they repeatedly invite
unsupported affordance assumptions and weak distractors.
Entry selection is also biased toward harder assets and more diverse protocols,
so active devices and richer affordance distinctions are preferred over passive
container-only questions when enough candidates are available.

The repository is now arranged so a fresh clone can start Level 1 work without
an extra local sync step. In particular, the committed tree already includes:

- `data/benchmark_inventory/files/` with the local 3D / mesh / USD assets used
  by the inventory and preview pipeline
- `data/protocol_v1/protocol_min_v1.jsonl` as the directly usable protocol
  working set for benchmark construction
- `data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl` plus the
  inventory-match byproducts used by this pipeline
- `pipeline/level-1/generated/` with one committed 20-question sample set and
  its `openai/gpt-5.4` evaluation outputs

Two oversized raw corpus dumps remain outside Git because they exceed GitHub's
single-file limit:

- `data/protocol_v1/all.jsonl`
- `data/protocol_v1/records/star.jsonl`

## Quick Start

The pipeline auto-loads `pipeline/level-1/.env` when present. A local ignored
file can contain:

```dotenv
OPENROUTER_API_KEY="..."
OPENROUTER_MODEL="openai/gpt-5.4"
```

With that file in place, generation can run without exporting shell variables:

```bash
conda activate agent
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20
```

Manual environment export still works:

```bash
conda activate agent
export OPENROUTER_API_KEY="..."
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20
```

The default OpenRouter model is `openai/gpt-5.4`. A fallback run with
`qwen/qwen3.6-plus` remains available:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20 --model qwen/qwen3.6-plus
```

The stronger default can also be made explicit:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20 --model openai/gpt-5.4
```

Generation is concurrent by default. The default `--concurrency 4` runs four API
requests at a time while preserving the final output order by question id. Use a
lower value when debugging or if the API route is rate-limited:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20 --concurrency 1
```

The API key can also be passed through stdin so it is not exported into the
shell environment:

```bash
conda activate agent
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --api-key-stdin --count 20
```

To inspect selected asset/protocol/view combinations without calling the API:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --dry-run --count 20
```

## Evaluation

Use the independent evaluator to measure answer accuracy of a multimodal
OpenRouter model on the generated Level 1 questions. The evaluator also
auto-loads `pipeline/level-1/.env`.

The current default evaluation contract is:

- the model may reason in natural language
- the last non-empty line must be exactly `Final Answer: X`
- automatic scoring uses only that final answer letter

This avoids brittle JSON-mode failures for some providers while still leaving a
parsable answer anchor.

```bash
conda activate agent
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/evaluate_level1_accuracy.py --model openai/gpt-5.4
```

Optional flags:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/evaluate_level1_accuracy.py \
  --questions pipeline/level-1/generated/level1_questions_20.json \
  --model openai/gpt-5.4 \
  --concurrency 2 \
  --output pipeline/level-1/generated/level1_questions_20.eval.openai_gpt-5.4.json
```

The evaluator now omits `temperature`, `max_tokens`, and `response_format` by
default, letting the provider use its native defaults. Override them only when
there is a concrete compatibility reason.

The evaluator also supports append-style checkpointing:

- a run writing `foo.json` will also maintain `foo.partial.jsonl`
- completed valid items are restored on rerun
- cached invalid rows are retried instead of being reused

The committed formal 200-question run is:

- question set:
  - `pipeline/level-1/generated/level1_questions_200_gpt54_grouped_formal.json`
- unified natural-language evaluation results:
  - `openai/gpt-5.4`: `102/200 = 0.51`, `invalid_count = 0`
  - `anthropic/claude-opus-4.7`: `100/200 = 0.50`, `invalid_count = 3`
  - `google/gemini-3.1-pro-preview`: `92/200 = 0.46`, `invalid_count = 0`

## Outputs

Outputs are written to `pipeline/level-1/generated/` by default:

- `level1_questions_20.json`
- `level1_questions_20.jsonl`
- `level1_questions_20.metadata.json`
- `level1_questions_200_gpt54_grouped_formal.json`
- `level1_questions_200_gpt54_grouped_formal.jsonl`
- `level1_questions_200_gpt54_grouped_formal.metadata.json`
- `level1_questions_200_gpt54_grouped_formal.eval.<model>.final_answer_unified.json`
- `level1_questions_200_gpt54_grouped_formal.eval.<model>.final_answer_unified.jsonl`

Metadata records the model and requested concurrency used for the run.

Each generated item contains:

- `image_paths`
- `question`
- `options`
- `reasoning_steps`
- `answer`
- source metadata such as `entry_id`, `source_protocol_id`, `source_protocol_step_indices`, and `source_protocol_nearby_step_indices`

## Validation

The script validates each model response before writing the final dataset:

- strict JSON object parsing
- exact option letters, defaulting to `A` through `J`
- a single-letter answer
- non-empty question, options, and reasoning steps
- English-only generated natural-language fields, checked by rejecting CJK text
- question-stem leakage checks that reject explicit asset names, aliases, brands,
  and match-group labels in the stem
- Python-call syntax validation for every option
- rejection of obviously implausible zero-valued operational parameters
- rejection of off-context distractor tokens and unsupported magnetic behavior
  for passive rack-like assets
- rejection of stems that leak the answer direction through functional hints
  such as "volumetric measuring tool" or "container capacity"
- rejection of low-difficulty option sets that do not include at least one
  same-function competitor to the correct answer

Useful local checks after generation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -c "import ast, pathlib; ast.parse(pathlib.Path('pipeline/level-1/build_level1_questions.py').read_text(encoding='utf-8'))"
rg -n -P "[\\x{3400}-\\x{4dbf}\\x{4e00}-\\x{9fff}\\x{3000}-\\x{303f}\\x{ff00}-\\x{ffef}]" pipeline/level-1/generated/level1_questions_20.json
git diff --check -- pipeline/level-1
```
