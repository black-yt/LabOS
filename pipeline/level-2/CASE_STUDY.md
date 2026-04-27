# Level 2 数据概览与案例分析
这份文档用于集中查看 Level 2 正式 hard 数据集的来源、构造思路、题目分布、strict / relaxed 两套评测结果，以及 5 个完整 case study。这里的中文只负责解释结构；题目输入、动作池代码、gold program、模型原始回答都保留英文原文，不做翻译，也不做压缩。
## 1. 数据源
- `data/benchmark_inventory/protocol_min_v1_with_inventory.jsonl`：Level 2 的 protocol 主来源。
- `data/assets_actions/autobio_labutopia_assets_actions.md`：动作概念与资产来源映射。
- 设计参考：`SGI-WetExperiment` 的 action pool 概念，以及 `SGI-Bench` `step_2_score.py` 的顺序 / 参数评分思路。
## 2. 简要构造 pipeline
1. 从 protocol 数据里扫描连续 step window，优先保留同一局部 stage 内、重复 `mix / incubate / centrifuge / wash / transfer` 的长链片段。
2. 根据 step 文本推断动作族，再从统一 action library 中抽取局部 action pool，默认保持在 protocol 抽象层。
3. 生成题目输入：背景、子目标、约束、raw inputs、以及完整 Python 函数定义形式的 action pool。
4. 生成 gold program：要求只用题面给出的函数，使用变量赋值和前序变量依赖，不允许表达式拼接。
5. 用 AST evaluator 计算 strict 指标；在此基础上，再给出 relaxed 指标，用于避免“步数不一致直接记 0”的过严现象。
## 3. 当前题目分布
| 指标 | 数值 |
| --- | --- |
| 正式题量 | 200 |
| 不同 protocol 数量 | 105 |
| 平均 gold 步数 | 10.85 |
| gold 步数分布 | 8: 11, 9: 22, 10: 39, 11: 49, 12: 72, 13: 7 |
| window family 分布 | centrifuge: 191, device: 33, incubate: 198, measure: 47, mix: 168, separate: 184, transfer: 200, wash: 168 |
## 4. 正式评测结果
| 模型 | OpenRouter 返回模型 | Strict Final | Relaxed Seq | Relaxed Param | Relaxed Final | Invalid |
| --- | --- | --- | --- | --- | --- | --- |
| GPT-5.4 | openai/gpt-5.4-20260305 | 0.032144 | 0.35806 | 0.378404 | 0.368232 | 4 |
| Claude Opus 4.7 | anthropic/claude-4.7-opus-20260416 | 0.034244 | 0.369285 | 0.369083 | 0.369184 | 13 |
| Gemini 3.1 Pro Preview | google/gemini-3.1-pro-preview-20260219 | 0.061774 | 0.405706 | 0.384192 | 0.394949 | 23 |
## 5. 代表性题目与 case study
下面 5 个样例覆盖了“极难 / 偏难 / 中位 / 强分歧 / 高分恢复”几类典型情况。
### level2_q0156：极难样例：三模型总体都很低，且存在 invalid
| 字段 | 内容 |
| --- | --- |
| protocol_id | star:PMC11135028 |
| protocol_title | Protocol for separation of fungal extracellular vesicles using ultracentrifugation from solid medium cultures |
| gold_step_count | 8 |
| window_families | centrifuge, incubate, separate, transfer |
| source_step_indices | 43, 44, 45, 46, 47, 48, 49, 50, 51, 52, 53, 54 |
| 模型 | Strict Final | Relaxed Final | 解析状态 |
| --- | --- | --- | --- |
| GPT-5.4 | 0.0 | 0.020685 | valid |
| Claude Opus 4.7 | 0.0 | 0.0 | invalid |
| Gemini 3.1 Pro Preview | 0.0 | 0.0 | invalid |
#### 原题输入（英文原文）
**Background**

````text
A fungal extracellular vesicle preparation has already been separated on an iodixanol density gradient and now needs downstream recovery of the gradient fractions, cleanup by ultracentrifugation, and preservation for later analysis. The current stage focuses on harvesting equal-volume fractions, diluting them in filtered PBS, re-pelleting vesicle material, removing residual liquid, resuspending the pellets in a small final volume, and freezing the recovered material.
````
**Goal**

````text
Generate the procedure to recover extracellular vesicle material from the completed iodixanol gradient and prepare the cleaned fraction samples for frozen storage.
````
**Constraints**

````text
- Start from a gradient sample that has already finished the enrichment ultracentrifugation stage.
- Recover 12 fractions of 1 mL each from the top toward the bottom into fresh tubes.
- Add 9 mL of 0.22 μm-filtered PBS to each fraction before the cleanup ultracentrifugation.
- Use a cleanup spin at 100000 x g for 60 min at 4°C after dilution.
- Include removal of remaining supernatant before final resuspension, represented by a brief drying or draining operation.
- Resuspend the recovered pellet material in 100 μL PBS with active mixing, then transfer the processed fractions to sterile tubes for storage at -80°C.
````
**Available Raw Inputs**

````text
- iodixanol_gradient: Completed iodixanol density gradient containing extracellular vesicle material after the enrichment ultracentrifugation.
- pbs_022um: Sterile 1x PBS filtered through a 0.22 μm membrane.
- fraction_tubes: Fresh ultracentrifuge-compatible tubes for collecting gradient fractions.
- storage_tubes: Sterile tubes intended for final frozen storage of recovered fractions.
````
**Action Pool Code**

```python
def centrifuge_sample(sample: str, speed_xg: int, duration_min: float, temperature_c: float) -> str:
    """Centrifuge a sample at a defined speed, duration, and temperature.

    Args:
        sample: Sample or tube placed in the centrifuge.
        speed_xg: Relative centrifugal force in x g.
        duration_min: Spin time in minutes.
        temperature_c: Centrifuge chamber temperature in Celsius.
    Returns:
        A handle for the centrifuged sample.
    """
    pass


def incubate_sample(sample: str, temperature_c: float, duration_min: float, condition: str) -> str:
    """Incubate a sample under a defined temperature and condition.

    Args:
        sample: Sample placed into incubation.
        temperature_c: Incubation temperature in Celsius.
        duration_min: Incubation time in minutes.
        condition: Condition such as static, shaking, protected from light, or humidified.
    Returns:
        A handle for the incubated sample.
    """
    pass


def heat_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Heat a sample on a named device or heat source.

    Args:
        sample: Sample being heated.
        temperature_c: Target temperature in Celsius.
        duration_min: Heating time in minutes.
        device: Heating device or bath used in the step.
    Returns:
        A handle for the heated sample.
    """
    pass


def cool_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Cool or chill a sample to a target temperature.

    Args:
        sample: Sample being cooled.
        temperature_c: Target cooling temperature in Celsius.
        duration_min: Cooling time in minutes.
        device: Cooling device such as ice bath, refrigerator, or freezer.
    Returns:
        A handle for the cooled sample.
    """
    pass


def set_thermal_mixer(sample: str, temperature_c: float, speed_rpm: int, duration_min: float) -> str:
    """Process a sample in a thermal mixer with specified temperature and agitation.

    Args:
        sample: Sample loaded into the thermal mixer.
        temperature_c: Temperature setting in Celsius.
        speed_rpm: Mixing speed in RPM.
        duration_min: Program duration in minutes.
    Returns:
        A handle for the thermomixed sample.
    """
    pass


def run_thermal_cycler(plate: str, program_name: str, cycles: int, lid_temperature_c: float) -> str:
    """Run a thermal cycler program on a loaded plate or tube strip.

    Args:
        plate: Loaded plate or strip processed by the cycler.
        program_name: Program identifier or stage name.
        cycles: Number of program cycles.
        lid_temperature_c: Heated lid temperature in Celsius.
    Returns:
        A handle for the thermocycled product.
    """
    pass


def dry_sample(sample: str, method: str, temperature_c: float, duration_min: float) -> str:
    """Dry a sample under a defined method and temperature.

    Args:
        sample: Sample being dried.
        method: Drying method such as air dry, oven dry, or vacuum dry.
        temperature_c: Drying temperature in Celsius.
        duration_min: Drying time in minutes.
    Returns:
        A handle for the dried sample.
    """
    pass


def store_sample(sample: str, temperature_c: float, duration_h: float, container: str) -> str:
    """Store a processed sample for later use.

    Args:
        sample: Sample being stored.
        temperature_c: Storage temperature in Celsius.
        duration_h: Storage duration in hours.
        container: Storage vessel or storage location.
    Returns:
        A handle for the stored sample.
    """
    pass


def filter_sample(sample: str, filter_type: str, pore_size_um: float, destination: str) -> str:
    """Filter a sample through a filter or membrane into a destination vessel.

    Args:
        sample: Input sample passed through the filter.
        filter_type: Filter medium or membrane type.
        pore_size_um: Filter pore size in micrometers.
        destination: Destination vessel after filtration.
    Returns:
        A handle for the filtered sample.
    """
    pass


def magnetic_separate(sample: str, rack: str, duration_min: float, collect_phase: str) -> str:
    """Separate a bead-based sample on a magnetic rack.

    Args:
        sample: Sample containing magnetic beads.
        rack: Magnetic rack identifier.
        duration_min: Magnetic separation time in minutes.
        collect_phase: Phase to retain after separation.
    Returns:
        A handle for the magnetically separated sample.
    """
    pass


def place_on_magnet(sample: str, rack: str, duration_min: float, orientation: str) -> str:
    """Place a vessel on a magnetic rack before aspirating or collecting phases.

    Args:
        sample: Sample vessel placed on the magnet.
        rack: Magnetic rack identifier.
        duration_min: Standing time on the magnet in minutes.
        orientation: Required vessel orientation on the rack.
    Returns:
        A handle for the sample after magnetic placement.
    """
    pass


def collect_fraction(sample: str, phase: str, destination: str, volume_ul: float) -> str:
    """Collect a named phase or fraction from a processed sample.

    Args:
        sample: Input sample that contains multiple phases or fractions.
        phase: Named phase or fraction to collect.
        destination: Target vessel for the collected fraction.
        volume_ul: Collected volume in microliters.
    Returns:
        A handle for the collected fraction.
    """
    pass


def add_reagent(sample: str, reagent: str, volume_ul: float, mixing: str) -> str:
    """Add a named reagent into an existing sample or vessel.

    Args:
        sample: Input sample or vessel that receives the reagent.
        reagent: Reagent or buffer being added.
        volume_ul: Added volume in microliters.
        mixing: Mixing instruction applied immediately after addition.
    Returns:
        A handle for the updated sample after reagent addition.
    """
    pass


def aliquot_sample(sample: str, destination: str, volume_ul: float, aliquot_count: int) -> str:
    """Split one sample into a defined aliquot or aliquot series.

    Args:
        sample: Input sample to split.
        destination: Target tube, plate, or vessel.
        volume_ul: Aliquot volume in microliters.
        aliquot_count: Number of equivalent aliquots prepared in the step.
    Returns:
        A handle for the aliquoted sample portion.
    """
    pass
```
**Gold Program**

