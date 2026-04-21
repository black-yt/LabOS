# 实验室条目总览

这个目录不再只围绕单个对象组织，而是统一收拢 `AutoBio` 与 `LabUtopia` 中适合 benchmark 复用的实验室条目，包括独立对象、组合对象、场景内对象引用、完整场景，以及少量仍然有参考价值的场景相关文件。

当前公开维护的核心产物有四类；另外，本地生成时还会额外产出 protocol 匹配结果文件，默认不纳入版本控制。

- `README.md`：总览、分类规则、可视化清单
- `benchmark_core_inventory.json`：机器可读的核心条目清单
- `preview_manifest.json`：预览图索引
- `previews/`：脚本生成的预览图
- `protocol_min_v1_with_inventory.jsonl` / `protocol_min_v1_inventory_matches.jsonl` / `protocol_min_v1_inventory_matches.stats.json`：本地生成的 protocol 匹配结果

## 1. 总览

| 来源仓库 | 组织方式 | 当前可见层级 | 核心条目数 | 主要路径 |
| --- | --- | --- | --- | --- |
| AutoBio | 对象优先，兼有完整 MuJoCo XML 场景 | 独立对象 25<br>组合对象 34<br>完整场景 19 | 40 | [assets/](files/autobio/autobio/assets)<br>[model/](files/autobio/autobio/model) |
| LabUtopia | 场景优先，核心文件是 USD 场景 | 场景内对象引用 11<br>完整场景 5<br>场景相关文件 3 | 13 | [chemistry_lab/](files/labutopia/assets/chemistry_lab) |

```mermaid
flowchart LR
    A[AutoBio] --> A1[独立对象]
    A --> A2[组合对象]
    A --> A3[完整场景]
    B[LabUtopia] --> B1[场景内对象引用]
    B --> B2[完整场景]
    B --> B3[场景相关文件]
    A1 --> C[合并后的实验室条目总表]
    A2 --> C
    A3 --> C
    B1 --> C
    B2 --> C
    B3 --> C
    C --> D[核心条目 53 项]
```

当前核心条目共 53 项，其中 `AutoBio` 40 项，`LabUtopia` 13 项。

## 2. 统一口径

这里统一使用“实验室条目”作为总称，不再把所有东西都叫作 asset。判断规则如下：

| 标识 | 中文解释 | 是否独立文件 | 典型路径 |
| --- | --- | --- | --- |
| `scene` | 完整场景入口，加载后看到的是整张实验台、整台设备或整个实验室。 | 是 | [lab.xml](files/autobio/autobio/model/scene/lab.xml)<br>[lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| `standalone_mesh_root` | 独立对象的 mesh 根入口，通常对应单个对象或单个对象目录。 | 是 | [pcr_plate_96well_vis.obj](files/autobio/autobio/assets/container/pcr_plate_96well_vis.obj) |
| `package_entrypoint` | 组合对象入口，会继续引用多个部件、材质或子文件。 | 是 | [centrifuge_eppendorf_5430.xml](files/autobio/autobio/model/instrument/centrifuge_eppendorf_5430.xml) |
| `scene_prim_reference` | 场景内对象引用，依附在某个 USD 场景里，本身不是独立文件。 | 否 | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd)<br><code>#/World/conical_bottle02</code> |

补充说明：`LabUtopia` 的很多对象当前仍然是“场景里的对象引用”，所以预览图使用的是场景缩略图叠加对象标签，而不是把对象单独拆出来后的独立渲染。

## 3. 上游结构

- `AutoBio` 的主脉络是 `autobio/assets/` + `autobio/model/`。前者更偏原始对象与部件，后者更偏装配入口、仪器入口、机器人入口与完整场景入口。
- `LabUtopia` 的主脉络是 `assets/chemistry_lab/`。它本质上更偏 scene-first，很多对象只能通过 `xxx.usd#/World/...` 这种场景内路径来引用。
- 因此两者合并时，不能只看独立对象；必须把场景、场景内对象引用和组合对象一起纳入统一清单。

## 4. 全部资产 / 场景

这一章展示的是上游范围内所有值得盘点和可视化的条目，不等于最终全部纳入 benchmark。少数上游条目如果缺失 mesh 或存在坏引用，会回退到本地代理预览或信息卡，不再保留失败 placeholder。

### 4.1 场景内对象引用

| 预览 | 来源 | 名称 | 代表路径 | 所在场景 |
| --- | --- | --- | --- | --- |
| <img src="previews/labutopia/scene_objects/cabinet.png" width="200" alt="cabinet"> | LabUtopia | cabinet | <code>/World/Cabinet_01</code><br><code>/World/Cabinet_02</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/drying-box.png" width="200" alt="drying box"> | LabUtopia | drying box | <code>/World/DryingBox_01</code><br><code>/World/DryingBox_02</code><br><code>/World/DryingBox_03</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/button.png" width="200" alt="button"> | LabUtopia | button | <code>/World/DryingBox_01/button</code><br><code>/World/heat_device/button</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/beaker.png" width="200" alt="beaker"> | LabUtopia | beaker | <code>/World/beaker1</code><br><code>/World/beaker2</code><br><code>/World/beaker3</code><br><code>/World/beaker_2</code><br><code>/World/target_beaker</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/conical-bottle.png" width="200" alt="conical bottle"> | LabUtopia | conical bottle | <code>/World/conical_bottle02</code><br><code>/World/conical_bottle03</code><br><code>/World/conical_bottle04</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/glass-rod.png" width="200" alt="glass rod"> | LabUtopia | glass rod | <code>/World/glass_rod</code> | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd) |
| <img src="previews/labutopia/scene_objects/graduated-cylinder.png" width="200" alt="graduated cylinder"> | LabUtopia | graduated cylinder | <code>/World/graduated_cylinder_03</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/heat-device.png" width="200" alt="heat device"> | LabUtopia | heat device | <code>/World/heat_device</code> | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd) |
| <img src="previews/labutopia/scene_objects/muffle-furnace.png" width="200" alt="muffle furnace"> | LabUtopia | muffle furnace | <code>/World/MuffleFurnace</code> | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/labutopia/scene_objects/rack-platform.png" width="200" alt="rack / platform"> | LabUtopia | rack / platform | <code>/World/target_plat</code> | [Scene1_hard.usd](files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd) |
| <img src="previews/labutopia/scene_objects/table-surface.png" width="200" alt="table surface"> | LabUtopia | table surface | <code>/World/table/surface</code><br><code>/World/table/surface/mesh</code> | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd) |

### 4.2 独立对象

