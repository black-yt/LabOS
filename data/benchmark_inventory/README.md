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
| AutoBio | 对象优先，兼有完整 MuJoCo XML 场景 | 独立对象 25<br>组合对象 34<br>完整场景 19 | 21 | [assets/](files/autobio/autobio/assets)<br>[model/](files/autobio/autobio/model) |
| LabUtopia | 场景优先，核心文件是 USD 场景 | 场景内对象引用 11<br>完整场景 5<br>场景相关文件 3 | 8 | [chemistry_lab/](files/labutopia/assets/chemistry_lab) |

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
    C --> D[核心条目 29 项]
```

当前核心条目共 29 项，其中 `AutoBio` 21 项，`LabUtopia` 8 项。

## 2. 统一口径

这里统一使用“实验室条目”作为总称，不再把所有东西都叫作 asset。判断规则如下：

| 标识 | 中文解释 | 是否独立文件 | 典型路径 |
| --- | --- | --- | --- |
| `scene` | 完整场景入口，加载后看到的是整张实验台、整台设备或整个实验室。 | 是 | [lab.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab.xml)<br>[lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) |
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
| <img src="previews/labutopia/scene_objects/muffle-furnace.png" width="200" alt="muffle furnace"> | LabUtopia | muffle furnace | <code>/World/MuffleFurnace</code> | [Scene1_hard.usd](files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd) |
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
| <img src="previews/autobio/scenes/bottlecap.png" width="200" alt="bottlecap"> | AutoBio | 完整场景 | bottlecap | [bottlecap.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/bottlecap.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/gallery.png" width="200" alt="gallery"> | AutoBio | 完整场景 | gallery | [gallery.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/gallery.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/gallery2.png" width="200" alt="gallery2"> | AutoBio | 完整场景 | gallery2 | [gallery2.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/gallery2.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/insert.png" width="200" alt="insert"> | AutoBio | 完整场景 | insert | [insert.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/insert.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/insert-centrifuge-5430.png" width="200" alt="insert_centrifuge_5430"> | AutoBio | 完整场景 | insert_centrifuge_5430 | [insert_centrifuge_5430.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/insert_centrifuge_5430.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/lab.png" width="200" alt="lab"> | AutoBio | 完整场景 | lab | [lab.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/lab-screw-all.png" width="200" alt="lab_screw_all"> | AutoBio | 完整场景 | lab_screw_all | [lab_screw_all.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab_screw_all.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/lab-screw-tighten.png" width="200" alt="lab_screw_tighten"> | AutoBio | 完整场景 | lab_screw_tighten | [lab_screw_tighten.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/lab_screw_tighten.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-centrifuge-5430.png" width="200" alt="mani_centrifuge_5430"> | AutoBio | 完整场景 | mani_centrifuge_5430 | [mani_centrifuge_5430.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_centrifuge_5430.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-centrifuge-5910.png" width="200" alt="mani_centrifuge_5910"> | AutoBio | 完整场景 | mani_centrifuge_5910 | [mani_centrifuge_5910.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_centrifuge_5910.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-centrifuge-mini.png" width="200" alt="mani_centrifuge_mini"> | AutoBio | 完整场景 | mani_centrifuge_mini | [mani_centrifuge_mini.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_centrifuge_mini.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-pipette.png" width="200" alt="mani_pipette"> | AutoBio | 完整场景 | mani_pipette | [mani_pipette.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_pipette.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-thermal-cycler.png" width="200" alt="mani_thermal_cycler"> | AutoBio | 完整场景 | mani_thermal_cycler | [mani_thermal_cycler.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_thermal_cycler.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/mani-thermal-mixer.png" width="200" alt="mani_thermal_mixer"> | AutoBio | 完整场景 | mani_thermal_mixer | [mani_thermal_mixer.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/mani_thermal_mixer.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/pickup.png" width="200" alt="pickup"> | AutoBio | 完整场景 | pickup | [pickup.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/pickup.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/screw.png" width="200" alt="screw"> | AutoBio | 完整场景 | screw | [screw.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/screw.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/screw-test.png" width="200" alt="screw_test"> | AutoBio | 完整场景 | screw_test | [screw_test.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/screw_test.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/screw-v3.png" width="200" alt="screw_v3"> | AutoBio | 完整场景 | screw_v3 | [screw_v3.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/screw_v3.xml) | MuJoCo XML 场景入口 |
| <img src="previews/autobio/scenes/vortex-mixer.png" width="200" alt="vortex_mixer"> | AutoBio | 完整场景 | vortex_mixer | [vortex_mixer.xml](https://github.com/autobio-bench/AutoBio/blob/main/autobio/model/scene/vortex_mixer.xml) | MuJoCo XML 场景入口 |
| <img src="previews/labutopia/scenes/lab-001.png" width="200" alt="lab_001"> | LabUtopia | 完整场景 | lab_001 | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd) | chemistry main scene |
| <img src="previews/labutopia/scenes/lab-003.png" width="200" alt="lab_003"> | LabUtopia | 完整场景 | lab_003 | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd) | chemistry main scene |
| <img src="previews/labutopia/scenes/scene1-hard.png" width="200" alt="Scene1_hard"> | LabUtopia | 完整场景 | Scene1_hard | [Scene1_hard.usd](files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd) | chemistry main scene |
| <img src="previews/labutopia/scenes/clock.png" width="200" alt="clock"> | LabUtopia | 完整场景 | clock | [clock.usd](files/labutopia/assets/chemistry_lab/lab_003/clock.usd) | chemistry special scene |
| <img src="previews/labutopia/scenes/navigation-lab-01.png" width="200" alt="navigation_lab_01"> | LabUtopia | 完整场景 | navigation_lab_01 | [lab.usd](https://github.com/Rui-li023/LabUtopia/blob/main/assets/navigation_lab/navigation_lab_01/lab.usd) | navigation scene |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-lab-004-usd.png" width="200" alt="assets/chemistry_lab/hard_task/lab_004.usd"> | LabUtopia | 场景相关文件 | lab_004 | [lab_004.usd](files/labutopia/assets/chemistry_lab/hard_task/lab_004.usd) | auxiliary USD |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-subusds-lab-015-usd.png" width="200" alt="assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd"> | LabUtopia | 场景相关文件 | lab_015 | [lab_015.usd](files/labutopia/assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd) | SubUSD |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-lab-003-subusds-lab-015-usd.png" width="200" alt="assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd"> | LabUtopia | 场景相关文件 | lab_015 | [lab_015.usd](files/labutopia/assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd) | SubUSD |

## 5. 筛选后的 Benchmark 资产 / 场景

这一节对应 `benchmark_core_inventory.json`。它只保留当前 benchmark 直接需要复用的核心条目，而不是上游仓库的全部文件。

### 5.1 纳入标准

只有同时满足下面这些条件的条目，才会进入这一章：

1. 能直接服务 benchmark 任务，而不是只提供环境背景。
2. 能稳定归入一个明确的语义类别，并绑定 `match_group` 与别名集合。
3. 能整理成结构化数据单元，而不只是上游仓库里的孤立文件。
4. 粒度适合题目构造与 protocol 匹配，不会过细到单个环境碎片，也不会过粗到整张场景。
5. 至少具备可追溯的来源路径、用途说明和可视化状态，便于后续扩展与人工核查。

### 5.2 核心条目表

| 预览 | 条目名称 | 来源 | 层级 | 匹配组 | 别名 | 用途 | 本地文件 | 可视化状态 | 原始链接 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| <img src="previews/core/autobio/autobio-cell-dish-100.png" width="360" alt="100 mm Cell Dish"> | 100 mm Cell Dish | AutoBio | 独立对象 | cell_dish | cell dish<br>cell dishes<br>cell culture dish<br>cell culture dishes<br>culture dish<br>culture dishes<br>petri dish<br>petri dishes | Cell culture plate for seeding, incubation, washing, and imaging. | [cell_dish_100_vis.obj](files/autobio/autobio/assets/container/cell_dish_100_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/cell_dish_100_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-1-5ml-screw.png" width="360" alt="1.5 mL Screw-Cap Microcentrifuge Tube"> | 1.5 mL Screw-Cap Microcentrifuge Tube | AutoBio | 独立对象 | microcentrifuge_tube_1_5ml | microcentrifuge tube<br>microcentrifuge tubes<br>eppendorf tube<br>eppendorf tubes<br>1.5 ml tube<br>1.5 ml tubes<br>1.5 ml microcentrifuge tube<br>1.5 ml centrifuge tube<br>1.5 ml screw cap tube | Small sample tube for aliquoting, mixing, incubation, and centrifugation. | [centrifuge_1-5ml_screw_vis/](files/autobio/autobio/assets/container/centrifuge_1-5ml_screw_vis) | 可直接按 mesh 渲染 | [源文件](https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/centrifuge_1-5ml_screw_vis) |
| <img src="previews/core/autobio/autobio-centrifuge-10ml.png" width="360" alt="10 mL Centrifuge Tube"> | 10 mL Centrifuge Tube | AutoBio | 独立对象 | centrifuge_tube_10ml | 10 ml centrifuge tube<br>10 ml centrifuge tubes<br>10ml centrifuge tube<br>10 ml tube<br>10 ml tubes | Medium-volume sample tube for transfer and centrifugation. | [centrifuge_10ml_vis.obj](files/autobio/autobio/assets/container/centrifuge_10ml_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/centrifuge_10ml_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-1500ul-open.png" width="360" alt="1.5 mL Open Microcentrifuge Tube"> | 1.5 mL Open Microcentrifuge Tube | AutoBio | 独立对象 | microcentrifuge_tube_1_5ml | microcentrifuge tube<br>microcentrifuge tubes<br>eppendorf tube<br>eppendorf tubes<br>1.5 ml tube<br>1.5 ml tubes<br>1.5 ml microcentrifuge tube<br>1.5 ml centrifuge tube<br>1.5 ml screw cap tube | Open microcentrifuge tube for liquid handling and insertion tasks. | [centrifuge_1500ul_no_lid_vis.obj](files/autobio/autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-15ml-screw.png" width="360" alt="15 mL Screw-Cap Centrifuge Tube"> | 15 mL Screw-Cap Centrifuge Tube | AutoBio | 独立对象 | centrifuge_tube_15ml | 15 ml centrifuge tube<br>15 ml centrifuge tubes<br>15ml centrifuge tube<br>15 ml conical tube<br>15 ml conical tubes<br>15ml conical tube<br>15 ml falcon tube<br>15 ml falcon tubes | Conical sample tube for medium-volume transfer and centrifugation. | [centrifuge_15ml_screw_vis/](files/autobio/autobio/assets/container/centrifuge_15ml_screw_vis) | 可直接按 mesh 渲染 | [源文件](https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/centrifuge_15ml_screw_vis) |
| <img src="previews/core/autobio/autobio-centrifuge-50ml.png" width="360" alt="50 mL Centrifuge Tube"> | 50 mL Centrifuge Tube | AutoBio | 独立对象 | centrifuge_tube_50ml | 50 ml centrifuge tube<br>50 ml centrifuge tubes<br>50ml centrifuge tube<br>50 ml conical tube<br>50 ml conical tubes<br>50ml conical tube<br>50 ml falcon tube<br>50 ml falcon tubes<br>falcon tube<br>falcon tubes | Large conical tube for reagent preparation and centrifugation. | [centrifuge_50ml_vis.obj](files/autobio/autobio/assets/container/centrifuge_50ml_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/centrifuge_50ml_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-50ml-screw.png" width="360" alt="50 mL Screw-Cap Centrifuge Tube"> | 50 mL Screw-Cap Centrifuge Tube | AutoBio | 独立对象 | centrifuge_tube_50ml | 50 ml centrifuge tube<br>50 ml centrifuge tubes<br>50ml centrifuge tube<br>50 ml conical tube<br>50 ml conical tubes<br>50ml conical tube<br>50 ml falcon tube<br>50 ml falcon tubes<br>falcon tube<br>falcon tubes | Large screw-cap tube for sealed transfer and centrifugation. | [centrifuge_50ml_screw_vis/](files/autobio/autobio/assets/container/centrifuge_50ml_screw_vis) | 可直接按 mesh 渲染 | [源文件](https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/centrifuge_50ml_screw_vis) |
| <img src="previews/core/autobio/autobio-cryovial-1-8ml.png" width="360" alt="1.8 mL Cryovial"> | 1.8 mL Cryovial | AutoBio | 独立对象 | cryovial | cryovial<br>cryovials<br>cryo vial<br>cryo vials<br>cryogenic vial<br>cryogenic vials | Cryogenic storage vial for frozen samples and aliquots. | [cryovial_1-8ml_vis/](files/autobio/autobio/assets/container/cryovial_1-8ml_vis) | 可直接按 mesh 渲染 | [源文件](https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/cryovial_1-8ml_vis) |
| <img src="previews/core/autobio/autobio-pcr-plate-96well.png" width="360" alt="96-Well PCR Plate"> | 96-Well PCR Plate | AutoBio | 独立对象 | pcr_plate | pcr plate<br>pcr plates<br>96 well pcr plate<br>96 well pcr plates<br>96 well plate<br>96 well plates<br>96 well microplate<br>96 well microplates | Plate for PCR setup, thermal cycling, and sample organization. | [pcr_plate_96well_vis.obj](files/autobio/autobio/assets/container/pcr_plate_96well_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/container/pcr_plate_96well_vis.obj) |
| <img src="previews/core/autobio/autobio-tip-200ul.png" width="360" alt="200 uL Pipette Tip"> | 200 uL Pipette Tip | AutoBio | 独立对象 | pipette_tip | pipette tip<br>pipette tips<br>micropipette tip<br>micropipette tips<br>200 ul tip<br>200 ul tips<br>200 ul pipette tip<br>200 ul pipette tips | Disposable liquid-handling tip for pipetting small volumes. | [visual.obj](files/autobio/autobio/assets/container/tip_200ul_vis/visual.obj) | 可直接按 mesh 渲染 | [源文件](https://github.com/autobio-bench/AutoBio/tree/main/autobio/assets/container/tip_200ul_vis) |
| <img src="previews/core/autobio/autobio-pipette.png" width="360" alt="Micropipette"> | Micropipette | AutoBio | 组合对象 | pipette | pipette<br>pipettes<br>micropipette<br>micropipettes<br>single channel pipette<br>single channel pipettes | Manual pipette for aspirating and dispensing liquids. | [pipette.gen.xml](files/autobio/autobio/model/object/pipette.gen.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/object/pipette.gen.xml) |
| <img src="previews/core/autobio/autobio-tip-box-24slot.png" width="360" alt="24-Slot Tip Box"> | 24-Slot Tip Box | AutoBio | 独立对象 | tip_box | tip box<br>tip boxes<br>pipette tip box<br>pipette tip boxes | Container for storing and presenting pipette tips. | [tip_box_24slot_vis.obj](files/autobio/autobio/assets/rack/tip_box_24slot_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/tip_box_24slot_vis.obj) |
| <img src="previews/core/autobio/autobio-pipette-rack-tri.png" width="360" alt="Triangular Pipette Rack"> | Triangular Pipette Rack | AutoBio | 独立对象 | pipette_rack | pipette rack<br>pipette racks<br>pipette holder<br>pipette holders<br>pipette stand<br>pipette stands | Rack for holding pipettes upright between operations. | [pipette_rack_tri_vis.obj](files/autobio/autobio/assets/rack/pipette_rack_tri_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/pipette_rack_tri_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-10slot-rack.png" width="360" alt="10-Slot Centrifuge Tube Rack"> | 10-Slot Centrifuge Tube Rack | AutoBio | 独立对象 | tube_rack | tube rack<br>tube racks<br>centrifuge tube rack<br>centrifuge tube racks<br>microcentrifuge tube rack<br>microcentrifuge tube racks<br>test tube rack<br>test tube racks | Rack for organizing and positioning sample tubes. | [centrifuge_10slot_vis.obj](files/autobio/autobio/assets/rack/centrifuge_10slot_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/centrifuge_10slot_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-plate-60well.png" width="360" alt="60-Well Plate Rack"> | 60-Well Plate Rack | AutoBio | 独立对象 | tube_rack | tube rack<br>tube racks<br>centrifuge tube rack<br>centrifuge tube racks<br>microcentrifuge tube rack<br>microcentrifuge tube racks<br>test tube rack<br>test tube racks | Multi-well rack for arranging small tubes or vials. | [centrifuge_plate_60well_vis.obj](files/autobio/autobio/assets/rack/centrifuge_plate_60well_vis.obj) | 可直接按 mesh 渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/assets/rack/centrifuge_plate_60well_vis.obj) |
| <img src="previews/core/autobio/autobio-centrifuge-5430.png" width="360" alt="Eppendorf 5430 Centrifuge"> | Eppendorf 5430 Centrifuge | AutoBio | 组合对象 | centrifuge | centrifuge<br>centrifuges<br>microcentrifuge<br>microcentrifuges<br>bench centrifuge<br>bench centrifuges<br>refrigerated centrifuge<br>refrigerated centrifuges | Bench centrifuge for spinning small sample tubes. | [centrifuge_eppendorf_5430.xml](files/autobio/autobio/model/instrument/centrifuge_eppendorf_5430.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/centrifuge_eppendorf_5430.xml) |
| <img src="previews/core/autobio/autobio-centrifuge-5910-ri.png" width="360" alt="Eppendorf 5910 Ri Centrifuge"> | Eppendorf 5910 Ri Centrifuge | AutoBio | 组合对象 | centrifuge | centrifuge<br>centrifuges<br>microcentrifuge<br>microcentrifuges<br>bench centrifuge<br>bench centrifuges<br>refrigerated centrifuge<br>refrigerated centrifuges | Large refrigerated centrifuge for higher-volume tube spinning. | [centrifuge_eppendorf_5910_ri.xml](files/autobio/autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml) |
| <img src="previews/core/autobio/autobio-centrifuge-tgear-mini.png" width="360" alt="Tiangen Tgear Mini Centrifuge"> | Tiangen Tgear Mini Centrifuge | AutoBio | 组合对象 | centrifuge | centrifuge<br>centrifuges<br>microcentrifuge<br>microcentrifuges<br>bench centrifuge<br>bench centrifuges<br>refrigerated centrifuge<br>refrigerated centrifuges | Compact mini centrifuge for quick spin-down operations. | [centrifuge_tiangen_tgear_mini.xml](files/autobio/autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml) |
| <img src="previews/core/autobio/autobio-thermal-cycler-c1000.png" width="360" alt="Bio-Rad C1000 Thermal Cycler"> | Bio-Rad C1000 Thermal Cycler | AutoBio | 组合对象 | thermal_cycler | thermal cycler<br>thermal cyclers<br>thermocycler<br>thermocyclers<br>pcr machine<br>pcr machines | PCR instrument for running thermal cycling programs. | [thermal_cycler_biorad_c1000.xml](files/autobio/autobio/model/instrument/thermal_cycler_biorad_c1000.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/thermal_cycler_biorad_c1000.xml) |
| <img src="previews/core/autobio/autobio-thermal-mixer-eppendorf-c.png" width="360" alt="Eppendorf C Thermal Mixer"> | Eppendorf C Thermal Mixer | AutoBio | 组合对象 | thermal_mixer | thermal mixer<br>thermal mixers<br>thermomixer<br>thermomixers<br>heat shaker<br>heat shakers | Instrument for controlled heating and shaking of samples. | [thermal_mixer_eppendorf_c.xml](files/autobio/autobio/model/instrument/thermal_mixer_eppendorf_c.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/thermal_mixer_eppendorf_c.xml) |
| <img src="previews/core/autobio/autobio-vortex-mixer-genie-2.png" width="360" alt="Genie 2 Vortex Mixer"> | Genie 2 Vortex Mixer | AutoBio | 组合对象 | vortex_mixer | vortex mixer<br>vortex mixers<br>vortexer<br>vortexers<br>vortex genie | Mixer for vortexing tubes and suspensions. | [vortex_mixer_genie_2.xml](files/autobio/autobio/model/instrument/vortex_mixer_genie_2.xml) | 可直接按 MJCF 装配渲染 | [源文件](https://raw.githubusercontent.com/autobio-bench/AutoBio/main/autobio/model/instrument/vortex_mixer_genie_2.xml) |
| <img src="previews/core/labutopia/labutopia-beaker-family.png" width="360" alt="Beaker Family"> | Beaker Family | LabUtopia | 场景内对象引用 | beaker | beaker<br>beakers<br>glass beaker<br>glass beakers | General glass container for mixing, pouring, heating, and transfer. | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd)<br><code>#/World/beaker</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/core/labutopia/labutopia-conical-bottle-family.png" width="360" alt="Conical Bottle / Flask Family"> | Conical Bottle / Flask Family | LabUtopia | 场景内对象引用 | conical_bottle | conical bottle<br>conical bottles<br>erlenmeyer flask<br>erlenmeyer flasks<br>conical flask<br>conical flasks | Flask-style glassware for liquid storage, mixing, and pouring. | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd)<br><code>#/World/conical_bottle02</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/core/labutopia/labutopia-graduated-cylinder-03.png" width="360" alt="Graduated Cylinder"> | Graduated Cylinder | LabUtopia | 场景内对象引用 | graduated_cylinder | graduated cylinder<br>graduated cylinders<br>measuring cylinder<br>measuring cylinders | Volumetric cylinder for measuring and dispensing liquids. | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd)<br><code>#/World/graduated_cylinder_03</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/core/labutopia/labutopia-glass-rod.png" width="360" alt="Glass Rod"> | Glass Rod | LabUtopia | 场景内对象引用 | glass_rod | glass rod<br>glass rods<br>stirring rod<br>stirring rods<br>glass stirring rod<br>glass stirring rods | Rod for manual stirring and mixing. | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd)<br><code>#/World/glass_rod</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/lab_003.usd) |
| <img src="previews/core/labutopia/labutopia-test-tube-rack.png" width="360" alt="Test Tube Rack"> | Test Tube Rack | LabUtopia | 场景内对象引用 | tube_rack | tube rack<br>tube racks<br>centrifuge tube rack<br>centrifuge tube racks<br>microcentrifuge tube rack<br>microcentrifuge tube racks<br>test tube rack<br>test tube racks | Rack for holding tubes upright during preparation and storage. | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd)<br><code>#/World/test_tube_rack</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/core/labutopia/labutopia-drying-box-family.png" width="360" alt="Drying Box Family"> | Drying Box Family | LabUtopia | 场景内对象引用 | drying_box | drying box<br>drying boxes<br>dry box<br>dry boxes<br>drying oven<br>drying ovens<br>drying chamber<br>drying chambers | Device used for drying or enclosed heating workflows. | [lab_001.usd](files/labutopia/assets/chemistry_lab/lab_001/lab_001.usd)<br><code>#/World/DryingBox_01</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_001/lab_001.usd) |
| <img src="previews/core/labutopia/labutopia-heat-device.png" width="360" alt="Heat Device / Hot Plate"> | Heat Device / Hot Plate | LabUtopia | 场景内对象引用 | heating_device | hot plate<br>hot plates<br>heating plate<br>heating plates<br>heating device<br>heating devices<br>heat device<br>heat devices<br>heater<br>heaters | Heating surface or device used to activate thermal tasks. | [lab_003.usd](files/labutopia/assets/chemistry_lab/lab_003/lab_003.usd)<br><code>#/World/heat_device</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/lab_003/lab_003.usd) |
| <img src="previews/core/labutopia/labutopia-muffle-furnace.png" width="360" alt="Muffle Furnace"> | Muffle Furnace | LabUtopia | 场景内对象引用 | muffle_furnace | muffle furnace<br>muffle furnaces<br>laboratory furnace<br>laboratory furnaces | High-temperature heating device for enclosed furnace operations. | [Scene1_hard.usd](files/labutopia/assets/chemistry_lab/hard_task/Scene1_hard.usd)<br><code>#/World/MuffleFurnace</code> | 当前使用 USD 场景缩略图展示 | [源文件](https://media.githubusercontent.com/media/Rui-li023/LabUtopia/main/assets/chemistry_lab/hard_task/Scene1_hard.usd) |

## 6. 当前结论

- 现在的目录口径已经从“只看 asset”改成“统一看实验室条目”。
- `AutoBio` 更适合提供独立对象、组合对象和可执行的完整场景。
- `LabUtopia` 更适合提供场景内对象引用、化学实验室场景和场景上下文。
- 后续如果要继续扩 benchmark，优先在这份核心条目表上补别名、补用途、补协议匹配结果，而不是再分叉新的清单文件。