```python
spin_complete = centrifuge_sample(sample=iodixanol_gradient, speed_xg=100000, duration_min=1080, temperature_c=4)
fractions = collect_fraction(sample=spin_complete, phase="F1-F12 top_to_bottom", destination=fraction_tubes, volume_ul=1000)
diluted_fractions = add_reagent(sample=fractions, reagent=pbs_022um, volume_ul=9000, mixing="invert to dilute each fraction")
washed_pellets = centrifuge_sample(sample=diluted_fractions, speed_xg=100000, duration_min=60, temperature_c=4)
drained_fractions = dry_sample(sample=washed_pellets, method="air dry after inversion on absorbent paper", temperature_c=4, duration_min=1)
resuspended_fractions = add_reagent(sample=drained_fractions, reagent=pbs_022um, volume_ul=100, mixing="pipette several times and rinse tube edges")
storage_aliquots = aliquot_sample(sample=resuspended_fractions, destination=storage_tubes, volume_ul=100, aliquot_count=12)
frozen_fractions = store_sample(sample=storage_aliquots, temperature_c=-80, duration_h=24, container=storage_tubes)
```
#### 模型回答（原始输出）
**GPT-5.4**

````text
```python
fraction_01 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 1", destination="fraction_tubes[1]", volume_ul=1000.0)
fraction_02 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 2", destination="fraction_tubes[2]", volume_ul=1000.0)
fraction_03 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 3", destination="fraction_tubes[3]", volume_ul=1000.0)
fraction_04 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 4", destination="fraction_tubes[4]", volume_ul=1000.0)
fraction_05 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 5", destination="fraction_tubes[5]", volume_ul=1000.0)
fraction_06 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 6", destination="fraction_tubes[6]", volume_ul=1000.0)
fraction_07 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 7", destination="fraction_tubes[7]", volume_ul=1000.0)
fraction_08 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 8", destination="fraction_tubes[8]", volume_ul=1000.0)
fraction_09 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 9", destination="fraction_tubes[9]", volume_ul=1000.0)
fraction_10 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 10", destination="fraction_tubes[10]", volume_ul=1000.0)
fraction_11 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 11", destination="fraction_tubes[11]", volume_ul=1000.0)
fraction_12 = collect_fraction(sample=iodixanol_gradient, phase="top fraction 12", destination="fraction_tubes[12]", volume_ul=1000.0)

fraction_01_diluted = add_reagent(sample=fraction_01, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_02_diluted = add_reagent(sample=fraction_02, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_03_diluted = add_reagent(sample=fraction_03, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_04_diluted = add_reagent(sample=fraction_04, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_05_diluted = add_reagent(sample=fraction_05, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_06_diluted = add_reagent(sample=fraction_06, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_07_diluted = add_reagent(sample=fraction_07, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_08_diluted = add_reagent(sample=fraction_08, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_09_diluted = add_reagent(sample=fraction_09, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_10_diluted = add_reagent(sample=fraction_10, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_11_diluted = add_reagent(sample=fraction_11, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")
fraction_12_diluted = add_reagent(sample=fraction_12, reagent="pbs_022um", volume_ul=9000.0, mixing="invert to mix")

fraction_01_pelleted = centrifuge_sample(sample=fraction_01_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_02_pelleted = centrifuge_sample(sample=fraction_02_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_03_pelleted = centrifuge_sample(sample=fraction_03_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_04_pelleted = centrifuge_sample(sample=fraction_04_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_05_pelleted = centrifuge_sample(sample=fraction_05_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_06_pelleted = centrifuge_sample(sample=fraction_06_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_07_pelleted = centrifuge_sample(sample=fraction_07_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_08_pelleted = centrifuge_sample(sample=fraction_08_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_09_pelleted = centrifuge_sample(sample=fraction_09_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_10_pelleted = centrifuge_sample(sample=fraction_10_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_11_pelleted = centrifuge_sample(sample=fraction_11_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)
fraction_12_pelleted = centrifuge_sample(sample=fraction_12_diluted, speed_xg=100000, duration_min=60.0, temperature_c=4.0)

fraction_01_supernatant_removed = collect_fraction(sample=fraction_01_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_02_supernatant_removed = collect_fraction(sample=fraction_02_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_03_supernatant_removed = collect_fraction(sample=fraction_03_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_04_supernatant_removed = collect_fraction(sample=fraction_04_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_05_supernatant_removed = collect_fraction(sample=fraction_05_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_06_supernatant_removed = collect_fraction(sample=fraction_06_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_07_supernatant_removed = collect_fraction(sample=fraction_07_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_08_supernatant_removed = collect_fraction(sample=fraction_08_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_09_supernatant_removed = collect_fraction(sample=fraction_09_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_10_supernatant_removed = collect_fraction(sample=fraction_10_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_11_supernatant_removed = collect_fraction(sample=fraction_11_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)
fraction_12_supernatant_removed = collect_fraction(sample=fraction_12_pelleted, phase="supernatant", destination="waste", volume_ul=9900.0)

fraction_01_drained = dry_sample(sample=fraction_01_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_02_drained = dry_sample(sample=fraction_02_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_03_drained = dry_sample(sample=fraction_03_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_04_drained = dry_sample(sample=fraction_04_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_05_drained = dry_sample(sample=fraction_05_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_06_drained = dry_sample(sample=fraction_06_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_07_drained = dry_sample(sample=fraction_07_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_08_drained = dry_sample(sample=fraction_08_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_09_drained = dry_sample(sample=fraction_09_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_10_drained = dry_sample(sample=fraction_10_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_11_drained = dry_sample(sample=fraction_11_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)
fraction_12_drained = dry_sample(sample=fraction_12_pelleted, method="air dry", temperature_c=22.0, duration_min=2.0)

fraction_01_resuspended = add_reagent(sample=fraction_01_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_02_resuspended = add_reagent(sample=fraction_02_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_03_resuspended = add_reagent(sample=fraction_03_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_04_resuspended = add_reagent(sample=fraction_04_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_05_resuspended = add_reagent(sample=fraction_05_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_06_resuspended = add_reagent(sample=fraction_06_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_07_resuspended = add_reagent(sample=fraction_07_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_08_resuspended = add_reagent(sample=fraction_08_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_09_resuspended = add_reagent(sample=fraction_09_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_10_resuspended = add_reagent(sample=fraction_10_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_11_resuspended = add_reagent(sample=fraction_11_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")
fraction_12_resuspended = add_reagent(sample=fraction_12_drained, reagent="pbs_022um", volume_ul=100.0, mixing="pipette mix")

fraction_01_mixed = set_thermal_mixer(sample=fraction_01_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_02_mixed = set_thermal_mixer(sample=fraction_02_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_03_mixed = set_thermal_mixer(sample=fraction_03_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_04_mixed = set_thermal_mixer(sample=fraction_04_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_05_mixed = set_thermal_mixer(sample=fraction_05_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_06_mixed = set_thermal_mixer(sample=fraction_06_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_07_mixed = set_thermal_mixer(sample=fraction_07_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_08_mixed = set_thermal_mixer(sample=fraction_08_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_09_mixed = set_thermal_mixer(sample=fraction_09_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_10_mixed = set_thermal_mixer(sample=fraction_10_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_11_mixed = set_thermal_mixer(sample=fraction_11_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)
fraction_12_mixed = set_thermal_mixer(sample=fraction_12_resuspended, temperature_c=4.0, speed_rpm=800, duration_min=2.0)

fraction_01_storage = aliquot_sample(sample=fraction_01_mixed, destination="storage_tubes[1]", volume_ul=100.0, aliquot_count=1)
fraction_02_storage = aliquot_sample(sample=fraction_02_mixed, destination="storage_tubes[2]", volume_ul=100.0, aliquot_count=1)
fraction_03_storage = aliquot_sample(sample=fraction_03_mixed, destination="storage_tubes[3]", volume_ul=100.0, aliquot_count=1)
fraction_04_storage = aliquot_sample(sample=fraction_04_mixed, destination="storage_tubes[4]", volume_ul=100.0, aliquot_count=1)
fraction_05_storage = aliquot_sample(sample=fraction_05_mixed, destination="storage_tubes[5]", volume_ul=100.0, aliquot_count=1)
fraction_06_storage = aliquot_sample(sample=fraction_06_mixed, destination="storage_tubes[6]", volume_ul=100.0, aliquot_count=1)
fraction_07_storage = aliquot_sample(sample=fraction_07_mixed, destination="storage_tubes[7]", volume_ul=100.0, aliquot_count=1)
fraction_08_storage = aliquot_sample(sample=fraction_08_mixed, destination="storage_tubes[8]", volume_ul=100.0, aliquot_count=1)
fraction_09_storage = aliquot_sample(sample=fraction_09_mixed, destination="storage_tubes[9]", volume_ul=100.0, aliquot_count=1)
fraction_10_storage = aliquot_sample(sample=fraction_10_mixed, destination="storage_tubes[10]", volume_ul=100.0, aliquot_count=1)
fraction_11_storage = aliquot_sample(sample=fraction_11_mixed, destination="storage_tubes[11]", volume_ul=100.0, aliquot_count=1)
fraction_12_storage = aliquot_sample(sample=fraction_12_mixed, destination="storage_tubes[12]", volume_ul=100.0, aliquot_count=1)

fraction_01_frozen = store_sample(sample=fraction_01_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[1]")
fraction_02_frozen = store_sample(sample=fraction_02_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[2]")
fraction_03_frozen = store_sample(sample=fraction_03_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[3]")
fraction_04_frozen = store_sample(sample=fraction_04_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[4]")
fraction_05_frozen = store_sample(sample=fraction_05_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[5]")
fraction_06_frozen = store_sample(sample=fraction_06_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[6]")
fraction_07_frozen = store_sample(sample=fraction_07_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[7]")
fraction_08_frozen = store_sample(sample=fraction_08_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[8]")
fraction_09_frozen = store_sample(sample=fraction_09_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[9]")
fraction_10_frozen = store_sample(sample=fraction_10_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[10]")
fraction_11_frozen = store_sample(sample=fraction_11_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[11]")
fraction_12_frozen = store_sample(sample=fraction_12_storage, temperature_c=-80.0, duration_h=24.0, container="storage_tubes[12]")
```
````
**Claude Opus 4.7**

````text
```python
fractions = []
for i in range(12):
    frac = collect_fraction(
        sample="iodixanol_gradient",
        phase=f"fraction_{i+1}_top_to_bottom",
        destination=f"fraction_tubes[{i}]",
        volume_ul=1000.0,
    )
    fractions.append(frac)

diluted = []
for i, frac in enumerate(fractions):
    d = add_reagent(
        sample=frac,
        reagent="pbs_022um",
        volume_ul=9000.0,
        mixing="gentle inversion",
    )
    diluted.append(d)

spun = []
for d in diluted:
    s = centrifuge_sample(
        sample=d,
        speed_xg=100000,
        duration_min=60.0,
        temperature_c=4.0,
    )
    spun.append(s)

drained = []
for s in spun:
    dr = dry_sample(
        sample=s,
        method="air dry",
        temperature_c=4.0,
        duration_min=2.0,
    )
    drained.append(dr)

resuspended = []
for dr in drained:
    r = add_reagent(
        sample=dr,
        reagent="pbs_022um",
        volume_ul=100.0,
        mixing="vortex",
    )
    resuspended.append(r)

transferred = []
for i, r in enumerate(resuspended):
    t = aliquot_sample(
        sample=r,
        destination=f"storage_tubes[{i}]",
        volume_ul=100.0,
        aliquot_count=1,
    )
    transferred.append(t)

stored = []
for t in transferred:
    st = store_sample(
        sample=t,
        temperature_c=-80.0,
        duration_h=24.0,
        container="sterile storage tube at -80C freezer",
    )
    stored.append(st)
```
````
**Gemini 3.1 Pro Preview**