| 预览 | 来源 | 名称 | 路径 |
| --- | --- | --- | --- |
| <img src="previews/autobio/standalone/cell-dish-100-vis.png" width="200" alt="cell_dish_100_vis"> | AutoBio | cell_dish_100_vis | [cell_dish_100_vis.obj](files/autobio/autobio/assets/container/cell_dish_100_vis.obj) |
| <img src="previews/autobio/standalone/centrifuge-1-5ml-screw-vis.png" width="200" alt="centrifuge_1-5ml_screw_vis"> | AutoBio | centrifuge_1-5ml_screw_vis | [centrifuge_1-5ml_screw_vis/](files/autobio/autobio/assets/container/centrifuge_1-5ml_screw_vis) |
| <img src="previews/autobio/standalone/centrifuge-10ml-vis.png" width="200" alt="centrifuge_10ml_vis"> | AutoBio | centrifuge_10ml_vis | [centrifuge_10ml_vis.obj](files/autobio/autobio/assets/container/centrifuge_10ml_vis.obj) |
| <img src="previews/autobio/standalone/centrifuge-1500ul-no-lid-vis.png" width="200" alt="centrifuge_1500ul_no_lid_vis"> | AutoBio | centrifuge_1500ul_no_lid_vis | [centrifuge_1500ul_no_lid_vis.obj](files/autobio/autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj) |
| <img src="previews/autobio/standalone/centrifuge-15ml-screw-vis.png" width="200" alt="centrifuge_15ml_screw_vis"> | AutoBio | centrifuge_15ml_screw_vis | [centrifuge_15ml_screw_vis/](files/autobio/autobio/assets/container/centrifuge_15ml_screw_vis) |
| <img src="previews/autobio/standalone/centrifuge-50ml-vis.png" width="200" alt="centrifuge_50ml_vis"> | AutoBio | centrifuge_50ml_vis | [centrifuge_50ml_vis.obj](files/autobio/autobio/assets/container/centrifuge_50ml_vis.obj) |
| <img src="previews/autobio/standalone/centrifuge-50ml-screw-vis.png" width="200" alt="centrifuge_50ml_screw_vis"> | AutoBio | centrifuge_50ml_screw_vis | [centrifuge_50ml_screw_vis/](files/autobio/autobio/assets/container/centrifuge_50ml_screw_vis) |
| <img src="previews/autobio/standalone/cryovial-1-8ml-vis.png" width="200" alt="cryovial_1-8ml_vis"> | AutoBio | cryovial_1-8ml_vis | [cryovial_1-8ml_vis/](files/autobio/autobio/assets/container/cryovial_1-8ml_vis) |
| <img src="previews/autobio/standalone/pcr-plate-96well-vis.png" width="200" alt="pcr_plate_96well_vis"> | AutoBio | pcr_plate_96well_vis | [pcr_plate_96well_vis.obj](files/autobio/autobio/assets/container/pcr_plate_96well_vis.obj) |
| <img src="previews/autobio/standalone/tip-200ul-vis.png" width="200" alt="tip_200ul_vis"> | AutoBio | tip_200ul_vis | [tip_200ul_vis/](files/autobio/autobio/assets/container/tip_200ul_vis) |
| <img src="previews/autobio/standalone/centrifuge-10slot-vis.png" width="200" alt="centrifuge_10slot_vis"> | AutoBio | centrifuge_10slot_vis | [centrifuge_10slot_vis.obj](files/autobio/autobio/assets/rack/centrifuge_10slot_vis.obj) |
| <img src="previews/autobio/standalone/centrifuge-plate-60well-vis.png" width="200" alt="centrifuge_plate_60well_vis"> | AutoBio | centrifuge_plate_60well_vis | [centrifuge_plate_60well_vis.obj](files/autobio/autobio/assets/rack/centrifuge_plate_60well_vis.obj) |
| <img src="previews/autobio/standalone/pipette-rack-tri-vis.png" width="200" alt="pipette_rack_tri_vis"> | AutoBio | pipette_rack_tri_vis | [pipette_rack_tri_vis.obj](files/autobio/autobio/assets/rack/pipette_rack_tri_vis.obj) |
| <img src="previews/autobio/standalone/tip-box-24slot-vis.png" width="200" alt="tip_box_24slot_vis"> | AutoBio | tip_box_24slot_vis | [tip_box_24slot_vis.obj](files/autobio/autobio/assets/rack/tip_box_24slot_vis.obj) |
| <img src="previews/autobio/standalone/pipette.png" width="200" alt="pipette"> | AutoBio | pipette | [pipette/](files/autobio/autobio/assets/tool/pipette) |
| <img src="previews/autobio/standalone/centrifuge-eppendorf-5430.png" width="200" alt="centrifuge_eppendorf_5430"> | AutoBio | centrifuge_eppendorf_5430 | [centrifuge_eppendorf_5430/](files/autobio/autobio/assets/instrument/centrifuge_eppendorf_5430) |
| <img src="previews/autobio/standalone/centrifuge-eppendorf-5910-ri.png" width="200" alt="centrifuge_eppendorf_5910_ri"> | AutoBio | centrifuge_eppendorf_5910_ri | [centrifuge_eppendorf_5910_ri/](files/autobio/autobio/assets/instrument/centrifuge_eppendorf_5910_ri) |
| <img src="previews/autobio/standalone/centrifuge-tiangen-tgear-mini.png" width="200" alt="centrifuge_tiangen_tgear_mini"> | AutoBio | centrifuge_tiangen_tgear_mini | [centrifuge_tiangen_tgear_mini/](files/autobio/autobio/assets/instrument/centrifuge_tiangen_tgear_mini) |
| <img src="previews/autobio/standalone/thermal-cycler-biorad-c1000.png" width="200" alt="thermal_cycler_biorad_c1000"> | AutoBio | thermal_cycler_biorad_c1000 | [thermal_cycler_biorad_c1000/](files/autobio/autobio/assets/instrument/thermal_cycler_biorad_c1000) |
| <img src="previews/autobio/standalone/thermal-mixer-eppendorf-c.png" width="200" alt="thermal_mixer_eppendorf_c"> | AutoBio | thermal_mixer_eppendorf_c | [thermal_mixer_eppendorf_c/](files/autobio/autobio/assets/instrument/thermal_mixer_eppendorf_c) |
| <img src="previews/autobio/standalone/vortex-mixer-genie-2.png" width="200" alt="vortex_mixer_genie_2"> | AutoBio | vortex_mixer_genie_2 | [vortex_mixer_genie_2/](files/autobio/autobio/assets/instrument/vortex_mixer_genie_2) |
| <img src="previews/autobio/standalone/aloha2.png" width="200" alt="aloha2"> | AutoBio | aloha2 | [aloha2/](files/autobio/autobio/assets/robot/aloha2) |
| <img src="previews/autobio/standalone/dexhand021.png" width="200" alt="dexhand021"> | AutoBio | dexhand021 | [dexhand021/](files/autobio/autobio/assets/robot/dexhand021) |
| <img src="previews/autobio/standalone/robotiq.png" width="200" alt="robotiq"> | AutoBio | robotiq | [robotiq/](files/autobio/autobio/assets/robot/robotiq) |
| <img src="previews/autobio/standalone/ur5e.png" width="200" alt="ur5e"> | AutoBio | ur5e | [ur5e/](files/autobio/autobio/assets/robot/ur5e) |

### 4.3 组合对象

