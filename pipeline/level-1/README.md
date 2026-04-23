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

- `data/benchmark_inventory/multiview_manifest.json`
- `data/benchmark_inventory/benchmark_core_inventory.json`
- `data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl`
- `data/benchmark_inventory/level-1-demo.md`

The pipeline selects one inventory entry with rendered multiview images, chooses
three available views, finds a matched protocol and relevant procedure steps,
then asks an OpenRouter chat model to produce a strict JSON question object.

## Quick Start

```bash
conda activate agent
export OPENROUTER_API_KEY="..."
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20
```

The default OpenRouter model is `qwen/qwen3.6-plus`. The same run can be made
explicit:

```bash
PYTHONDONTWRITEBYTECODE=1 python pipeline/level-1/build_level1_questions.py --count 20 --model qwen/qwen3.6-plus
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

## Outputs

Outputs are written to `pipeline/level-1/generated/` by default:

- `level1_questions_20.json`
- `level1_questions_20.jsonl`
- `level1_questions_20.metadata.json`

Each generated item contains:

- `image_paths`
- `question`
- `options`
- `reasoning_steps`
- `answer`
- source metadata such as `entry_id`, `source_protocol_id`, and protocol step indices

## Validation

The script validates each model response before writing the final dataset:

- strict JSON object parsing
- exact option letters, defaulting to `A` through `J`
- a single-letter answer
- non-empty question, options, and reasoning steps
- English-only generated natural-language fields, checked by rejecting CJK text

Useful local checks after generation:

```bash
PYTHONDONTWRITEBYTECODE=1 python -c "import ast, pathlib; ast.parse(pathlib.Path('pipeline/level-1/build_level1_questions.py').read_text(encoding='utf-8'))"
rg -n -P "[\\x{3400}-\\x{4dbf}\\x{4e00}-\\x{9fff}\\x{3000}-\\x{303f}\\x{ff00}-\\x{ffef}]" pipeline/level-1/generated/level1_questions_20.json
git diff --check -- pipeline/level-1
```