````text
```python
for fraction_index in [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]:
    fraction_sample = collect_fraction(
        sample=iodixanol_gradient,
        phase="gradient_fraction",
        destination=fraction_tubes,
        volume_ul=1000.0
    )

    diluted_sample = add_reagent(
        sample=fraction_sample,
        reagent=pbs_022um,
        volume_ul=9000.0,
        mixing="gentle inversion"
    )

    centrifuged_sample = centrifuge_sample(
        sample=diluted_sample,
        speed_xg=100000,
        duration_min=60.0,
        temperature_c=4.0
    )

    drained_sample = dry_sample(
        sample=centrifuged_sample,
        method="drain supernatant",
        temperature_c=25.0,
        duration_min=1.0
    )

    resuspended_sample = add_reagent(
        sample=drained_sample,
        reagent=pbs_022um,
        volume_ul=100.0,
        mixing="active mixing"
    )

    transferred_sample = aliquot_sample(
        sample=resuspended_sample,
        destination=storage_tubes,
        volume_ul=100.0,
        aliquot_count=1
    )

    stored_sample = store_sample(
        sample=transferred_sample,
        temperature_c=-80.0,
        duration_h=720.0,
        container="-80C freezer"
    )
```
````
### level2_q0003：偏难样例：重复热混匀与离心链条
| 字段 | 内容 |
| --- | --- |
| protocol_id | star:PMC10519843 |
| protocol_title | Protocol to capture transcription factor-mediated 3D chromatin interactions using affinity tag-based BL-HiChIP |
| gold_step_count | 13 |
| window_families | centrifuge, incubate, measure, mix, separate, transfer, wash |
| source_step_indices | 83, 84, 85, 86, 87, 88, 89, 90, 91, 92, 93, 94 |
| 模型 | Strict Final | Relaxed Final | 解析状态 |
| --- | --- | --- | --- |
| GPT-5.4 | 0.0 | 0.315476 | valid |
| Claude Opus 4.7 | 0.0 | 0.340278 | valid |
| Gemini 3.1 Pro Preview | 0.0 | 0.0 | invalid |
#### 原题输入（英文原文）
**Background**

````text
In the BL-HiChIP workflow, immunoprecipitated chromatin has already been captured on magnetic beads and washed. The current stage focuses on releasing DNA-protein complexes from the beads, reversing crosslinks with Proteinase K, extracting and precipitating DNA, and finally resuspending and quantifying the recovered BL-HiChIP DNA.
````
**Goal**

````text
Process the washed immunoprecipitation bead sample through elution, reverse crosslinking, organic extraction, DNA precipitation, pellet cleanup, final resuspension, and concentration measurement to obtain purified BL-HiChIP DNA ready for downstream QC.
````
**Constraints**

````text
- Use the washed immunoprecipitation bead material as the starting sample and maintain a single dependency chain through purification.
- Perform bead elution under thermal mixing conditions corresponding to 65 degrees Celsius, 900 rpm, and 30 minutes.
- Represent the repeated elution outcome as a combined eluate totaling 600 microliters before reverse crosslinking.
- Reverse crosslinking must include Proteinase K digestion at 55 degrees Celsius overnight; normalize overnight as 16 hours.
- The phase-separation tube preparation requires a high-speed spin at 16000 x g for 0.5 minutes at 25 degrees Celsius before extraction.
- After adding phenol-chloroform-isoamyl alcohol, vigorously mix and then centrifuge at 16000 x g for 5 minutes at 25 degrees Celsius.
- DNA precipitation must reflect isopropanol and sodium acetate conditions followed by storage at minus 20 degrees Celsius overnight; normalize overnight as 16 hours.
- Pellet recovery requires centrifugation at 16000 x g for 30 minutes at 4 degrees Celsius.
- After ethanol washes, include a drying step of 5 minutes at 25 degrees Celsius before final dissolution.
- Final DNA dissolution must occur in 10 mM Tris-HCl at 37 degrees Celsius for 60 minutes, followed by a concentration readout with a Qubit-style fluorometric assay and a recorded concentration metric.
````
**Available Raw Inputs**

````text
- washed_ip_beads: Washed BL-HiChIP immunoprecipitation beads after the final wash series
- dna_elution_buffer: DNA elution buffer used to release protein-chromatin DNA complexes from beads
- proteinase_k_digest_mix: Proteinase K reagent already combined conceptually with the eluate for reverse crosslinking
- maxtract_tube: MaXtract high-density tube prepared for phenol-chloroform extraction
- organic_extraction_mix: Phenol-chloroform-isoamyl alcohol extraction mixture
- dna_precipitation_mix: Isopropanol, sodium acetate, and GlycoBlue precipitation setup
- tris_resuspension_buffer: 10 mM Tris-HCl pH 8.0 used for final DNA resuspension
````
**Action Pool Code**

```python
def centrifuge_sample(sample: str, speed_xg: int, duration_min: float, temperature_c: float) -> str:
    """Centrifuge a sample at a defined speed, duration, and temperature.

    Args:
        sample: Sample or tube placed in the centrifuge.
        speed_xg: Relative centrifugal force in x g.
        duration_min: Spin time in minutes.
        temperature_c: Centrifuge chamber temperature in Celsius.
    Returns:
        A handle for the centrifuged sample.
    """
    pass


def incubate_sample(sample: str, temperature_c: float, duration_min: float, condition: str) -> str:
    """Incubate a sample under a defined temperature and condition.

    Args:
        sample: Sample placed into incubation.
        temperature_c: Incubation temperature in Celsius.
        duration_min: Incubation time in minutes.
        condition: Condition such as static, shaking, protected from light, or humidified.
    Returns:
        A handle for the incubated sample.
    """
    pass


def heat_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Heat a sample on a named device or heat source.

    Args:
        sample: Sample being heated.
        temperature_c: Target temperature in Celsius.
        duration_min: Heating time in minutes.
        device: Heating device or bath used in the step.
    Returns:
        A handle for the heated sample.
    """
    pass


def cool_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Cool or chill a sample to a target temperature.

    Args:
        sample: Sample being cooled.
        temperature_c: Target cooling temperature in Celsius.
        duration_min: Cooling time in minutes.
        device: Cooling device such as ice bath, refrigerator, or freezer.
    Returns:
        A handle for the cooled sample.
    """
    pass


def set_thermal_mixer(sample: str, temperature_c: float, speed_rpm: int, duration_min: float) -> str:
    """Process a sample in a thermal mixer with specified temperature and agitation.

    Args:
        sample: Sample loaded into the thermal mixer.
        temperature_c: Temperature setting in Celsius.
        speed_rpm: Mixing speed in RPM.
        duration_min: Program duration in minutes.
    Returns:
        A handle for the thermomixed sample.
    """
    pass


def run_thermal_cycler(plate: str, program_name: str, cycles: int, lid_temperature_c: float) -> str:
    """Run a thermal cycler program on a loaded plate or tube strip.

    Args:
        plate: Loaded plate or strip processed by the cycler.
        program_name: Program identifier or stage name.
        cycles: Number of program cycles.
        lid_temperature_c: Heated lid temperature in Celsius.
    Returns:
        A handle for the thermocycled product.
    """
    pass


def dry_sample(sample: str, method: str, temperature_c: float, duration_min: float) -> str:
    """Dry a sample under a defined method and temperature.

    Args:
        sample: Sample being dried.
        method: Drying method such as air dry, oven dry, or vacuum dry.
        temperature_c: Drying temperature in Celsius.
        duration_min: Drying time in minutes.
    Returns:
        A handle for the dried sample.
    """
    pass


def store_sample(sample: str, temperature_c: float, duration_h: float, container: str) -> str:
    """Store a processed sample for later use.

    Args:
        sample: Sample being stored.
        temperature_c: Storage temperature in Celsius.
        duration_h: Storage duration in hours.
        container: Storage vessel or storage location.
    Returns:
        A handle for the stored sample.
    """
    pass


def measure_signal(sample: str, assay: str, wavelength_nm: int, replicate_n: int) -> str:
    """Measure a sample with an assay-specific readout.

    Args:
        sample: Sample or plate being measured.
        assay: Measurement assay or modality.
        wavelength_nm: Measurement wavelength in nanometers.
        replicate_n: Number of technical replicates included in the readout.
    Returns:
        A handle for the measurement result.
    """
    pass


def record_measurement(sample: str, metric: str, unit: str, note: str) -> str:
    """Record a derived metric or QC observation from a processed sample.

    Args:
        sample: Sample or output being documented.
        metric: Named metric being recorded.
        unit: Unit of the recorded metric.
        note: Short observation or QC note.
    Returns:
        A handle for the recorded measurement entry.
    """
    pass


def mix_sample(sample: str, method: str, duration_s: float, speed: str) -> str:
    """Mix a sample using a generic laboratory method.

    Args:
        sample: Sample being mixed.
        method: Mixing method such as inversion, pipetting, or rocking.
        duration_s: Mixing duration in seconds.
        speed: Speed setting or qualitative speed description.
    Returns:
        A handle for the mixed sample.
    """
    pass


def vortex_mix(sample: str, duration_s: float, speed_rpm: int, temperature_c: float) -> str:
    """Mix a sample on a vortex mixer.

    Args:
        sample: Sample placed on the vortex mixer.
        duration_s: Vortex duration in seconds.
        speed_rpm: Mixer speed in RPM.
        temperature_c: Ambient or controlled temperature during mixing.
    Returns:
        A handle for the vortexed sample.
    """
    pass


def stir_with_rod(container: str, duration_s: float, speed_desc: str, temperature_c: float) -> str:
    """Stir a liquid sample with a glass rod or stirring tool.

    Args:
        container: Container holding the liquid to stir.
        duration_s: Stirring duration in seconds.
        speed_desc: Qualitative stirring intensity.
        temperature_c: Sample temperature during stirring.
    Returns:
        A handle for the stirred sample.
    """
    pass


def shake_container(sample: str, amplitude_mm: float, repeat_n: int, duration_s: float) -> str:
    """Shake a closed vessel for coarse liquid mixing.

    Args:
        sample: Sample or vessel being shaken.
        amplitude_mm: Shake amplitude in millimeters.
        repeat_n: Number of shake repetitions or cycles.
        duration_s: Total shaking duration in seconds.
    Returns:
        A handle for the shaken sample.
    """
    pass
```
**Gold Program**