| 预览 | 来源 | 类别 | 名称 | 路径 |
| --- | --- | --- | --- | --- |
| <img src="previews/autobio/composite/object-cell-dish-100.png" width="200" alt="cell_dish_100"> | AutoBio | 对象 | cell_dish_100 | [cell_dish_100.gen.xml](files/autobio/autobio/model/object/cell_dish_100.gen.xml)<br>[cell_dish_100.xml](files/autobio/autobio/model/object/cell_dish_100.xml) |
| <img src="previews/autobio/composite/object-centrifuge-1-5ml.png" width="200" alt="centrifuge_1-5ml"> | AutoBio | 对象 | centrifuge_1-5ml | [centrifuge_1-5ml.xml](files/autobio/autobio/model/object/centrifuge_1-5ml.xml) |
| <img src="previews/autobio/composite/object-centrifuge-1-5ml-screw.png" width="200" alt="centrifuge_1-5ml_screw"> | AutoBio | 对象 | centrifuge_1-5ml_screw | [centrifuge_1-5ml_screw.xml](files/autobio/autobio/model/object/centrifuge_1-5ml_screw.xml) |
| <img src="previews/autobio/composite/object-centrifuge-1-5ml-screw-simple.png" width="200" alt="centrifuge_1-5ml_screw-simple"> | AutoBio | 对象 | centrifuge_1-5ml_screw-simple | [centrifuge_1-5ml_screw-simple.xml](files/autobio/autobio/model/object/centrifuge_1-5ml_screw-simple.xml) |
| <img src="previews/autobio/composite/object-centrifuge-10ml.png" width="200" alt="centrifuge_10ml"> | AutoBio | 对象 | centrifuge_10ml | [centrifuge_10ml.gen.xml](files/autobio/autobio/model/object/centrifuge_10ml.gen.xml)<br>[centrifuge_10ml.xml](files/autobio/autobio/model/object/centrifuge_10ml.xml) |
| <img src="previews/autobio/composite/object-centrifuge-10slot.png" width="200" alt="centrifuge_10slot"> | AutoBio | 对象 | centrifuge_10slot | [centrifuge_10slot.gen.xml](files/autobio/autobio/model/object/centrifuge_10slot.gen.xml)<br>[centrifuge_10slot.xml](files/autobio/autobio/model/object/centrifuge_10slot.xml) |
| <img src="previews/autobio/composite/object-centrifuge-1500ul-no-lid.png" width="200" alt="centrifuge_1500ul_no_lid"> | AutoBio | 对象 | centrifuge_1500ul_no_lid | [centrifuge_1500ul_no_lid.gen.xml](files/autobio/autobio/model/object/centrifuge_1500ul_no_lid.gen.xml)<br>[centrifuge_1500ul_no_lid.xml](files/autobio/autobio/model/object/centrifuge_1500ul_no_lid.xml) |
| <img src="previews/autobio/composite/object-centrifuge-15ml.png" width="200" alt="centrifuge_15ml"> | AutoBio | 对象 | centrifuge_15ml | [centrifuge_15ml.xml](files/autobio/autobio/model/object/centrifuge_15ml.xml) |
| <img src="previews/autobio/composite/object-centrifuge-15ml-screw.png" width="200" alt="centrifuge_15ml_screw"> | AutoBio | 对象 | centrifuge_15ml_screw | [centrifuge_15ml_screw.xml](files/autobio/autobio/model/object/centrifuge_15ml_screw.xml) |
| <img src="previews/autobio/composite/object-centrifuge-50ml.png" width="200" alt="centrifuge_50ml"> | AutoBio | 对象 | centrifuge_50ml | [centrifuge_50ml.gen.xml](files/autobio/autobio/model/object/centrifuge_50ml.gen.xml)<br>[centrifuge_50ml.xml](files/autobio/autobio/model/object/centrifuge_50ml.xml) |
| <img src="previews/autobio/composite/object-centrifuge-50ml-screw.png" width="200" alt="centrifuge_50ml_screw"> | AutoBio | 对象 | centrifuge_50ml_screw | [centrifuge_50ml_screw.xml](files/autobio/autobio/model/object/centrifuge_50ml_screw.xml) |
| <img src="previews/autobio/composite/object-centrifuge-plate-60well.png" width="200" alt="centrifuge_plate_60well"> | AutoBio | 对象 | centrifuge_plate_60well | [centrifuge_plate_60well.gen.xml](files/autobio/autobio/model/object/centrifuge_plate_60well.gen.xml)<br>[centrifuge_plate_60well.xml](files/autobio/autobio/model/object/centrifuge_plate_60well.xml) |
| <img src="previews/autobio/composite/object-cryovial-1-8ml.png" width="200" alt="cryovial_1-8ml"> | AutoBio | 对象 | cryovial_1-8ml | [cryovial_1-8ml.xml](files/autobio/autobio/model/object/cryovial_1-8ml.xml) |
| <img src="previews/autobio/composite/object-pcr-plate-96well.png" width="200" alt="pcr_plate_96well"> | AutoBio | 对象 | pcr_plate_96well | [pcr_plate_96well.gen.xml](files/autobio/autobio/model/object/pcr_plate_96well.gen.xml)<br>[pcr_plate_96well.xml](files/autobio/autobio/model/object/pcr_plate_96well.xml) |
| <img src="previews/autobio/composite/object-pipette.png" width="200" alt="pipette"> | AutoBio | 对象 | pipette | [pipette.gen.xml](files/autobio/autobio/model/object/pipette.gen.xml)<br>[pipette.xml](files/autobio/autobio/model/object/pipette.xml) |
| <img src="previews/autobio/composite/object-pipette-rack.png" width="200" alt="pipette_rack"> | AutoBio | 对象 | pipette_rack | [pipette_rack.gen.xml](files/autobio/autobio/model/object/pipette_rack.gen.xml)<br>[pipette_rack.xml](files/autobio/autobio/model/object/pipette_rack.xml) |
| <img src="previews/autobio/composite/object-pipette-tip.png" width="200" alt="pipette_tip"> | AutoBio | 对象 | pipette_tip | [pipette_tip.gen.xml](files/autobio/autobio/model/object/pipette_tip.gen.xml)<br>[pipette_tip.xml](files/autobio/autobio/model/object/pipette_tip.xml) |
| <img src="previews/autobio/composite/object-tip-box.png" width="200" alt="tip_box"> | AutoBio | 对象 | tip_box | [tip_box.gen.xml](files/autobio/autobio/model/object/tip_box.gen.xml)<br>[tip_box.xml](files/autobio/autobio/model/object/tip_box.xml) |
| <img src="previews/autobio/composite/instrument-centrifuge-eppendorf-5430.png" width="200" alt="centrifuge_eppendorf_5430"> | AutoBio | 仪器 | centrifuge_eppendorf_5430 | [centrifuge_eppendorf_5430.xml](files/autobio/autobio/model/instrument/centrifuge_eppendorf_5430.xml) |
| <img src="previews/autobio/composite/instrument-centrifuge-eppendorf-5910-ri.png" width="200" alt="centrifuge_eppendorf_5910_ri"> | AutoBio | 仪器 | centrifuge_eppendorf_5910_ri | [centrifuge_eppendorf_5910_ri.xml](files/autobio/autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml) |
| <img src="previews/autobio/composite/instrument-centrifuge-tiangen-tgear-mini.png" width="200" alt="centrifuge_tiangen_tgear_mini"> | AutoBio | 仪器 | centrifuge_tiangen_tgear_mini | [centrifuge_tiangen_tgear_mini.xml](files/autobio/autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml) |
| <img src="previews/autobio/composite/instrument-thermal-cycler-biorad-c1000.png" width="200" alt="thermal_cycler_biorad_c1000"> | AutoBio | 仪器 | thermal_cycler_biorad_c1000 | [thermal_cycler_biorad_c1000.xml](files/autobio/autobio/model/instrument/thermal_cycler_biorad_c1000.xml) |
| <img src="previews/autobio/composite/instrument-thermal-mixer-eppendorf-c.png" width="200" alt="thermal_mixer_eppendorf_c"> | AutoBio | 仪器 | thermal_mixer_eppendorf_c | [thermal_mixer_eppendorf_c.xml](files/autobio/autobio/model/instrument/thermal_mixer_eppendorf_c.xml) |
| <img src="previews/autobio/composite/instrument-vortex-mixer-genie-2.png" width="200" alt="vortex_mixer_genie_2"> | AutoBio | 仪器 | vortex_mixer_genie_2 | [vortex_mixer_genie_2.xml](files/autobio/autobio/model/instrument/vortex_mixer_genie_2.xml) |
| <img src="previews/autobio/composite/robot-2f85.png" width="200" alt="2f85"> | AutoBio | 机器人 | 2f85 | [2f85.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/robot/2f85.xml) |
| <img src="previews/autobio/composite/robot-aloha-left.png" width="200" alt="aloha_left"> | AutoBio | 机器人 | aloha_left | [aloha_left.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/robot/aloha_left.xml) |
| <img src="previews/autobio/composite/robot-dualrm.png" width="200" alt="dualrm"> | AutoBio | 机器人 | dualrm | [dualrm.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/robot/dualrm.xml) |
| <img src="previews/autobio/composite/robot-piper.png" width="200" alt="piper"> | AutoBio | 机器人 | piper | [piper.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/robot/piper.xml) |
| <img src="previews/autobio/composite/robot-ur5e-dexhand021-right.png" width="200" alt="ur5e_dexhand021_right"> | AutoBio | 机器人 | ur5e_dexhand021_right | [ur5e_dexhand021_right.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/robot/ur5e_dexhand021_right.xml) |
| <img src="previews/autobio/composite/robot-ur5e-gripper.png" width="200" alt="ur5e_gripper"> | AutoBio | 机器人 | ur5e_gripper | [ur5e_gripper.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/robot/ur5e_gripper.xml) |
| <img src="previews/autobio/composite/hand-dexhand021-right.png" width="200" alt="dexhand021_right"> | AutoBio | 手部末端 | dexhand021_right | [dexhand021_right.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/hand/dexhand021_right.xml) |
| <img src="previews/autobio/composite/hand-shadowhand-left.png" width="200" alt="shadowhand_left"> | AutoBio | 手部末端 | shadowhand_left | [shadowhand_left.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/hand/shadowhand_left.xml) |
| <img src="previews/autobio/composite/hand-shadowhand-right.png" width="200" alt="shadowhand_right"> | AutoBio | 手部末端 | shadowhand_right | [shadowhand_right.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/hand/shadowhand_right.xml) |
| <img src="previews/autobio/composite/hand-shadowhand-right-mjx.png" width="200" alt="shadowhand_right_mjx"> | AutoBio | 手部末端 | shadowhand_right_mjx | [shadowhand_right_mjx.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/hand/shadowhand_right_mjx.xml) |