```python
eluted_beads = set_thermal_mixer(sample=washed_ip_beads, temperature_c=65.0, speed_rpm=900, duration_min=30.0)
combined_eluate = mix_sample(sample=eluted_beads, method="pipetting", duration_s=20.0, speed="medium")
reverse_crosslinked = incubate_sample(sample=proteinase_k_digest_mix, temperature_c=55.0, duration_min=960.0, condition="static")
prepared_maxtract = centrifuge_sample(sample=maxtract_tube, speed_xg=16000, duration_min=0.5, temperature_c=25.0)
extraction_mixed = vortex_mix(sample=organic_extraction_mix, duration_s=10.0, speed_rpm=3000, temperature_c=25.0)
phase_separated = centrifuge_sample(sample=extraction_mixed, speed_xg=16000, duration_min=5.0, temperature_c=25.0)
precipitation_mixed = mix_sample(sample=dna_precipitation_mix, method="inversion", duration_s=15.0, speed="gentle")
precipitated_dna = store_sample(sample=precipitation_mixed, temperature_c=-20.0, duration_h=16.0, container="1.5 mL tube")
dna_pellet = centrifuge_sample(sample=precipitated_dna, speed_xg=16000, duration_min=30.0, temperature_c=4.0)
dried_pellet = dry_sample(sample=dna_pellet, method="air dry", temperature_c=25.0, duration_min=5.0)
resuspended_dna = incubate_sample(sample=tris_resuspension_buffer, temperature_c=37.0, duration_min=60.0, condition="static")
qubit_readout = measure_signal(sample=resuspended_dna, assay="Qubit fluorometer", wavelength_nm=0, replicate_n=1)
recorded_concentration = record_measurement(sample=qubit_readout, metric="DNA concentration", unit="ng/uL", note="BL-HiChIP DNA after purification and resuspension")
```
#### 模型回答（原始输出）
**GPT-5.4**

````text
```python
elution_round_1 = set_thermal_mixer(
    sample="washed_ip_beads + 300 uL dna_elution_buffer",
    temperature_c=65.0,
    speed_rpm=900,
    duration_min=30.0,
)

elution_round_2 = set_thermal_mixer(
    sample="washed_ip_beads after first elution + 300 uL dna_elution_buffer",
    temperature_c=65.0,
    speed_rpm=900,
    duration_min=30.0,
)

combined_eluate = mix_sample(
    sample="eluate_from_elution_round_1 + eluate_from_elution_round_2; total_volume=600 uL",
    method="pipetting",
    duration_s=20.0,
    speed="moderate",
)

reverse_crosslink_setup = mix_sample(
    sample="combined_eluate + proteinase_k_digest_mix",
    method="pipetting",
    duration_s=20.0,
    speed="moderate",
)

reverse_crosslinked = incubate_sample(
    sample=reverse_crosslink_setup,
    temperature_c=55.0,
    duration_min=960.0,
    condition="static",
)

maxtract_pre_spun = centrifuge_sample(
    sample="maxtract_tube",
    speed_xg=16000,
    duration_min=0.5,
    temperature_c=25.0,
)

extraction_setup = mix_sample(
    sample=f"{reverse_crosslinked} transferred_to {maxtract_pre_spun} + organic_extraction_mix",
    method="pipetting",
    duration_s=20.0,
    speed="moderate",
)

extraction_vigorous_mix = vortex_mix(
    sample=extraction_setup,
    duration_s=30.0,
    speed_rpm=3000,
    temperature_c=25.0,
)

phase_separated = centrifuge_sample(
    sample=extraction_vigorous_mix,
    speed_xg=16000,
    duration_min=5.0,
    temperature_c=25.0,
)

precipitation_setup = mix_sample(
    sample=f"aqueous_phase_from {phase_separated} + dna_precipitation_mix",
    method="inversion",
    duration_s=30.0,
    speed="gentle",
)

precipitation_cold_storage = store_sample(
    sample=precipitation_setup,
    temperature_c=-20.0,
    duration_h=16.0,
    container="precipitation_tube",
)

pellet_recovery = centrifuge_sample(
    sample=precipitation_cold_storage,
    speed_xg=16000,
    duration_min=30.0,
    temperature_c=4.0,
)

ethanol_wash_1 = mix_sample(
    sample=f"pellet_from {pellet_recovery} + 70% ethanol",
    method="inversion",
    duration_s=15.0,
    speed="gentle",
)

ethanol_wash_1_spin = centrifuge_sample(
    sample=ethanol_wash_1,
    speed_xg=16000,
    duration_min=5.0,
    temperature_c=4.0,
)

ethanol_wash_2 = mix_sample(
    sample=f"pellet_from {ethanol_wash_1_spin} + 70% ethanol",
    method="inversion",
    duration_s=15.0,
    speed="gentle",
)

ethanol_wash_2_spin = centrifuge_sample(
    sample=ethanol_wash_2,
    speed_xg=16000,
    duration_min=5.0,
    temperature_c=4.0,
)

dried_pellet = dry_sample(
    sample=f"pellet_from {ethanol_wash_2_spin}",
    method="air dry",
    temperature_c=25.0,
    duration_min=5.0,
)

resuspension_setup = mix_sample(
    sample=f"{dried_pellet} + tris_resuspension_buffer",
    method="pipetting",
    duration_s=20.0,
    speed="gentle",
)

resuspended_dna = incubate_sample(
    sample=resuspension_setup,
    temperature_c=37.0,
    duration_min=60.0,
    condition="static",
)

qubit_readout = measure_signal(
    sample=resuspended_dna,
    assay="Qubit fluorometric DNA assay",
    wavelength_nm=0,
    replicate_n=1,
)

recorded_concentration = record_measurement(
    sample=qubit_readout,
    metric="BL-HiChIP DNA concentration",
    unit="ng/uL",
    note="Purified DNA resuspended in 10 mM Tris-HCl after elution, reverse crosslinking, organic extraction, precipitation, ethanol wash, and drying.",
)
```
````
**Claude Opus 4.7**

````text
```python
# Step 1: Elute DNA from washed IP beads at 65C, 900 rpm, 30 min
eluate = set_thermal_mixer(sample="washed_ip_beads + dna_elution_buffer", temperature_c=65.0, speed_rpm=900, duration_min=30.0)

# Combined eluate (600 uL total from repeated elutions)
combined_eluate = mix_sample(sample=eluate + " combined 600uL", method="pipetting", duration_s=30.0, speed="gentle")

# Step 2: Reverse crosslinking with Proteinase K at 55C overnight (16 h)
rev_xlink = incubate_sample(sample=combined_eluate + " + proteinase_k_digest_mix", temperature_c=55.0, duration_min=960.0, condition="static")

# Step 3: Prepare MaXtract tube with high-speed spin
prepped_maxtract = centrifuge_sample(sample="maxtract_tube", speed_xg=16000, duration_min=0.5, temperature_c=25.0)

# Step 4: Add sample + phenol-chloroform-isoamyl alcohol, vigorously mix
loaded_maxtract = mix_sample(sample=prepped_maxtract + " + " + rev_xlink + " + organic_extraction_mix", method="inversion", duration_s=30.0, speed="vigorous")
vortexed_extract = vortex_mix(sample=loaded_maxtract, duration_s=30.0, speed_rpm=2500, temperature_c=25.0)

# Step 5: Phase separation centrifugation
phase_separated = centrifuge_sample(sample=vortexed_extract, speed_xg=16000, duration_min=5.0, temperature_c=25.0)

# Step 6: DNA precipitation with isopropanol + sodium acetate, store at -20C overnight (16 h)
precip_mix = mix_sample(sample=phase_separated + " + dna_precipitation_mix", method="inversion", duration_s=30.0, speed="moderate")
precipitated = store_sample(sample=precip_mix, temperature_c=-20.0, duration_h=16.0, container="freezer tube")

# Step 7: Pellet recovery at 16000 x g, 30 min, 4C
pellet = centrifuge_sample(sample=precipitated, speed_xg=16000, duration_min=30.0, temperature_c=4.0)

# Step 8: Ethanol washes (represented as wash + spin cycles)
wash1 = mix_sample(sample=pellet + " + 70% ethanol", method="inversion", duration_s=15.0, speed="gentle")
wash1_spin = centrifuge_sample(sample=wash1, speed_xg=16000, duration_min=5.0, temperature_c=4.0)
wash2 = mix_sample(sample=wash1_spin + " + 70% ethanol", method="inversion", duration_s=15.0, speed="gentle")
wash2_spin = centrifuge_sample(sample=wash2, speed_xg=16000, duration_min=5.0, temperature_c=4.0)

# Step 9: Dry pellet 5 min at 25C
dried_pellet = dry_sample(sample=wash2_spin, method="air dry", temperature_c=25.0, duration_min=5.0)

# Step 10: Final dissolution in 10 mM Tris-HCl at 37C for 60 min
dissolved_dna = incubate_sample(sample=dried_pellet + " + tris_resuspension_buffer", temperature_c=37.0, duration_min=60.0, condition="static")

# Step 11: Qubit-style fluorometric concentration measurement
qubit_reading = measure_signal(sample=dissolved_dna, assay="Qubit dsDNA HS fluorometric", wavelength_nm=485, replicate_n=1)

# Step 12: Record DNA concentration metric
recorded_conc = record_measurement(sample=dissolved_dna, metric="DNA concentration", unit="ng/uL", note="BL-HiChIP purified DNA concentration by Qubit")
```
````
**Gemini 3.1 Pro Preview**

````text
```python
elution_mix = f"{washed_ip_beads} + {dna_elution_buffer}"
thermomixed_elution = set_thermal_mixer(sample=elution_mix, temperature_c=65.0, speed_rpm=900, duration_min=30.0)

combined_eluate = f"combined 600 uL eluate of {thermomixed_elution}"

crosslink_mix = f"{combined_eluate} + {proteinase_k_digest_mix}"
digested_sample = incubate_sample(sample=crosslink_mix, temperature_c=55.0, duration_min=960.0, condition="static")

prepared_maxtract = centrifuge_sample(sample=maxtract_tube, speed_xg=16000, duration_min=0.5, temperature_c=25.0)

extraction_mix = f"{digested_sample} + {prepared_maxtract} + {organic_extraction_mix}"
vigorously_mixed = mix_sample(sample=extraction_mix, method="vigorous", duration_s=15.0, speed="high")
phase_separated = centrifuge_sample(sample=vigorously_mixed, speed_xg=16000, duration_min=5.0, temperature_c=25.0)

precipitation_mix = f"aqueous phase of {phase_separated} + {dna_precipitation_mix}"
precipitated_dna = store_sample(sample=precipitation_mix, temperature_c=-20.0, duration_h=16.0, container="tube")

pellet = centrifuge_sample(sample=precipitated_dna, speed_xg=16000, duration_min=30.0, temperature_c=4.0)

ethanol_washed = f"ethanol washed {pellet}"
dried_pellet = dry_sample(sample=ethanol_washed, method="air dry", temperature_c=25.0, duration_min=5.0)

resuspension_mix = f"{dried_pellet} + {tris_resuspension_buffer}"
resuspended_dna = incubate_sample(sample=resuspension_mix, temperature_c=37.0, duration_min=60.0, condition="static")

qubit_reading = measure_signal(sample=resuspended_dna, assay="Qubit-style fluorometric assay", wavelength_nm=530, replicate_n=1)
recorded_conc = record_measurement(sample=qubit_reading, metric="concentration", unit="ng/uL", note="Purified BL-HiChIP DNA")
```
````
### level2_q0071：中位样例：三模型都有部分恢复能力
| 字段 | 内容 |
| --- | --- |
| protocol_id | star:PMC8844903 |
| protocol_title | Isolation and feeder-free primary culture of four cell types from a single human skin sample |
| gold_step_count | 9 |
| window_families | centrifuge, incubate, mix, separate, transfer, wash |
| source_step_indices | 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34 |
| 模型 | Strict Final | Relaxed Final | 解析状态 |
| --- | --- | --- | --- |
| GPT-5.4 | 0.0 | 0.402778 | valid |
| Claude Opus 4.7 | 0.0 | 0.295833 | valid |
| Gemini 3.1 Pro Preview | 0.0 | 0.397222 | valid |
#### 原题输入（英文原文）
**Background**

````text
Adult human skin has already been split into epidermal and dermal fractions for parallel primary cell isolation. The current local stage focuses on the dermis-derived endothelial fraction: endothelial growth medium must be warmed, an Attachment Factor-coated flask must be readied and equilibrated, the extruded endothelial suspension in a 50 mL tube must be recovered by a cold gentle spin, and the recovered cells must be placed into primary culture. Epidermal strips may be held cold only for a short same-day delay.
````
**Goal**

````text
Recover the dermal endothelial cell fraction and establish it in an equilibrated coated flask for overnight primary culture while preserving a short cold hold state for the epidermal strips.
````
**Constraints**

````text
- Warm ECGM to 37 C before using it for flask equilibration or pellet resuspension.
- Attachment Factor coating on the T75 flask requires 30 min at 37 C, with no rinse afterward, followed by addition of 15 mL ECGM and at least 30 min equilibration at 37 C.
- The dermis-derived endothelial suspension in the 50 mL conical must be centrifuged at about 250 x g for 7 min at 4 C.
- Treat the post-spin pellet as fragile and resuspend it gently in 2 mL ECGM per T75 flask before inoculation.
- After inoculation, incubate the endothelial culture overnight for about 16 h at 37 C under a humidified 5% CO2 condition.
- Include a temporary 4 C storage state for the epidermal strips for same-day processing rather than overnight.
- Use repeated action families and keep later steps dependent on outputs from earlier ones.
````
**Available Raw Inputs**

````text
- ecgm_media: Endothelial cell growth medium prepared for HDMEC culture
- attachment_factor_t75: Uncoated T75 flask intended for endothelial culture coating
- extruded_hdmec_suspension_50ml: Dermis-derived endothelial cell suspension collected in a 50 mL conical tube
- epidermal_strips_hbs: Epidermal strips held in HBS pending same-day keratinocyte isolation
````
**Action Pool Code**

```python
def centrifuge_sample(sample: str, speed_xg: int, duration_min: float, temperature_c: float) -> str:
    """Centrifuge a sample at a defined speed, duration, and temperature.

    Args:
        sample: Sample or tube placed in the centrifuge.
        speed_xg: Relative centrifugal force in x g.
        duration_min: Spin time in minutes.
        temperature_c: Centrifuge chamber temperature in Celsius.
    Returns:
        A handle for the centrifuged sample.
    """
    pass


def incubate_sample(sample: str, temperature_c: float, duration_min: float, condition: str) -> str:
    """Incubate a sample under a defined temperature and condition.

    Args:
        sample: Sample placed into incubation.
        temperature_c: Incubation temperature in Celsius.
        duration_min: Incubation time in minutes.
        condition: Condition such as static, shaking, protected from light, or humidified.
    Returns:
        A handle for the incubated sample.
    """
    pass


def heat_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Heat a sample on a named device or heat source.

    Args:
        sample: Sample being heated.
        temperature_c: Target temperature in Celsius.
        duration_min: Heating time in minutes.
        device: Heating device or bath used in the step.
    Returns:
        A handle for the heated sample.
    """
    pass


def cool_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Cool or chill a sample to a target temperature.

    Args:
        sample: Sample being cooled.
        temperature_c: Target cooling temperature in Celsius.
        duration_min: Cooling time in minutes.
        device: Cooling device such as ice bath, refrigerator, or freezer.
    Returns:
        A handle for the cooled sample.
    """
    pass


def set_thermal_mixer(sample: str, temperature_c: float, speed_rpm: int, duration_min: float) -> str:
    """Process a sample in a thermal mixer with specified temperature and agitation.

    Args:
        sample: Sample loaded into the thermal mixer.
        temperature_c: Temperature setting in Celsius.
        speed_rpm: Mixing speed in RPM.
        duration_min: Program duration in minutes.
    Returns:
        A handle for the thermomixed sample.
    """
    pass


def run_thermal_cycler(plate: str, program_name: str, cycles: int, lid_temperature_c: float) -> str:
    """Run a thermal cycler program on a loaded plate or tube strip.

    Args:
        plate: Loaded plate or strip processed by the cycler.
        program_name: Program identifier or stage name.
        cycles: Number of program cycles.
        lid_temperature_c: Heated lid temperature in Celsius.
    Returns:
        A handle for the thermocycled product.
    """
    pass


def dry_sample(sample: str, method: str, temperature_c: float, duration_min: float) -> str:
    """Dry a sample under a defined method and temperature.

    Args:
        sample: Sample being dried.
        method: Drying method such as air dry, oven dry, or vacuum dry.
        temperature_c: Drying temperature in Celsius.
        duration_min: Drying time in minutes.
    Returns:
        A handle for the dried sample.
    """
    pass


def store_sample(sample: str, temperature_c: float, duration_h: float, container: str) -> str:
    """Store a processed sample for later use.

    Args:
        sample: Sample being stored.
        temperature_c: Storage temperature in Celsius.
        duration_h: Storage duration in hours.
        container: Storage vessel or storage location.
    Returns:
        A handle for the stored sample.
    """
    pass


def mix_sample(sample: str, method: str, duration_s: float, speed: str) -> str:
    """Mix a sample using a generic laboratory method.

    Args:
        sample: Sample being mixed.
        method: Mixing method such as inversion, pipetting, or rocking.
        duration_s: Mixing duration in seconds.
        speed: Speed setting or qualitative speed description.
    Returns:
        A handle for the mixed sample.
    """
    pass


def vortex_mix(sample: str, duration_s: float, speed_rpm: int, temperature_c: float) -> str:
    """Mix a sample on a vortex mixer.

    Args:
        sample: Sample placed on the vortex mixer.
        duration_s: Vortex duration in seconds.
        speed_rpm: Mixer speed in RPM.
        temperature_c: Ambient or controlled temperature during mixing.
    Returns:
        A handle for the vortexed sample.
    """
    pass


def stir_with_rod(container: str, duration_s: float, speed_desc: str, temperature_c: float) -> str:
    """Stir a liquid sample with a glass rod or stirring tool.

    Args:
        container: Container holding the liquid to stir.
        duration_s: Stirring duration in seconds.
        speed_desc: Qualitative stirring intensity.
        temperature_c: Sample temperature during stirring.
    Returns:
        A handle for the stirred sample.
    """
    pass


def shake_container(sample: str, amplitude_mm: float, repeat_n: int, duration_s: float) -> str:
    """Shake a closed vessel for coarse liquid mixing.

    Args:
        sample: Sample or vessel being shaken.
        amplitude_mm: Shake amplitude in millimeters.
        repeat_n: Number of shake repetitions or cycles.
        duration_s: Total shaking duration in seconds.
    Returns:
        A handle for the shaken sample.
    """
    pass


def filter_sample(sample: str, filter_type: str, pore_size_um: float, destination: str) -> str:
    """Filter a sample through a filter or membrane into a destination vessel.

    Args:
        sample: Input sample passed through the filter.
        filter_type: Filter medium or membrane type.
        pore_size_um: Filter pore size in micrometers.
        destination: Destination vessel after filtration.
    Returns:
        A handle for the filtered sample.
    """
    pass


def magnetic_separate(sample: str, rack: str, duration_min: float, collect_phase: str) -> str:
    """Separate a bead-based sample on a magnetic rack.

    Args:
        sample: Sample containing magnetic beads.
        rack: Magnetic rack identifier.
        duration_min: Magnetic separation time in minutes.
        collect_phase: Phase to retain after separation.
    Returns:
        A handle for the magnetically separated sample.
    """
    pass
```
**Gold Program**

```python
warmed_ecgm_media = heat_sample(sample=ecgm_media, temperature_c=37.0, duration_min=20.0, device='water bath')
coated_t75 = incubate_sample(sample=attachment_factor_t75, temperature_c=37.0, duration_min=30.0, condition='static sealed with Attachment Factor')
equilibrated_t75 = incubate_sample(sample=coated_t75, temperature_c=37.0, duration_min=30.0, condition='static with 15 mL warmed ECGM')
held_epidermis = store_sample(sample=epidermal_strips_hbs, temperature_c=4.0, duration_h=3.0, container='refrigerator dish')
rinsed_hdmec_suspension = mix_sample(sample=extruded_hdmec_suspension_50ml, method='pipetting with ECGM rinse combined in tube', duration_s=20.0, speed='gentle')
spun_hdmec_pellet = centrifuge_sample(sample=rinsed_hdmec_suspension, speed_xg=250, duration_min=7.0, temperature_c=4.0)
resuspended_hdmec_cells = mix_sample(sample=spun_hdmec_pellet, method='pipetting in 2 mL warmed ECGM', duration_s=15.0, speed='gentle')
inoculated_t75 = mix_sample(sample=equilibrated_t75, method='add 2 mL HDMEC suspension', duration_s=10.0, speed='gentle')
overnight_hdmec_culture = incubate_sample(sample=inoculated_t75, temperature_c=37.0, duration_min=960.0, condition='humidified 5% CO2 static')
```
#### 模型回答（原始输出）
**GPT-5.4**

````text
```python
warmed_ecgm_media = heat_sample(
    sample="ecgm_media",
    temperature_c=37.0,
    duration_min=30.0,
    device="water bath"
)

attachment_factor_coated_t75 = incubate_sample(
    sample="attachment_factor_t75",
    temperature_c=37.0,
    duration_min=30.0,
    condition="static Attachment Factor coating"
)

equilibrated_attachment_factor_t75 = incubate_sample(
    sample=f"{attachment_factor_coated_t75} + 15 mL of {warmed_ecgm_media}",
    temperature_c=37.0,
    duration_min=30.0,
    condition="static ECGM equilibration"
)

cold_held_epidermal_strips = store_sample(
    sample="epidermal_strips_hbs",
    temperature_c=4.0,
    duration_h=4.0,
    container="refrigerator"
)

spun_extruded_hdmec_suspension = centrifuge_sample(
    sample="extruded_hdmec_suspension_50ml",
    speed_xg=250,
    duration_min=7.0,
    temperature_c=4.0
)

gently_resuspended_hdmec_pellet = mix_sample(
    sample=f"{spun_extruded_hdmec_suspension} pellet in 2 mL {warmed_ecgm_media}",
    method="pipetting",
    duration_s=20.0,
    speed="gentle"
)

inoculated_endothelial_primary_culture = incubate_sample(
    sample=f"{equilibrated_attachment_factor_t75} inoculated with {gently_resuspended_hdmec_pellet}",
    temperature_c=37.0,
    duration_min=960.0,
    condition="humidified 5% CO2"
)
```
````
**Claude Opus 4.7**