### 4.4 完整场景与场景相关文件

| 预览 | 来源 | 类别 | 名称 | 路径 | 说明 |
| --- | --- | --- | --- | --- | --- |
| <img src="previews/autobio/scenes/bottlecap.png" width="200" alt="bottlecap"> | AutoBio | 完整场景 | bottlecap | [bottlecap.xml](files/autobio/autobio/model/scene/bottlecap.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/gallery.png" width="200" alt="gallery"> | AutoBio | 完整场景 | gallery | [gallery.xml](files/autobio/autobio/model/scene/gallery.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/gallery2.png" width="200" alt="gallery2"> | AutoBio | 完整场景 | gallery2 | [gallery2.xml](files/autobio/autobio/model/scene/gallery2.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/insert.png" width="200" alt="insert"> | AutoBio | 完整场景 | insert | [insert.xml](files/autobio/autobio/model/scene/insert.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/insert-centrifuge-5430.png" width="200" alt="insert_centrifuge_5430"> | AutoBio | 完整场景 | insert_centrifuge_5430 | [insert_centrifuge_5430.xml](files/autobio/autobio/model/scene/insert_centrifuge_5430.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/lab.png" width="200" alt="lab"> | AutoBio | 完整场景 | lab | [lab.xml](files/autobio/autobio/model/scene/lab.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/lab-screw-all.png" width="200" alt="lab_screw_all"> | AutoBio | 完整场景 | lab_screw_all | [lab_screw_all.xml](files/autobio/autobio/model/scene/lab_screw_all.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/lab-screw-tighten.png" width="200" alt="lab_screw_tighten"> | AutoBio | 完整场景 | lab_screw_tighten | [lab_screw_tighten.xml](files/autobio/autobio/model/scene/lab_screw_tighten.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-centrifuge-5430.png" width="200" alt="mani_centrifuge_5430"> | AutoBio | 完整场景 | mani_centrifuge_5430 | [mani_centrifuge_5430.xml](files/autobio/autobio/model/scene/mani_centrifuge_5430.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-centrifuge-5910.png" width="200" alt="mani_centrifuge_5910"> | AutoBio | 完整场景 | mani_centrifuge_5910 | [mani_centrifuge_5910.xml](files/autobio/autobio/model/scene/mani_centrifuge_5910.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-centrifuge-mini.png" width="200" alt="mani_centrifuge_mini"> | AutoBio | 完整场景 | mani_centrifuge_mini | [mani_centrifuge_mini.xml](files/autobio/autobio/model/scene/mani_centrifuge_mini.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-pipette.png" width="200" alt="mani_pipette"> | AutoBio | 完整场景 | mani_pipette | [mani_pipette.xml](files/autobio/autobio/model/scene/mani_pipette.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-thermal-cycler.png" width="200" alt="mani_thermal_cycler"> | AutoBio | 完整场景 | mani_thermal_cycler | [mani_thermal_cycler.xml](files/autobio/autobio/model/scene/mani_thermal_cycler.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-thermal-mixer.png" width="200" alt="mani_thermal_mixer"> | AutoBio | 完整场景 | mani_thermal_mixer | [mani_thermal_mixer.xml](files/autobio/autobio/model/scene/mani_thermal_mixer.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/pickup.png" width="200" alt="pickup"> | AutoBio | 完整场景 | pickup | [pickup.xml](files/autobio/autobio/model/scene/pickup.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/screw.png" width="200" alt="screw"> | AutoBio | 完整场景 | screw | [screw.xml](files/autobio/autobio/model/scene/screw.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/screw-test.png" width="200" alt="screw_test"> | AutoBio | 完整场景 | screw_test | [screw_test.xml](files/autobio/autobio/model/scene/screw_test.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/screw-v3.png" width="200" alt="screw_v3"> | AutoBio | 完整场景 | screw_v3 | [screw_v3.xml](files/autobio/autobio/model/scene/screw_v3.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/vortex-mixer.png" width="200" alt="vortex_mixer"> | AutoBio | 完整场景 | vortex_mixer | [vortex_mixer.xml](files/autobio/autobio/model/scene/vortex_mixer.xml) | MuJoCo XML 场景入口 |
| <img src="previews/labutopia/scenes/lab-001.png" width="200" alt="lab_001"> | LabUtopia | 完整场景 | lab_001 | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) | chemistry main scene |
| <img src="previews/labutopia/scenes/lab-003.png" width="200" alt="lab_003"> | LabUtopia | 完整场景 | lab_003 | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd) | chemistry main scene |
| <img src="previews/labutopia/scenes/scene1-hard.png" width="200" alt="Scene1_hard"> | LabUtopia | 完整场景 | Scene1_hard | [Scene1_hard.usd](files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd) | chemistry main scene |
| <img src="previews/labutopia/scenes/clock.png" width="200" alt="clock"> | LabUtopia | 完整场景 | clock | [clock.usd](files/labutopia/assets/chemistry_lab/lab_003/clock.usd) | chemistry special scene |
| <img src="previews/labutopia/scenes/navigation-lab-01.png" width="200" alt="navigation_lab_01"> | LabUtopia | 完整场景 | navigation_lab_01 | [lab.usd](files/labutopia/assets/navigation_lab/navigation_lab_01/lab.usd) | navigation scene |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-lab-004-usd.png" width="200" alt="assets/chemistry_lab/hard_task/lab_004.usd"> | LabUtopia | 场景相关文件 | lab_004 | [lab_004.usd](files/labutopia/assets/chemistry_lab/hard_task/lab_004.usd) | auxiliary USD |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-subusds-lab-015-usd.png" width="200" alt="assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd"> | LabUtopia | 场景相关文件 | lab_015 | [lab_015.usd](files/labutopia/assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd) | SubUSD |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-lab-003-subusds-lab-015-usd.png" width="200" alt="assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd"> | LabUtopia | 场景相关文件 | lab_015 | [lab_015.usd](files/labutopia/assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd) | SubUSD |

## 5. 筛选后的 Benchmark 资产 / 场景

这一节对应 `benchmark_core_inventory.json`。这里采用最宽的 protocol 口径：凡是能直接服务 protocol 构造、protocol 理解，或者能作为 Level 2 视觉上下文的完整场景，都纳入第 5 章；只把明显属于 Level 3 执行器的 robot / hand / gripper 留在第 4 章。

### 5.1 纳入标准

只有同时满足下面这些条件的条目，才会进入这一章：

1. 条目本身或场景主体必须直接服务 protocol 构造、protocol 理解或 Level 2 的实验上下文表达。
2. 能稳定归入一个明确的语义类别，并绑定 `match_group` 与别名集合。
3. 能整理成结构化数据单元，而不只是上游仓库里的孤立文件。
4. 粒度适合题目构造与 protocol 匹配；完整场景只要提供 protocol 相关仪器、容器、实验台面或实验室上下文，就纳入。
5. 至少具备可追溯的来源路径、用途说明和可视化状态，便于后续扩展与人工核查。

### 5.2 核心条目表

这一节改为 HTML 两列布局：左侧固定放大预览图，右侧放条目字段，避免 GitHub Markdown 表格把图片继续压缩。
当前共 `053` 项，编号从 `000` 到 `052`。

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-cell-dish-100.png" width="420" alt="100 mm Cell Dish">
    </td>
    <td valign="top">
      <p><strong><code>000</code> 100 mm Cell Dish</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>cell_dish</code></p>
      <p><strong>用途：</strong>Cell culture plate for seeding, incubation, washing, and imaging.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/cell_dish_100_vis.obj">cell_dish_100_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/cell_dish_100_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>cell dish<br>cell dishes<br>cell culture dish<br>cell culture dishes<br>culture dish<br>culture dishes<br>petri dish<br>petri dishes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-1-5ml-screw.png" width="420" alt="1.5 mL Screw-Cap Microcentrifuge Tube">
    </td>
    <td valign="top">
      <p><strong><code>001</code> 1.5 mL Screw-Cap Microcentrifuge Tube</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>microcentrifuge_tube_1_5ml</code></p>
      <p><strong>用途：</strong>Small sample tube for aliquoting, mixing, incubation, and centrifugation.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/centrifuge_1-5ml_screw_vis">centrifuge_1-5ml_screw_vis/</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/centrifuge_1-5ml_screw_vis">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>microcentrifuge tube<br>microcentrifuge tubes<br>eppendorf tube<br>eppendorf tubes<br>1.5 ml tube<br>1.5 ml tubes<br>1.5 ml microcentrifuge tube<br>1.5 ml centrifuge tube<br>1.5 ml screw cap tube</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-10ml.png" width="420" alt="10 mL Centrifuge Tube">
    </td>
    <td valign="top">
      <p><strong><code>002</code> 10 mL Centrifuge Tube</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>centrifuge_tube_10ml</code></p>
      <p><strong>用途：</strong>Medium-volume sample tube for transfer and centrifugation.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/centrifuge_10ml_vis.obj">centrifuge_10ml_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/centrifuge_10ml_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>10 ml centrifuge tube<br>10 ml centrifuge tubes<br>10ml centrifuge tube<br>10 ml tube<br>10 ml tubes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-1500ul-open.png" width="420" alt="1.5 mL Open Microcentrifuge Tube">
    </td>
    <td valign="top">
      <p><strong><code>003</code> 1.5 mL Open Microcentrifuge Tube</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>microcentrifuge_tube_1_5ml</code></p>
      <p><strong>用途：</strong>Open microcentrifuge tube for liquid handling and insertion tasks.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj">centrifuge_1500ul_no_lid_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>microcentrifuge tube<br>microcentrifuge tubes<br>eppendorf tube<br>eppendorf tubes<br>1.5 ml tube<br>1.5 ml tubes<br>1.5 ml microcentrifuge tube<br>1.5 ml centrifuge tube<br>1.5 ml screw cap tube</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-15ml-screw.png" width="420" alt="15 mL Screw-Cap Centrifuge Tube">
    </td>
    <td valign="top">
      <p><strong><code>004</code> 15 mL Screw-Cap Centrifuge Tube</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>centrifuge_tube_15ml</code></p>
      <p><strong>用途：</strong>Conical sample tube for medium-volume transfer and centrifugation.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/centrifuge_15ml_screw_vis">centrifuge_15ml_screw_vis/</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/centrifuge_15ml_screw_vis">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>15 ml centrifuge tube<br>15 ml centrifuge tubes<br>15ml centrifuge tube<br>15 ml conical tube<br>15 ml conical tubes<br>15ml conical tube<br>15 ml falcon tube<br>15 ml falcon tubes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-50ml.png" width="420" alt="50 mL Centrifuge Tube">
    </td>
    <td valign="top">
      <p><strong><code>005</code> 50 mL Centrifuge Tube</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>centrifuge_tube_50ml</code></p>
      <p><strong>用途：</strong>Large conical tube for reagent preparation and centrifugation.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/centrifuge_50ml_vis.obj">centrifuge_50ml_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/centrifuge_50ml_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>50 ml centrifuge tube<br>50 ml centrifuge tubes<br>50ml centrifuge tube<br>50 ml conical tube<br>50 ml conical tubes<br>50ml conical tube<br>50 ml falcon tube<br>50 ml falcon tubes<br>falcon tube<br>falcon tubes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-50ml-screw.png" width="420" alt="50 mL Screw-Cap Centrifuge Tube">
    </td>
    <td valign="top">
      <p><strong><code>006</code> 50 mL Screw-Cap Centrifuge Tube</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>centrifuge_tube_50ml</code></p>
      <p><strong>用途：</strong>Large screw-cap tube for sealed transfer and centrifugation.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/centrifuge_50ml_screw_vis">centrifuge_50ml_screw_vis/</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/centrifuge_50ml_screw_vis">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>50 ml centrifuge tube<br>50 ml centrifuge tubes<br>50ml centrifuge tube<br>50 ml conical tube<br>50 ml conical tubes<br>50ml conical tube<br>50 ml falcon tube<br>50 ml falcon tubes<br>falcon tube<br>falcon tubes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-cryovial-1-8ml.png" width="420" alt="1.8 mL Cryovial">
    </td>
    <td valign="top">
      <p><strong><code>007</code> 1.8 mL Cryovial</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>cryovial</code></p>
      <p><strong>用途：</strong>Cryogenic storage vial for frozen samples and aliquots.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/cryovial_1-8ml_vis">cryovial_1-8ml_vis/</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/cryovial_1-8ml_vis">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>cryovial<br>cryovials<br>cryo vial<br>cryo vials<br>cryogenic vial<br>cryogenic vials</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-pcr-plate-96well.png" width="420" alt="96-Well PCR Plate">
    </td>
    <td valign="top">
      <p><strong><code>008</code> 96-Well PCR Plate</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>pcr_plate</code></p>
      <p><strong>用途：</strong>Plate for PCR setup, thermal cycling, and sample organization.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/pcr_plate_96well_vis.obj">pcr_plate_96well_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/pcr_plate_96well_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>pcr plate<br>pcr plates<br>96 well pcr plate<br>96 well pcr plates<br>96 well plate<br>96 well plates<br>96 well microplate<br>96 well microplates</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-tip-200ul.png" width="420" alt="200 uL Pipette Tip">
    </td>
    <td valign="top">
      <p><strong><code>009</code> 200 uL Pipette Tip</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>pipette_tip</code></p>
      <p><strong>用途：</strong>Disposable liquid-handling tip for pipetting small volumes.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/container/tip_200ul_vis/visual.obj">visual.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/tip_200ul_vis">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>pipette tip<br>pipette tips<br>micropipette tip<br>micropipette tips<br>200 ul tip<br>200 ul tips<br>200 ul pipette tip<br>200 ul pipette tips</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-pipette.png" width="420" alt="Micropipette">
    </td>
    <td valign="top">
      <p><strong><code>010</code> Micropipette</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>pipette</code></p>
      <p><strong>用途：</strong>Manual pipette for aspirating and dispensing liquids.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/object/pipette.gen.xml">pipette.gen.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/object/pipette.gen.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>pipette<br>pipettes<br>micropipette<br>micropipettes<br>single channel pipette<br>single channel pipettes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-tip-box-24slot.png" width="420" alt="24-Slot Tip Box">
    </td>
    <td valign="top">
      <p><strong><code>011</code> 24-Slot Tip Box</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>tip_box</code></p>
      <p><strong>用途：</strong>Container for storing and presenting pipette tips.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/rack/tip_box_24slot_vis.obj">tip_box_24slot_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/tip_box_24slot_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>tip box<br>tip boxes<br>pipette tip box<br>pipette tip boxes</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-pipette-rack-tri.png" width="420" alt="Triangular Pipette Rack">
    </td>
    <td valign="top">
      <p><strong><code>012</code> Triangular Pipette Rack</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>pipette_rack</code></p>
      <p><strong>用途：</strong>Rack for holding pipettes upright between operations.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/rack/pipette_rack_tri_vis.obj">pipette_rack_tri_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/pipette_rack_tri_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>pipette rack<br>pipette racks<br>pipette holder<br>pipette holders<br>pipette stand<br>pipette stands</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-10slot-rack.png" width="420" alt="10-Slot Centrifuge Tube Rack">
    </td>
    <td valign="top">
      <p><strong><code>013</code> 10-Slot Centrifuge Tube Rack</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>tube_rack</code></p>
      <p><strong>用途：</strong>Rack for organizing and positioning sample tubes.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/rack/centrifuge_10slot_vis.obj">centrifuge_10slot_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/centrifuge_10slot_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>tube rack<br>tube racks<br>centrifuge tube rack<br>centrifuge tube racks<br>microcentrifuge tube rack<br>microcentrifuge tube racks<br>test tube rack<br>test tube racks</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-plate-60well.png" width="420" alt="60-Well Plate Rack">
    </td>
    <td valign="top">
      <p><strong><code>014</code> 60-Well Plate Rack</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>独立对象<br>
      <strong>匹配组：</strong><code>tube_rack</code></p>
      <p><strong>用途：</strong>Multi-well rack for arranging small tubes or vials.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/assets/rack/centrifuge_plate_60well_vis.obj">centrifuge_plate_60well_vis.obj</a></p>
      <p><strong>可视化状态：</strong>可直接按 mesh 渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/centrifuge_plate_60well_vis.obj">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>tube rack<br>tube racks<br>centrifuge tube rack<br>centrifuge tube racks<br>microcentrifuge tube rack<br>microcentrifuge tube racks<br>test tube rack<br>test tube racks</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-5430.png" width="420" alt="Eppendorf 5430 Centrifuge">
    </td>
    <td valign="top">
      <p><strong><code>015</code> Eppendorf 5430 Centrifuge</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>centrifuge</code></p>
      <p><strong>用途：</strong>Bench centrifuge for spinning small sample tubes.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/instrument/centrifuge_eppendorf_5430.xml">centrifuge_eppendorf_5430.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/centrifuge_eppendorf_5430.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>centrifuge<br>centrifuges<br>microcentrifuge<br>microcentrifuges<br>bench centrifuge<br>bench centrifuges<br>refrigerated centrifuge<br>refrigerated centrifuges</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-5910-ri.png" width="420" alt="Eppendorf 5910 Ri Centrifuge">
    </td>
    <td valign="top">
      <p><strong><code>016</code> Eppendorf 5910 Ri Centrifuge</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>centrifuge</code></p>
      <p><strong>用途：</strong>Large refrigerated centrifuge for higher-volume tube spinning.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml">centrifuge_eppendorf_5910_ri.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>centrifuge<br>centrifuges<br>microcentrifuge<br>microcentrifuges<br>bench centrifuge<br>bench centrifuges<br>refrigerated centrifuge<br>refrigerated centrifuges</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-centrifuge-tgear-mini.png" width="420" alt="Tiangen Tgear Mini Centrifuge">
    </td>
    <td valign="top">
      <p><strong><code>017</code> Tiangen Tgear Mini Centrifuge</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>centrifuge</code></p>
      <p><strong>用途：</strong>Compact mini centrifuge for quick spin-down operations.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml">centrifuge_tiangen_tgear_mini.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>centrifuge<br>centrifuges<br>microcentrifuge<br>microcentrifuges<br>bench centrifuge<br>bench centrifuges<br>refrigerated centrifuge<br>refrigerated centrifuges</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-thermal-cycler-c1000.png" width="420" alt="Bio-Rad C1000 Thermal Cycler">
    </td>
    <td valign="top">
      <p><strong><code>018</code> Bio-Rad C1000 Thermal Cycler</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>thermal_cycler</code></p>
      <p><strong>用途：</strong>PCR instrument for running thermal cycling programs.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/instrument/thermal_cycler_biorad_c1000.xml">thermal_cycler_biorad_c1000.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/thermal_cycler_biorad_c1000.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>thermal cycler<br>thermal cyclers<br>thermocycler<br>thermocyclers<br>pcr machine<br>pcr machines</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-thermal-mixer-eppendorf-c.png" width="420" alt="Eppendorf C Thermal Mixer">
    </td>
    <td valign="top">
      <p><strong><code>019</code> Eppendorf C Thermal Mixer</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>thermal_mixer</code></p>
      <p><strong>用途：</strong>Instrument for controlled heating and shaking of samples.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/instrument/thermal_mixer_eppendorf_c.xml">thermal_mixer_eppendorf_c.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/thermal_mixer_eppendorf_c.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>thermal mixer<br>thermal mixers<br>thermomixer<br>thermomixers<br>heat shaker<br>heat shakers</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-vortex-mixer-genie-2.png" width="420" alt="Genie 2 Vortex Mixer">
    </td>
    <td valign="top">
      <p><strong><code>020</code> Genie 2 Vortex Mixer</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>组合对象<br>
      <strong>匹配组：</strong><code>vortex_mixer</code></p>
      <p><strong>用途：</strong>Mixer for vortexing tubes and suspensions.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/instrument/vortex_mixer_genie_2.xml">vortex_mixer_genie_2.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 装配渲染<br>
      <strong>原始链接：</strong><a href="https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/vortex_mixer_genie_2.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>vortex mixer<br>vortex mixers<br>vortexer<br>vortexers<br>vortex genie</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-beaker-family.png" width="420" alt="Beaker Family">
    </td>
    <td valign="top">
      <p><strong><code>021</code> Beaker Family</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>beaker</code></p>
      <p><strong>用途：</strong>General glass container for mixing, pouring, heating, and transfer.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd">lab_001.usd</a><br><code>#/World/beaker1</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>beaker<br>beakers<br>glass beaker<br>glass beakers</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-conical-bottle-family.png" width="420" alt="Conical Bottle / Flask Family">
    </td>
    <td valign="top">
      <p><strong><code>022</code> Conical Bottle / Flask Family</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>conical_bottle</code></p>
      <p><strong>用途：</strong>Flask-style glassware for liquid storage, mixing, and pouring.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd">lab_001.usd</a><br><code>#/World/conical_bottle02</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>conical bottle<br>conical bottles<br>erlenmeyer flask<br>erlenmeyer flasks<br>conical flask<br>conical flasks</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-graduated-cylinder-03.png" width="420" alt="Graduated Cylinder">
    </td>
    <td valign="top">
      <p><strong><code>023</code> Graduated Cylinder</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>graduated_cylinder</code></p>
      <p><strong>用途：</strong>Volumetric cylinder for measuring and dispensing liquids.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd">lab_001.usd</a><br><code>#/World/graduated_cylinder_03</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>graduated cylinder<br>graduated cylinders<br>measuring cylinder<br>measuring cylinders</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-glass-rod.png" width="420" alt="Glass Rod">
    </td>
    <td valign="top">
      <p><strong><code>024</code> Glass Rod</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>glass_rod</code></p>
      <p><strong>用途：</strong>Rod for manual stirring and mixing.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd">lab_003.usd</a><br><code>#/World/glass_rod</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/lab_003.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>glass rod<br>glass rods<br>stirring rod<br>stirring rods<br>glass stirring rod<br>glass stirring rods</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-test-tube-rack.png" width="420" alt="Test Tube Rack">
    </td>
    <td valign="top">
      <p><strong><code>025</code> Test Tube Rack</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>tube_rack</code></p>
      <p><strong>用途：</strong>Rack for holding tubes upright during preparation and storage.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd">lab_003.usd</a><br><code>#/World/test_tube_rack</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/lab_003.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>tube rack<br>tube racks<br>centrifuge tube rack<br>centrifuge tube racks<br>microcentrifuge tube rack<br>microcentrifuge tube racks<br>test tube rack<br>test tube racks</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-drying-box-family.png" width="420" alt="Drying Box Family">
    </td>
    <td valign="top">
      <p><strong><code>026</code> Drying Box Family</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>drying_box</code></p>
      <p><strong>用途：</strong>Device used for drying or enclosed heating workflows.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd">lab_001.usd</a><br><code>#/World/DryingBox_01</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>drying box<br>drying boxes<br>dry box<br>dry boxes<br>drying oven<br>drying ovens<br>drying chamber<br>drying chambers</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-heat-device.png" width="420" alt="Heat Device / Hot Plate">
    </td>
    <td valign="top">
      <p><strong><code>027</code> Heat Device / Hot Plate</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>heating_device</code></p>
      <p><strong>用途：</strong>Heating surface or device used to activate thermal tasks.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd">lab_003.usd</a><br><code>#/World/heat_device</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/lab_003.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>hot plate<br>hot plates<br>heating plate<br>heating plates<br>heating device<br>heating devices<br>heat device<br>heat devices<br>heater<br>heaters</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-muffle-furnace.png" width="420" alt="Muffle Furnace">
    </td>
    <td valign="top">
      <p><strong><code>028</code> Muffle Furnace</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>场景内对象引用<br>
      <strong>匹配组：</strong><code>muffle_furnace</code></p>
      <p><strong>用途：</strong>High-temperature heating device for enclosed furnace operations.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd">lab_001.usd</a><br><code>#/World/MuffleFurnace</code></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>muffle furnace<br>muffle furnaces<br>laboratory furnace<br>laboratory furnaces</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-bottlecap.png" width="420" alt="AutoBio Scene: bottlecap">
    </td>
    <td valign="top">
      <p><strong><code>029</code> AutoBio Scene: bottlecap</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_bottlecap</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/bottlecap.xml">bottlecap.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/bottlecap.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>bottlecap<br>bottlecap</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-gallery.png" width="420" alt="AutoBio Scene: gallery">
    </td>
    <td valign="top">
      <p><strong><code>030</code> AutoBio Scene: gallery</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_gallery</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/gallery.xml">gallery.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/gallery.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>gallery<br>gallery</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-gallery2.png" width="420" alt="AutoBio Scene: gallery2">
    </td>
    <td valign="top">
      <p><strong><code>031</code> AutoBio Scene: gallery2</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_gallery2</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/gallery2.xml">gallery2.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/gallery2.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>gallery2<br>gallery2</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-insert.png" width="420" alt="AutoBio Scene: insert">
    </td>
    <td valign="top">
      <p><strong><code>032</code> AutoBio Scene: insert</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_insert</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/insert.xml">insert.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/insert.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>insert<br>insert</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-insert-centrifuge-5430.png" width="420" alt="AutoBio Scene: insert centrifuge 5430">
    </td>
    <td valign="top">
      <p><strong><code>033</code> AutoBio Scene: insert centrifuge 5430</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_insert_centrifuge_5430</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/insert_centrifuge_5430.xml">insert_centrifuge_5430.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/insert_centrifuge_5430.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>insert_centrifuge_5430<br>insert centrifuge 5430</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-lab.png" width="420" alt="AutoBio Scene: lab">
    </td>
    <td valign="top">
      <p><strong><code>034</code> AutoBio Scene: lab</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_lab</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/lab.xml">lab.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>lab<br>lab</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-lab-screw-all.png" width="420" alt="AutoBio Scene: lab screw all">
    </td>
    <td valign="top">
      <p><strong><code>035</code> AutoBio Scene: lab screw all</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_lab_screw_all</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/lab_screw_all.xml">lab_screw_all.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab_screw_all.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>lab_screw_all<br>lab screw all</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-lab-screw-tighten.png" width="420" alt="AutoBio Scene: lab screw tighten">
    </td>
    <td valign="top">
      <p><strong><code>036</code> AutoBio Scene: lab screw tighten</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_lab_screw_tighten</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/lab_screw_tighten.xml">lab_screw_tighten.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab_screw_tighten.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>lab_screw_tighten<br>lab screw tighten</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-mani-centrifuge-5430.png" width="420" alt="AutoBio Scene: mani centrifuge 5430">
    </td>
    <td valign="top">
      <p><strong><code>037</code> AutoBio Scene: mani centrifuge 5430</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_mani_centrifuge_5430</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/mani_centrifuge_5430.xml">mani_centrifuge_5430.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_centrifuge_5430.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>mani_centrifuge_5430<br>mani centrifuge 5430</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-mani-centrifuge-5910.png" width="420" alt="AutoBio Scene: mani centrifuge 5910">
    </td>
    <td valign="top">
      <p><strong><code>038</code> AutoBio Scene: mani centrifuge 5910</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_mani_centrifuge_5910</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/mani_centrifuge_5910.xml">mani_centrifuge_5910.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_centrifuge_5910.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>mani_centrifuge_5910<br>mani centrifuge 5910</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-mani-centrifuge-mini.png" width="420" alt="AutoBio Scene: mani centrifuge mini">
    </td>
    <td valign="top">
      <p><strong><code>039</code> AutoBio Scene: mani centrifuge mini</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_mani_centrifuge_mini</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/mani_centrifuge_mini.xml">mani_centrifuge_mini.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_centrifuge_mini.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>mani_centrifuge_mini<br>mani centrifuge mini</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-mani-pipette.png" width="420" alt="AutoBio Scene: mani pipette">
    </td>
    <td valign="top">
      <p><strong><code>040</code> AutoBio Scene: mani pipette</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_mani_pipette</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/mani_pipette.xml">mani_pipette.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_pipette.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>mani_pipette<br>mani pipette</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-mani-thermal-cycler.png" width="420" alt="AutoBio Scene: mani thermal cycler">
    </td>
    <td valign="top">
      <p><strong><code>041</code> AutoBio Scene: mani thermal cycler</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_mani_thermal_cycler</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/mani_thermal_cycler.xml">mani_thermal_cycler.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_thermal_cycler.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>mani_thermal_cycler<br>mani thermal cycler</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-mani-thermal-mixer.png" width="420" alt="AutoBio Scene: mani thermal mixer">
    </td>
    <td valign="top">
      <p><strong><code>042</code> AutoBio Scene: mani thermal mixer</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_mani_thermal_mixer</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/mani_thermal_mixer.xml">mani_thermal_mixer.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_thermal_mixer.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>mani_thermal_mixer<br>mani thermal mixer</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-pickup.png" width="420" alt="AutoBio Scene: pickup">
    </td>
    <td valign="top">
      <p><strong><code>043</code> AutoBio Scene: pickup</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_pickup</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/pickup.xml">pickup.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/pickup.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>pickup<br>pickup</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-screw.png" width="420" alt="AutoBio Scene: screw">
    </td>
    <td valign="top">
      <p><strong><code>044</code> AutoBio Scene: screw</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_screw</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/screw.xml">screw.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/screw.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>screw<br>screw</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-screw-test.png" width="420" alt="AutoBio Scene: screw test">
    </td>
    <td valign="top">
      <p><strong><code>045</code> AutoBio Scene: screw test</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_screw_test</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/screw_test.xml">screw_test.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/screw_test.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>screw_test<br>screw test</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-screw-v3.png" width="420" alt="AutoBio Scene: screw v3">
    </td>
    <td valign="top">
      <p><strong><code>046</code> AutoBio Scene: screw v3</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_screw_v3</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/screw_v3.xml">screw_v3.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/screw_v3.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>screw_v3<br>screw v3</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/autobio/autobio-scene-vortex-mixer.png" width="420" alt="AutoBio Scene: vortex mixer">
    </td>
    <td valign="top">
      <p><strong><code>047</code> AutoBio Scene: vortex mixer</strong></p>
      <p><strong>来源：</strong>AutoBio<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_vortex_mixer</code></p>
      <p><strong>用途：</strong>Full AutoBio scene image for Level 2 multi-instrument visual context.</p>
      <p><strong>本地文件：</strong><a href="files/autobio/autobio/model/scene/vortex_mixer.xml">vortex_mixer.xml</a></p>
      <p><strong>可视化状态：</strong>可直接按 MJCF 场景渲染<br>
      <strong>原始链接：</strong><a href="https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/vortex_mixer.xml">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>vortex_mixer<br>vortex mixer</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-scene-lab-001.png" width="420" alt="LabUtopia Scene: lab_001">
    </td>
    <td valign="top">
      <p><strong><code>048</code> LabUtopia Scene: lab_001</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_lab_001</code></p>
      <p><strong>用途：</strong>Full LabUtopia scene image for Level 2 laboratory context.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd">lab_001.usd</a></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>lab_001<br>lab 001</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-scene-lab-003.png" width="420" alt="LabUtopia Scene: lab_003">
    </td>
    <td valign="top">
      <p><strong><code>049</code> LabUtopia Scene: lab_003</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_lab_003</code></p>
      <p><strong>用途：</strong>Full LabUtopia scene image for Level 2 laboratory context.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd">lab_003.usd</a></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/lab_003.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>lab_003<br>lab 003</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-scene-scene1-hard.png" width="420" alt="LabUtopia Scene: Scene1_hard">
    </td>
    <td valign="top">
      <p><strong><code>050</code> LabUtopia Scene: Scene1_hard</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_scene1_hard</code></p>
      <p><strong>用途：</strong>Full LabUtopia scene image for Level 2 laboratory context.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd">Scene1_hard.usd</a></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/hard_task/Scene1_hard.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>scene1_hard<br>scene1 hard</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-scene-clock.png" width="420" alt="LabUtopia Scene: clock">
    </td>
    <td valign="top">
      <p><strong><code>051</code> LabUtopia Scene: clock</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_clock</code></p>
      <p><strong>用途：</strong>Full LabUtopia scene image for Level 2 laboratory context.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/chemistry_lab/lab_003/clock.usd">clock.usd</a></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/clock.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>clock<br>clock</p>
      </details>
    </td>
  </tr>
</table>

<table>
  <tr>
    <td valign="top" width="450">
      <img src="previews/core/labutopia/labutopia-scene-navigation-lab-01.png" width="420" alt="LabUtopia Scene: navigation_lab_01">
    </td>
    <td valign="top">
      <p><strong><code>052</code> LabUtopia Scene: navigation_lab_01</strong></p>
      <p><strong>来源：</strong>LabUtopia<br>
      <strong>层级：</strong>完整场景<br>
      <strong>匹配组：</strong><code>scene_navigation_lab_01</code></p>
      <p><strong>用途：</strong>Full LabUtopia scene image for Level 2 laboratory context.</p>
      <p><strong>本地文件：</strong><a href="files/labutopia/assets/navigation_lab/navigation_lab_01/lab.usd">lab.usd</a></p>
      <p><strong>可视化状态：</strong>当前使用 USD 场景缩略图展示<br>
      <strong>原始链接：</strong><a href="https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/navigation_lab/navigation_lab_01/lab.usd">源文件</a></p>
      <details>
        <summary><strong>别名</strong></summary>
        <p>navigation_lab_01<br>navigation lab 01</p>
      </details>
    </td>
  </tr>
</table>

## 6. 当前结论

- 现在的目录口径已经从“只看 asset”改成“统一看实验室条目”。
- `AutoBio` 更适合提供独立对象、组合对象和可执行的完整场景。
- `LabUtopia` 更适合提供场景内对象引用、化学实验室场景和场景上下文。
- 后续如果要继续扩 benchmark，优先在这份核心条目表上补别名、补用途、补协议匹配结果，而不是再分叉新的清单文件。