````text
```python
# Warm ECGM to 37 C
warmed_ecgm = heat_sample(sample="ecgm_media", temperature_c=37.0, duration_min=15.0, device="water_bath")

# Cold hold for epidermal strips (short same-day 4 C storage)
epidermal_cold_hold = store_sample(sample="epidermal_strips_hbs", temperature_c=4.0, duration_h=2.0, container="refrigerator_4C")

# Coat T75 flask with Attachment Factor: 30 min at 37 C
coated_flask = incubate_sample(sample="attachment_factor_t75", temperature_c=37.0, duration_min=30.0, condition="humidified")

# Add 15 mL warmed ECGM to the coated flask and equilibrate at 37 C for >= 30 min
flask_with_ecgm = mix_sample(sample=coated_flask + "+" + warmed_ecgm + "_15mL", method="pipetting", duration_s=20.0, speed="gentle")
equilibrated_flask = incubate_sample(sample=flask_with_ecgm, temperature_c=37.0, duration_min=30.0, condition="humidified_5pct_CO2")

# Cold gentle spin of the extruded endothelial suspension: ~250 x g, 7 min, 4 C
chilled_suspension = cool_sample(sample="extruded_hdmec_suspension_50ml", temperature_c=4.0, duration_min=5.0, device="ice_bath")
spun_suspension = centrifuge_sample(sample=chilled_suspension, speed_xg=250, duration_min=7.0, temperature_c=4.0)

# Gentle resuspension of fragile pellet in 2 mL warmed ECGM
resuspended_pellet = mix_sample(sample=spun_suspension + "+" + warmed_ecgm + "_2mL", method="pipetting", duration_s=15.0, speed="gentle")

# Inoculate equilibrated flask with the resuspended endothelial cells
inoculated_flask = mix_sample(sample=equilibrated_flask + "+" + resuspended_pellet, method="pipetting", duration_s=10.0, speed="gentle")

# Overnight primary culture ~16 h at 37 C, humidified 5% CO2
overnight_culture = incubate_sample(sample=inoculated_flask, temperature_c=37.0, duration_min=960.0, condition="humidified_5pct_CO2")
```
````
**Gemini 3.1 Pro Preview**

````text
```python
warmed_ecgm = heat_sample(
    sample="ecgm_media",
    temperature_c=37.0,
    duration_min=30.0,
    device="water bath"
)

coated_flask = incubate_sample(
    sample="attachment_factor_t75",
    temperature_c=37.0,
    duration_min=30.0,
    condition="static"
)

equilibrated_flask = incubate_sample(
    sample=f"{coated_flask} with 15 mL {warmed_ecgm}",
    temperature_c=37.0,
    duration_min=30.0,
    condition="static"
)

spun_endo_suspension = centrifuge_sample(
    sample="extruded_hdmec_suspension_50ml",
    speed_xg=250,
    duration_min=7.0,
    temperature_c=4.0
)

resuspended_endo_cells = mix_sample(
    sample=f"pellet from {spun_endo_suspension} + 2 mL {warmed_ecgm}",
    method="pipetting",
    duration_s=60.0,
    speed="gentle"
)

inoculated_culture = mix_sample(
    sample=f"{resuspended_endo_cells} transferred to {equilibrated_flask}",
    method="rocking",
    duration_s=15.0,
    speed="gentle"
)

final_incubated_culture = incubate_sample(
    sample=inoculated_culture,
    temperature_c=37.0,
    duration_min=960.0,
    condition="humidified 5% CO2"
)

stored_epidermal_strips = store_sample(
    sample="epidermal_strips_hbs",
    temperature_c=4.0,
    duration_h=4.0,
    container="refrigerator"
)
```
````
### level2_q0041：分歧样例：GPT 明显低于 Claude / Gemini
| 字段 | 内容 |
| --- | --- |
| protocol_id | star:PMC11419825 |
| protocol_title | Protocol to identify receptors of secreted proteins through CRISPR-Cas9 whole-genome screening technology |
| gold_step_count | 13 |
| window_families | centrifuge, incubate, measure, mix, separate, transfer, wash |
| source_step_indices | 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 36 |
| 模型 | Strict Final | Relaxed Final | 解析状态 |
| --- | --- | --- | --- |
| GPT-5.4 | 0.0 | 0.22476 | valid |
| Claude Opus 4.7 | 0.5 | 0.875 | valid |
| Gemini 3.1 Pro Preview | 0.5 | 0.875 | valid |
#### 原题输入（英文原文）
**Background**

````text
Following flow-cytometry enrichment, the GFP-negative experimental cells have been collected and need to be pelleted, preserved, and processed for genomic DNA recovery. At this stage, the task is the local genomic DNA extraction workflow for the sorted-cell fraction using a silica spin-column style cleanup before downstream sgRNA amplification and sequencing preparation.
````
**Goal**

````text
Prepare genomic DNA from the sorted GFP-negative cell fraction, including pellet handling, lysis, column-based cleanup, elution, concentration measurement, and frozen storage.
````
**Constraints**

````text
- Use the sorted GFP-negative cells as the starting material and include the post-sort pelleting condition of 500 x g for 10 min.
- The cell pellet must be stored at -80 C before the extraction workflow proceeds.
- Model the early extraction stage as a lysis setup followed by a 10 min incubation after addition of PBS, RNase A, and Proteinase K.
- After lysis buffer treatment, include a 65 C heating step for 15 min using a water-bath style device.
- Before the first column-binding spin, represent thorough mixing after ethanol addition.
- The column cleanup must include repeated high-speed spins at 12000 x g, with three 1 min spins associated with binding and wash handling plus one 2 min dry spin.
- Include a room-temperature elution wait of 3 min before the final 12000 x g recovery spin.
- Measure genomic DNA concentration with a Nanodrop-like absorbance readout and then store the purified DNA at -20 C.
- Use only action-pool functions and keep the program within 7 to 13 top-level function calls.
````
**Available Raw Inputs**

````text
- sorted_gfp_negative_cells: Experimental GFP-negative cells collected by flow sorting for genomic DNA extraction.
- lysis_mix: Mini-prep lysis setup corresponding to PBS, RNase A, and Proteinase K addition.
- buffer_dl: Buffer DL used for genomic DNA extraction lysis.
- ethanol_binding_state: Sample state after ethanol addition before loading to the silica column.
- buffer_ae: Elution buffer AE for genomic DNA recovery.
````
**Action Pool Code**

```python
def centrifuge_sample(sample: str, speed_xg: int, duration_min: float, temperature_c: float) -> str:
    """Centrifuge a sample at a defined speed, duration, and temperature.

    Args:
        sample: Sample or tube placed in the centrifuge.
        speed_xg: Relative centrifugal force in x g.
        duration_min: Spin time in minutes.
        temperature_c: Centrifuge chamber temperature in Celsius.
    Returns:
        A handle for the centrifuged sample.
    """
    pass


def incubate_sample(sample: str, temperature_c: float, duration_min: float, condition: str) -> str:
    """Incubate a sample under a defined temperature and condition.

    Args:
        sample: Sample placed into incubation.
        temperature_c: Incubation temperature in Celsius.
        duration_min: Incubation time in minutes.
        condition: Condition such as static, shaking, protected from light, or humidified.
    Returns:
        A handle for the incubated sample.
    """
    pass


def heat_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Heat a sample on a named device or heat source.

    Args:
        sample: Sample being heated.
        temperature_c: Target temperature in Celsius.
        duration_min: Heating time in minutes.
        device: Heating device or bath used in the step.
    Returns:
        A handle for the heated sample.
    """
    pass


def cool_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Cool or chill a sample to a target temperature.

    Args:
        sample: Sample being cooled.
        temperature_c: Target cooling temperature in Celsius.
        duration_min: Cooling time in minutes.
        device: Cooling device such as ice bath, refrigerator, or freezer.
    Returns:
        A handle for the cooled sample.
    """
    pass


def set_thermal_mixer(sample: str, temperature_c: float, speed_rpm: int, duration_min: float) -> str:
    """Process a sample in a thermal mixer with specified temperature and agitation.

    Args:
        sample: Sample loaded into the thermal mixer.
        temperature_c: Temperature setting in Celsius.
        speed_rpm: Mixing speed in RPM.
        duration_min: Program duration in minutes.
    Returns:
        A handle for the thermomixed sample.
    """
    pass


def run_thermal_cycler(plate: str, program_name: str, cycles: int, lid_temperature_c: float) -> str:
    """Run a thermal cycler program on a loaded plate or tube strip.

    Args:
        plate: Loaded plate or strip processed by the cycler.
        program_name: Program identifier or stage name.
        cycles: Number of program cycles.
        lid_temperature_c: Heated lid temperature in Celsius.
    Returns:
        A handle for the thermocycled product.
    """
    pass


def dry_sample(sample: str, method: str, temperature_c: float, duration_min: float) -> str:
    """Dry a sample under a defined method and temperature.

    Args:
        sample: Sample being dried.
        method: Drying method such as air dry, oven dry, or vacuum dry.
        temperature_c: Drying temperature in Celsius.
        duration_min: Drying time in minutes.
    Returns:
        A handle for the dried sample.
    """
    pass


def store_sample(sample: str, temperature_c: float, duration_h: float, container: str) -> str:
    """Store a processed sample for later use.

    Args:
        sample: Sample being stored.
        temperature_c: Storage temperature in Celsius.
        duration_h: Storage duration in hours.
        container: Storage vessel or storage location.
    Returns:
        A handle for the stored sample.
    """
    pass


def measure_signal(sample: str, assay: str, wavelength_nm: int, replicate_n: int) -> str:
    """Measure a sample with an assay-specific readout.

    Args:
        sample: Sample or plate being measured.
        assay: Measurement assay or modality.
        wavelength_nm: Measurement wavelength in nanometers.
        replicate_n: Number of technical replicates included in the readout.
    Returns:
        A handle for the measurement result.
    """
    pass


def record_measurement(sample: str, metric: str, unit: str, note: str) -> str:
    """Record a derived metric or QC observation from a processed sample.

    Args:
        sample: Sample or output being documented.
        metric: Named metric being recorded.
        unit: Unit of the recorded metric.
        note: Short observation or QC note.
    Returns:
        A handle for the recorded measurement entry.
    """
    pass


def mix_sample(sample: str, method: str, duration_s: float, speed: str) -> str:
    """Mix a sample using a generic laboratory method.

    Args:
        sample: Sample being mixed.
        method: Mixing method such as inversion, pipetting, or rocking.
        duration_s: Mixing duration in seconds.
        speed: Speed setting or qualitative speed description.
    Returns:
        A handle for the mixed sample.
    """
    pass


def vortex_mix(sample: str, duration_s: float, speed_rpm: int, temperature_c: float) -> str:
    """Mix a sample on a vortex mixer.

    Args:
        sample: Sample placed on the vortex mixer.
        duration_s: Vortex duration in seconds.
        speed_rpm: Mixer speed in RPM.
        temperature_c: Ambient or controlled temperature during mixing.
    Returns:
        A handle for the vortexed sample.
    """
    pass


def stir_with_rod(container: str, duration_s: float, speed_desc: str, temperature_c: float) -> str:
    """Stir a liquid sample with a glass rod or stirring tool.

    Args:
        container: Container holding the liquid to stir.
        duration_s: Stirring duration in seconds.
        speed_desc: Qualitative stirring intensity.
        temperature_c: Sample temperature during stirring.
    Returns:
        A handle for the stirred sample.
    """
    pass


def shake_container(sample: str, amplitude_mm: float, repeat_n: int, duration_s: float) -> str:
    """Shake a closed vessel for coarse liquid mixing.

    Args:
        sample: Sample or vessel being shaken.
        amplitude_mm: Shake amplitude in millimeters.
        repeat_n: Number of shake repetitions or cycles.
        duration_s: Total shaking duration in seconds.
    Returns:
        A handle for the shaken sample.
    """
    pass
```
**Gold Program**

```python
pelleted_cells = centrifuge_sample(sample=sorted_gfp_negative_cells, speed_xg=500, duration_min=10, temperature_c=4)
frozen_pellet = store_sample(sample=pelleted_cells, temperature_c=-80, duration_h=1, container="freezer")
lysed_cells = incubate_sample(sample=lysis_mix, temperature_c=25, duration_min=10, condition="static")
heated_lysate = heat_sample(sample=buffer_dl, temperature_c=65, duration_min=15, device="water bath")
binding_mix = vortex_mix(sample=ethanol_binding_state, duration_s=5, speed_rpm=2500, temperature_c=25)
column_bound = centrifuge_sample(sample=binding_mix, speed_xg=12000, duration_min=1, temperature_c=25)
gw1_processed = centrifuge_sample(sample=column_bound, speed_xg=12000, duration_min=1, temperature_c=25)
gw2_processed = centrifuge_sample(sample=gw1_processed, speed_xg=12000, duration_min=1, temperature_c=25)
dry_column = centrifuge_sample(sample=gw2_processed, speed_xg=12000, duration_min=2, temperature_c=25)
elution_wait = incubate_sample(sample=buffer_ae, temperature_c=25, duration_min=3, condition="static")
eluted_dna = centrifuge_sample(sample=elution_wait, speed_xg=12000, duration_min=1, temperature_c=25)
dna_signal = measure_signal(sample=eluted_dna, assay="nanodrop", wavelength_nm=260, replicate_n=1)
stored_gdna = store_sample(sample=dna_signal, temperature_c=-20, duration_h=24, container="microcentrifuge tube")
```
#### 模型回答（原始输出）
**GPT-5.4**

````text
```python
pelleted_sorted_cells = centrifuge_sample(
    sample="sorted_gfp_negative_cells",
    speed_xg=500,
    duration_min=10,
    temperature_c=4
)

frozen_pellet = store_sample(
    sample=pelleted_sorted_cells,
    temperature_c=-80,
    duration_h=24,
    container="cell_pellet_tube"
)

lysis_setup = set_thermal_mixer(
    sample="cell_pellet_from_sorted_gfp_negative_cells + lysis_mix",
    temperature_c=25,
    speed_rpm=800,
    duration_min=10
)

buffer_dl_lysed = mix_sample(
    sample=f"{lysis_setup} + buffer_dl",
    method="pipetting",
    duration_s=30,
    speed="thorough"
)

heated_lysate = heat_sample(
    sample=buffer_dl_lysed,
    temperature_c=65,
    duration_min=15,
    device="water_bath"
)

ethanol_mixed_binding_state = vortex_mix(
    sample="ethanol_binding_state",
    duration_s=15,
    speed_rpm=2500,
    temperature_c=25
)

column_cleanup_processed = centrifuge_sample(
    sample=f"{heated_lysate} -> silica_spin_column with {ethanol_mixed_binding_state}; binding spin 1 min, wash spin 1 min, wash spin 1 min, dry spin 2 min, elute with buffer_ae after 3 min RT wait, recovery spin",
    speed_xg=12000,
    duration_min=6,
    temperature_c=25
)

nanodrop_readout = measure_signal(
    sample=column_cleanup_processed,
    assay="nanodrop_absorbance_dna",
    wavelength_nm=260,
    replicate_n=1
)

dna_concentration_record = record_measurement(
    sample=nanodrop_readout,
    metric="gDNA_concentration",
    unit="ng/uL",
    note="Purified genomic DNA concentration measured by Nanodrop-like absorbance readout."
)

stored_purified_gdna = store_sample(
    sample=column_cleanup_processed,
    temperature_c=-20,
    duration_h=168,
    container="purified_gdna_tube"
)
```
````
**Claude Opus 4.7**

````text
```python
pellet = centrifuge_sample(sample="sorted_gfp_negative_cells", speed_xg=500, duration_min=10.0, temperature_c=4.0)
stored_pellet = store_sample(sample=pellet, temperature_c=-80.0, duration_h=12.0, container="-80C freezer")
lysis_setup = incubate_sample(sample=stored_pellet + "+lysis_mix", temperature_c=25.0, duration_min=10.0, condition="static")
dl_heated = heat_sample(sample=lysis_setup + "+buffer_dl", temperature_c=65.0, duration_min=15.0, device="water bath")
etoh_mixed = vortex_mix(sample="ethanol_binding_state", duration_s=15.0, speed_rpm=2500, temperature_c=25.0)
bind_spin = centrifuge_sample(sample=etoh_mixed, speed_xg=12000, duration_min=1.0, temperature_c=25.0)
wash1_spin = centrifuge_sample(sample=bind_spin, speed_xg=12000, duration_min=1.0, temperature_c=25.0)
wash2_spin = centrifuge_sample(sample=wash1_spin, speed_xg=12000, duration_min=1.0, temperature_c=25.0)
dry_spin = centrifuge_sample(sample=wash2_spin, speed_xg=12000, duration_min=2.0, temperature_c=25.0)
elution_wait = incubate_sample(sample=dry_spin + "+buffer_ae", temperature_c=25.0, duration_min=3.0, condition="static")
eluted_dna = centrifuge_sample(sample=elution_wait, speed_xg=12000, duration_min=1.0, temperature_c=25.0)
conc = measure_signal(sample=eluted_dna, assay="Nanodrop absorbance", wavelength_nm=260, replicate_n=2)
stored_dna = store_sample(sample=eluted_dna, temperature_c=-20.0, duration_h=72.0, container="-20C freezer")
```
````
**Gemini 3.1 Pro Preview**

````text
```python
pellet = centrifuge_sample(
    sample="sorted_gfp_negative_cells",
    speed_xg=500,
    duration_min=10.0,
    temperature_c=4.0
)

stored_pellet = store_sample(
    sample=pellet,
    temperature_c=-80.0,
    duration_h=12.0,
    container="freezer"
)

lysis_incubation = incubate_sample(
    sample=stored_pellet + " + lysis_mix",
    temperature_c=25.0,
    duration_min=10.0,
    condition="static"
)

heated_lysate = heat_sample(
    sample=lysis_incubation + " + buffer_dl",
    temperature_c=65.0,
    duration_min=15.0,
    device="water-bath"
)

mixed_ethanol = vortex_mix(
    sample=heated_lysate + " + ethanol_binding_state",
    duration_s=15.0,
    speed_rpm=2000,
    temperature_c=25.0
)

bind_spin = centrifuge_sample(
    sample=mixed_ethanol,
    speed_xg=12000,
    duration_min=1.0,
    temperature_c=25.0
)

wash_1_spin = centrifuge_sample(
    sample=bind_spin,
    speed_xg=12000,
    duration_min=1.0,
    temperature_c=25.0
)

wash_2_spin = centrifuge_sample(
    sample=wash_1_spin,
    speed_xg=12000,
    duration_min=1.0,
    temperature_c=25.0
)

dry_spin = centrifuge_sample(
    sample=wash_2_spin,
    speed_xg=12000,
    duration_min=2.0,
    temperature_c=25.0
)

elution_wait = incubate_sample(
    sample=dry_spin + " + buffer_ae",
    temperature_c=25.0,
    duration_min=3.0,
    condition="static"
)

recovery_spin = centrifuge_sample(
    sample=elution_wait,
    speed_xg=12000,
    duration_min=1.0,
    temperature_c=25.0
)

dna_concentration = measure_signal(
    sample=recovery_spin,
    assay="absorbance (Nanodrop)",
    wavelength_nm=260,
    replicate_n=1
)

final_gDNA = store_sample(
    sample=recovery_spin,
    temperature_c=-20.0,
    duration_h=72.0,
    container="freezer"
)
```
````
### level2_q0074：高分样例：三模型都能较完整恢复程序
| 字段 | 内容 |
| --- | --- |
| protocol_id | star:PMC11465143 |
| protocol_title | Protocol for generating a 3D culture of epiblast stem cells |
| gold_step_count | 8 |
| window_families | centrifuge, incubate, mix, separate, transfer, wash |
| source_step_indices | 40, 41, 42, 43, 44, 45, 46, 47, 48, 49, 50, 51 |
| 模型 | Strict Final | Relaxed Final | 解析状态 |
| --- | --- | --- | --- |
| GPT-5.4 | 0.625 | 0.921875 | valid |
| Claude Opus 4.7 | 0.5 | 0.859375 | valid |
| Gemini 3.1 Pro Preview | 0.625 | 0.921875 | valid |
#### 原题输入（英文原文）
**Background**

````text
Mouse epiblast stem cell spheroids grown in Matrigel are being processed at the passaging stage. The current material has already been exposed to matrix-dissolving and dissociation reagents, and the remaining work focuses on the cold spin and wash cycle needed to recover small cell clumps suitable for replating.
````
**Goal**

````text
Process the dissociating 3D EpiSC suspension through the required recovery, wash, and pellet-loosening stage so that a replating-ready cell suspension is obtained for subsequent mixing with cold Matrigel.
````
**Constraints**

````text
- Include the initial 37 C incubation for 20 min after Matrigel breakup, and a second 37 C incubation for 4 min after TrypLE exposure.
- Use centrifugation at 300 x g for 4 min at 4 C for each required spin in this segment.
- Represent repeated pipette resuspension events with a mixing action, and preserve the idea that the pellet is washed after enzymatic dissociation before final recovery.
- The workflow should include three cold centrifugation events separated by reagent-driven mixing or incubation states.
- After the final spin, the pellet must be loosened and treated as the replating-ready material rather than jumping directly to plating medium addition.
- Do not include downstream Matrigel plating, well setup, freezing medium preparation, or storage.
- Maintain a single dependency chain where each new state comes from the previous processed sample.
````
**Available Raw Inputs**

````text
- matrigel_broken_suspension: 3D EpiSC material in dispase after Matrigel has been mechanically disrupted.
- eppendorf_tube: 1.5 mL tube used to hold the collected cell suspension.
- tryple_cell_mix: Collected cell pellet resuspended in 1 mL TrypLE.
- wash_buffer_cell_mix: Cell pellet resuspended in 1 mL wash buffer after enzymatic treatment.
````
**Action Pool Code**

```python
def centrifuge_sample(sample: str, speed_xg: int, duration_min: float, temperature_c: float) -> str:
    """Centrifuge a sample at a defined speed, duration, and temperature.

    Args:
        sample: Sample or tube placed in the centrifuge.
        speed_xg: Relative centrifugal force in x g.
        duration_min: Spin time in minutes.
        temperature_c: Centrifuge chamber temperature in Celsius.
    Returns:
        A handle for the centrifuged sample.
    """
    pass


def incubate_sample(sample: str, temperature_c: float, duration_min: float, condition: str) -> str:
    """Incubate a sample under a defined temperature and condition.

    Args:
        sample: Sample placed into incubation.
        temperature_c: Incubation temperature in Celsius.
        duration_min: Incubation time in minutes.
        condition: Condition such as static, shaking, protected from light, or humidified.
    Returns:
        A handle for the incubated sample.
    """
    pass


def heat_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Heat a sample on a named device or heat source.

    Args:
        sample: Sample being heated.
        temperature_c: Target temperature in Celsius.
        duration_min: Heating time in minutes.
        device: Heating device or bath used in the step.
    Returns:
        A handle for the heated sample.
    """
    pass


def cool_sample(sample: str, temperature_c: float, duration_min: float, device: str) -> str:
    """Cool or chill a sample to a target temperature.

    Args:
        sample: Sample being cooled.
        temperature_c: Target cooling temperature in Celsius.
        duration_min: Cooling time in minutes.
        device: Cooling device such as ice bath, refrigerator, or freezer.
    Returns:
        A handle for the cooled sample.
    """
    pass


def set_thermal_mixer(sample: str, temperature_c: float, speed_rpm: int, duration_min: float) -> str:
    """Process a sample in a thermal mixer with specified temperature and agitation.

    Args:
        sample: Sample loaded into the thermal mixer.
        temperature_c: Temperature setting in Celsius.
        speed_rpm: Mixing speed in RPM.
        duration_min: Program duration in minutes.
    Returns:
        A handle for the thermomixed sample.
    """
    pass


def run_thermal_cycler(plate: str, program_name: str, cycles: int, lid_temperature_c: float) -> str:
    """Run a thermal cycler program on a loaded plate or tube strip.

    Args:
        plate: Loaded plate or strip processed by the cycler.
        program_name: Program identifier or stage name.
        cycles: Number of program cycles.
        lid_temperature_c: Heated lid temperature in Celsius.
    Returns:
        A handle for the thermocycled product.
    """
    pass


def dry_sample(sample: str, method: str, temperature_c: float, duration_min: float) -> str:
    """Dry a sample under a defined method and temperature.

    Args:
        sample: Sample being dried.
        method: Drying method such as air dry, oven dry, or vacuum dry.
        temperature_c: Drying temperature in Celsius.
        duration_min: Drying time in minutes.
    Returns:
        A handle for the dried sample.
    """
    pass


def store_sample(sample: str, temperature_c: float, duration_h: float, container: str) -> str:
    """Store a processed sample for later use.

    Args:
        sample: Sample being stored.
        temperature_c: Storage temperature in Celsius.
        duration_h: Storage duration in hours.
        container: Storage vessel or storage location.
    Returns:
        A handle for the stored sample.
    """
    pass


def mix_sample(sample: str, method: str, duration_s: float, speed: str) -> str:
    """Mix a sample using a generic laboratory method.

    Args:
        sample: Sample being mixed.
        method: Mixing method such as inversion, pipetting, or rocking.
        duration_s: Mixing duration in seconds.
        speed: Speed setting or qualitative speed description.
    Returns:
        A handle for the mixed sample.
    """
    pass


def vortex_mix(sample: str, duration_s: float, speed_rpm: int, temperature_c: float) -> str:
    """Mix a sample on a vortex mixer.

    Args:
        sample: Sample placed on the vortex mixer.
        duration_s: Vortex duration in seconds.
        speed_rpm: Mixer speed in RPM.
        temperature_c: Ambient or controlled temperature during mixing.
    Returns:
        A handle for the vortexed sample.
    """
    pass


def stir_with_rod(container: str, duration_s: float, speed_desc: str, temperature_c: float) -> str:
    """Stir a liquid sample with a glass rod or stirring tool.

    Args:
        container: Container holding the liquid to stir.
        duration_s: Stirring duration in seconds.
        speed_desc: Qualitative stirring intensity.
        temperature_c: Sample temperature during stirring.
    Returns:
        A handle for the stirred sample.
    """
    pass


def shake_container(sample: str, amplitude_mm: float, repeat_n: int, duration_s: float) -> str:
    """Shake a closed vessel for coarse liquid mixing.

    Args:
        sample: Sample or vessel being shaken.
        amplitude_mm: Shake amplitude in millimeters.
        repeat_n: Number of shake repetitions or cycles.
        duration_s: Total shaking duration in seconds.
    Returns:
        A handle for the shaken sample.
    """
    pass


def filter_sample(sample: str, filter_type: str, pore_size_um: float, destination: str) -> str:
    """Filter a sample through a filter or membrane into a destination vessel.

    Args:
        sample: Input sample passed through the filter.
        filter_type: Filter medium or membrane type.
        pore_size_um: Filter pore size in micrometers.
        destination: Destination vessel after filtration.
    Returns:
        A handle for the filtered sample.
    """
    pass


def magnetic_separate(sample: str, rack: str, duration_min: float, collect_phase: str) -> str:
    """Separate a bead-based sample on a magnetic rack.

    Args:
        sample: Sample containing magnetic beads.
        rack: Magnetic rack identifier.
        duration_min: Magnetic separation time in minutes.
        collect_phase: Phase to retain after separation.
    Returns:
        A handle for the magnetically separated sample.
    """
    pass
```
**Gold Program**

```python
step1 = incubate_sample(sample=matrigel_broken_suspension, temperature_c=37, duration_min=20, condition="static")
step2 = centrifuge_sample(sample=step1, speed_xg=300, duration_min=4, temperature_c=4)
step3 = mix_sample(sample=tryple_cell_mix, method="pipetting", duration_s=10, speed="moderate")
step4 = incubate_sample(sample=step3, temperature_c=37, duration_min=4, condition="static")
step5 = centrifuge_sample(sample=step4, speed_xg=300, duration_min=4, temperature_c=4)
step6 = mix_sample(sample=wash_buffer_cell_mix, method="pipetting", duration_s=10, speed="moderate")
step7 = centrifuge_sample(sample=step6, speed_xg=300, duration_min=4, temperature_c=4)
step8 = mix_sample(sample=step7, method="pipetting", duration_s=5, speed="gentle")
```
#### 模型回答（原始输出）
**GPT-5.4**

````text
```python
incubated_dispase_suspension = incubate_sample(
    sample=matrigel_broken_suspension,
    temperature_c=37.0,
    duration_min=20.0,
    condition="static",
)

first_cold_spin = centrifuge_sample(
    sample=incubated_dispase_suspension,
    speed_xg=300,
    duration_min=4.0,
    temperature_c=4.0,
)

mixed_tryple_cell_mix = mix_sample(
    sample=tryple_cell_mix,
    method="pipetting",
    duration_s=20.0,
    speed="gentle",
)

second_37c_incubation = incubate_sample(
    sample=mixed_tryple_cell_mix,
    temperature_c=37.0,
    duration_min=4.0,
    condition="static",
)

second_cold_spin = centrifuge_sample(
    sample=second_37c_incubation,
    speed_xg=300,
    duration_min=4.0,
    temperature_c=4.0,
)

mixed_wash_buffer_cell_mix = mix_sample(
    sample=wash_buffer_cell_mix,
    method="pipetting",
    duration_s=20.0,
    speed="gentle",
)

third_cold_spin = centrifuge_sample(
    sample=mixed_wash_buffer_cell_mix,
    speed_xg=300,
    duration_min=4.0,
    temperature_c=4.0,
)

replating_ready_cell_suspension = mix_sample(
    sample=third_cold_spin,
    method="pipetting",
    duration_s=15.0,
    speed="gentle",
)
```
````
**Claude Opus 4.7**

````text
```python
# 1. Incubate matrigel-broken suspension at 37 C for 20 min (dispase digestion)
dispase_incubated = incubate_sample(sample="matrigel_broken_suspension", temperature_c=37.0, duration_min=20.0, condition="humidified")

# 2. First cold spin to collect cells
first_pellet = centrifuge_sample(sample=dispase_incubated, speed_xg=300, duration_min=4.0, temperature_c=4.0)

# 3. Resuspend pellet in TrypLE (represented by mixing) -> tryple_cell_mix
tryple_resuspended = mix_sample(sample="tryple_cell_mix", method="pipetting", duration_s=30.0, speed="gentle")

# 4. Incubate at 37 C for 4 min for TrypLE dissociation
tryple_incubated = incubate_sample(sample=tryple_resuspended, temperature_c=37.0, duration_min=4.0, condition="static")

# 5. Second cold spin after enzymatic dissociation
second_pellet = centrifuge_sample(sample=tryple_incubated, speed_xg=300, duration_min=4.0, temperature_c=4.0)

# 6. Wash: resuspend pellet in wash buffer
wash_resuspended = mix_sample(sample="wash_buffer_cell_mix", method="pipetting", duration_s=30.0, speed="gentle")

# 7. Third cold spin to recover washed pellet
third_pellet = centrifuge_sample(sample=wash_resuspended, speed_xg=300, duration_min=4.0, temperature_c=4.0)

# 8. Loosen the final pellet to obtain replating-ready small clumps
replating_ready_suspension = mix_sample(sample=third_pellet, method="pipetting", duration_s=15.0, speed="gentle")
```
````
**Gemini 3.1 Pro Preview**

````text
```python
# Step 1: Initial 37 C incubation for 20 min after Matrigel breakup
incubated_matrigel = incubate_sample(
    sample=matrigel_broken_suspension,
    temperature_c=37.0,
    duration_min=20.0,
    condition='static'
)

# Step 2: First cold spin to collect the cells
spin_1 = centrifuge_sample(
    sample=incubated_matrigel,
    speed_xg=300,
    duration_min=4.0,
    temperature_c=4.0
)

# Step 3: Resuspension in TrypLE (reagent-driven mixing via pipetting)
tryple_resuspended = mix_sample(
    sample=spin_1,
    method='pipetting',
    duration_s=15.0,
    speed='moderate'
)

# Step 4: Second 37 C incubation for 4 min after TrypLE exposure
incubated_tryple = incubate_sample(
    sample=tryple_resuspended,
    temperature_c=37.0,
    duration_min=4.0,
    condition='static'
)

# Step 5: Second cold spin to pellet after enzymatic dissociation
spin_2 = centrifuge_sample(
    sample=incubated_tryple,
    speed_xg=300,
    duration_min=4.0,
    temperature_c=4.0
)

# Step 6: Resuspension in wash buffer (pellet washing step via pipetting)
wash_resuspended = mix_sample(
    sample=spin_2,
    method='pipetting',
    duration_s=15.0,
    speed='moderate'
)

# Step 7: Third cold spin to recover the final washed pellet
spin_3 = centrifuge_sample(
    sample=wash_resuspended,
    speed_xg=300,
    duration_min=4.0,
    temperature_c=4.0
)

# Step 8: Loosen the final pellet via pipetting (treated as replating-ready material)
replating_ready_cells = mix_sample(
    sample=spin_3,
    method='pipetting',
    duration_s=10.0,
    speed='gentle'
)
```
````
