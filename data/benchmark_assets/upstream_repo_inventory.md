# AutoBio / LabUtopia 上游结构清单

这份文档只做两件事：

1. 把 `AutoBio` 和 `LabUtopia` 里的 `scene / asset / composite asset / scene object reference` 分清楚
2. 给出每一类的实际路径和预览图

## 1. 先记住四个概念

| 术语 | 中文解释 | 典型例子 |
|---|---|---|
| `scene` | 整个实验环境入口，打开后看到的是整张实验台或整个实验室 | `autobio/model/scene/lab.xml`、`assets/chemistry_lab/lab_001/lab_001.usd` |
| `asset (standalone_mesh_root)` | 单个对象的独立 mesh 根入口 | `autobio/assets/container/pcr_plate_96well_vis.obj` |
| `composite asset (package_entrypoint)` | 单个对象的装配入口文件，会继续引用多个 mesh / 部件 | `autobio/model/instrument/centrifuge_eppendorf_5430.xml` |
| `scene object reference (scene_prim_reference)` | scene 里的某个对象路径，本身不是独立文件 | `assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02` |

一眼判断规则：

1. 加载后如果出来的是完整环境，就是 `scene`
2. 如果长得像 `xxx.usd#/World/...`，就是 `scene object reference`
3. 如果它是单对象 mesh 根文件，就是 `asset`
4. 如果它是单对象入口文件，但会继续引用很多部件，就是 `composite asset`

## 2. AutoBio

- 组织方式：`asset-first + scene xml`
- `scene` 主入口：`autobio/model/scene/`
- `composite asset` 主入口：`autobio/model/object/`、`autobio/model/instrument/`、`autobio/model/robot/`、`autobio/model/hand/`
- `asset` / raw mesh 主入口：`autobio/assets/container/`、`autobio/assets/rack/`、`autobio/assets/tool/`、`autobio/assets/instrument/`、`autobio/assets/robot/`

### 2.1 AutoBio scenes

| Preview | Scene | Path |
| --- | --- | --- |
| <img src="previews/autobio/scenes/bottlecap.png" width="160" alt="bottlecap"> | bottlecap | `autobio/model/scene/bottlecap.xml` |
| <img src="previews/autobio/scenes/gallery.png" width="160" alt="gallery"> | gallery | `autobio/model/scene/gallery.xml` |
| <img src="previews/autobio/scenes/gallery2.png" width="160" alt="gallery2"> | gallery2 | `autobio/model/scene/gallery2.xml` |
| <img src="previews/autobio/scenes/insert.png" width="160" alt="insert"> | insert | `autobio/model/scene/insert.xml` |
| <img src="previews/autobio/scenes/insert-centrifuge-5430.png" width="160" alt="insert_centrifuge_5430"> | insert_centrifuge_5430 | `autobio/model/scene/insert_centrifuge_5430.xml` |
| <img src="previews/autobio/scenes/lab.png" width="160" alt="lab"> | lab | `autobio/model/scene/lab.xml` |
| <img src="previews/autobio/scenes/lab-screw-all.png" width="160" alt="lab_screw_all"> | lab_screw_all | `autobio/model/scene/lab_screw_all.xml` |
| <img src="previews/autobio/scenes/lab-screw-tighten.png" width="160" alt="lab_screw_tighten"> | lab_screw_tighten | `autobio/model/scene/lab_screw_tighten.xml` |
| <img src="previews/autobio/scenes/mani-centrifuge-5430.png" width="160" alt="mani_centrifuge_5430"> | mani_centrifuge_5430 | `autobio/model/scene/mani_centrifuge_5430.xml` |
| <img src="previews/autobio/scenes/mani-centrifuge-5910.png" width="160" alt="mani_centrifuge_5910"> | mani_centrifuge_5910 | `autobio/model/scene/mani_centrifuge_5910.xml` |
| <img src="previews/autobio/scenes/mani-centrifuge-mini.png" width="160" alt="mani_centrifuge_mini"> | mani_centrifuge_mini | `autobio/model/scene/mani_centrifuge_mini.xml` |
| <img src="previews/autobio/scenes/mani-pipette.png" width="160" alt="mani_pipette"> | mani_pipette | `autobio/model/scene/mani_pipette.xml` |
| <img src="previews/autobio/scenes/mani-thermal-cycler.png" width="160" alt="mani_thermal_cycler"> | mani_thermal_cycler | `autobio/model/scene/mani_thermal_cycler.xml` |
| <img src="previews/autobio/scenes/mani-thermal-mixer.png" width="160" alt="mani_thermal_mixer"> | mani_thermal_mixer | `autobio/model/scene/mani_thermal_mixer.xml` |
| <img src="previews/autobio/scenes/pickup.png" width="160" alt="pickup"> | pickup | `autobio/model/scene/pickup.xml` |
| <img src="previews/autobio/scenes/screw.png" width="160" alt="screw"> | screw | `autobio/model/scene/screw.xml` |
| <img src="previews/autobio/scenes/screw-test.png" width="160" alt="screw_test"> | screw_test | `autobio/model/scene/screw_test.xml` |
| <img src="previews/autobio/scenes/screw-v3.png" width="160" alt="screw_v3"> | screw_v3 | `autobio/model/scene/screw_v3.xml` |
| <img src="previews/autobio/scenes/vortex-mixer.png" width="160" alt="vortex_mixer"> | vortex_mixer | `autobio/model/scene/vortex_mixer.xml` |

### 2.2 AutoBio composite assets

说明：`object/` 目录里若同时存在 `.xml` 与 `.gen.xml`，这里按同一资产 family 合并展示。

| Preview | Category | Name | Path |
| --- | --- | --- | --- |
| <img src="previews/autobio/composite/object-cell-dish-100.png" width="160" alt="cell_dish_100"> | object | cell_dish_100 | `autobio/model/object/cell_dish_100.xml`<br>`autobio/model/object/cell_dish_100.gen.xml` |
| <img src="previews/autobio/composite/object-centrifuge-1-5ml.png" width="160" alt="centrifuge_1-5ml"> | object | centrifuge_1-5ml | `autobio/model/object/centrifuge_1-5ml.xml` |
| <img src="previews/autobio/composite/object-centrifuge-1-5ml-screw.png" width="160" alt="centrifuge_1-5ml_screw"> | object | centrifuge_1-5ml_screw | `autobio/model/object/centrifuge_1-5ml_screw.xml` |
| <img src="previews/autobio/composite/object-centrifuge-1-5ml-screw-simple.png" width="160" alt="centrifuge_1-5ml_screw-simple"> | object | centrifuge_1-5ml_screw-simple | `autobio/model/object/centrifuge_1-5ml_screw-simple.xml` |
| <img src="previews/autobio/composite/object-centrifuge-10ml.png" width="160" alt="centrifuge_10ml"> | object | centrifuge_10ml | `autobio/model/object/centrifuge_10ml.xml`<br>`autobio/model/object/centrifuge_10ml.gen.xml` |
| <img src="previews/autobio/composite/object-centrifuge-10slot.png" width="160" alt="centrifuge_10slot"> | object | centrifuge_10slot | `autobio/model/object/centrifuge_10slot.xml`<br>`autobio/model/object/centrifuge_10slot.gen.xml` |
| <img src="previews/autobio/composite/object-centrifuge-1500ul-no-lid.png" width="160" alt="centrifuge_1500ul_no_lid"> | object | centrifuge_1500ul_no_lid | `autobio/model/object/centrifuge_1500ul_no_lid.xml`<br>`autobio/model/object/centrifuge_1500ul_no_lid.gen.xml` |
| <img src="previews/autobio/composite/object-centrifuge-15ml.png" width="160" alt="centrifuge_15ml"> | object | centrifuge_15ml | `autobio/model/object/centrifuge_15ml.xml` |
| <img src="previews/autobio/composite/object-centrifuge-15ml-screw.png" width="160" alt="centrifuge_15ml_screw"> | object | centrifuge_15ml_screw | `autobio/model/object/centrifuge_15ml_screw.xml` |
| <img src="previews/autobio/composite/object-centrifuge-50ml.png" width="160" alt="centrifuge_50ml"> | object | centrifuge_50ml | `autobio/model/object/centrifuge_50ml.xml`<br>`autobio/model/object/centrifuge_50ml.gen.xml` |
| <img src="previews/autobio/composite/object-centrifuge-50ml-screw.png" width="160" alt="centrifuge_50ml_screw"> | object | centrifuge_50ml_screw | `autobio/model/object/centrifuge_50ml_screw.xml` |
| <img src="previews/autobio/composite/object-centrifuge-plate-60well.png" width="160" alt="centrifuge_plate_60well"> | object | centrifuge_plate_60well | `autobio/model/object/centrifuge_plate_60well.xml`<br>`autobio/model/object/centrifuge_plate_60well.gen.xml` |
| <img src="previews/autobio/composite/object-cryovial-1-8ml.png" width="160" alt="cryovial_1-8ml"> | object | cryovial_1-8ml | `autobio/model/object/cryovial_1-8ml.xml` |
| <img src="previews/autobio/composite/object-pcr-plate-96well.png" width="160" alt="pcr_plate_96well"> | object | pcr_plate_96well | `autobio/model/object/pcr_plate_96well.xml`<br>`autobio/model/object/pcr_plate_96well.gen.xml` |
| <img src="previews/autobio/composite/object-pipette.png" width="160" alt="pipette"> | object | pipette | `autobio/model/object/pipette.xml`<br>`autobio/model/object/pipette.gen.xml` |
| <img src="previews/autobio/composite/object-pipette-rack.png" width="160" alt="pipette_rack"> | object | pipette_rack | `autobio/model/object/pipette_rack.xml`<br>`autobio/model/object/pipette_rack.gen.xml` |
| <img src="previews/autobio/composite/object-pipette-tip.png" width="160" alt="pipette_tip"> | object | pipette_tip | `autobio/model/object/pipette_tip.xml`<br>`autobio/model/object/pipette_tip.gen.xml` |
| <img src="previews/autobio/composite/object-tip-box.png" width="160" alt="tip_box"> | object | tip_box | `autobio/model/object/tip_box.xml`<br>`autobio/model/object/tip_box.gen.xml` |
| <img src="previews/autobio/composite/instrument-centrifuge-eppendorf-5430.png" width="160" alt="centrifuge_eppendorf_5430"> | instrument | centrifuge_eppendorf_5430 | `autobio/model/instrument/centrifuge_eppendorf_5430.xml` |
| <img src="previews/autobio/composite/instrument-centrifuge-eppendorf-5910-ri.png" width="160" alt="centrifuge_eppendorf_5910_ri"> | instrument | centrifuge_eppendorf_5910_ri | `autobio/model/instrument/centrifuge_eppendorf_5910_ri.xml` |
| <img src="previews/autobio/composite/instrument-centrifuge-tiangen-tgear-mini.png" width="160" alt="centrifuge_tiangen_tgear_mini"> | instrument | centrifuge_tiangen_tgear_mini | `autobio/model/instrument/centrifuge_tiangen_tgear_mini.xml` |
| <img src="previews/autobio/composite/instrument-thermal-cycler-biorad-c1000.png" width="160" alt="thermal_cycler_biorad_c1000"> | instrument | thermal_cycler_biorad_c1000 | `autobio/model/instrument/thermal_cycler_biorad_c1000.xml` |
| <img src="previews/autobio/composite/instrument-thermal-mixer-eppendorf-c.png" width="160" alt="thermal_mixer_eppendorf_c"> | instrument | thermal_mixer_eppendorf_c | `autobio/model/instrument/thermal_mixer_eppendorf_c.xml` |
| <img src="previews/autobio/composite/instrument-vortex-mixer-genie-2.png" width="160" alt="vortex_mixer_genie_2"> | instrument | vortex_mixer_genie_2 | `autobio/model/instrument/vortex_mixer_genie_2.xml` |
| <img src="previews/autobio/composite/robot-2f85.png" width="160" alt="2f85"> | robot | 2f85 | `autobio/model/robot/2f85.xml` |
| <img src="previews/autobio/composite/robot-aloha-left.png" width="160" alt="aloha_left"> | robot | aloha_left | `autobio/model/robot/aloha_left.xml` |
| <img src="previews/autobio/composite/robot-dualrm.png" width="160" alt="dualrm"> | robot | dualrm | `autobio/model/robot/dualrm.xml` |
| <img src="previews/autobio/composite/robot-piper.png" width="160" alt="piper"> | robot | piper | `autobio/model/robot/piper.xml` |
| <img src="previews/autobio/composite/robot-ur5e-dexhand021-right.png" width="160" alt="ur5e_dexhand021_right"> | robot | ur5e_dexhand021_right | `autobio/model/robot/ur5e_dexhand021_right.xml` |
| <img src="previews/autobio/composite/robot-ur5e-gripper.png" width="160" alt="ur5e_gripper"> | robot | ur5e_gripper | `autobio/model/robot/ur5e_gripper.xml` |
| <img src="previews/autobio/composite/hand-dexhand021-right.png" width="160" alt="dexhand021_right"> | hand | dexhand021_right | `autobio/model/hand/dexhand021_right.xml` |
| <img src="previews/autobio/composite/hand-shadowhand-left.png" width="160" alt="shadowhand_left"> | hand | shadowhand_left | `autobio/model/hand/shadowhand_left.xml` |
| <img src="previews/autobio/composite/hand-shadowhand-right.png" width="160" alt="shadowhand_right"> | hand | shadowhand_right | `autobio/model/hand/shadowhand_right.xml` |
| <img src="previews/autobio/composite/hand-shadowhand-right-mjx.png" width="160" alt="shadowhand_right_mjx"> | hand | shadowhand_right_mjx | `autobio/model/hand/shadowhand_right_mjx.xml` |

### 2.3 AutoBio standalone assets / raw mesh roots

| Preview | Name | Path |
| --- | --- | --- |
| <img src="previews/autobio/standalone/cell-dish-100-vis.png" width="160" alt="cell_dish_100_vis"> | cell_dish_100_vis | `autobio/assets/container/cell_dish_100_vis.obj` |
| <img src="previews/autobio/standalone/centrifuge-1-5ml-screw-vis.png" width="160" alt="centrifuge_1-5ml_screw_vis"> | centrifuge_1-5ml_screw_vis | `autobio/assets/container/centrifuge_1-5ml_screw_vis` |
| <img src="previews/autobio/standalone/centrifuge-10ml-vis.png" width="160" alt="centrifuge_10ml_vis"> | centrifuge_10ml_vis | `autobio/assets/container/centrifuge_10ml_vis.obj` |
| <img src="previews/autobio/standalone/centrifuge-1500ul-no-lid-vis.png" width="160" alt="centrifuge_1500ul_no_lid_vis"> | centrifuge_1500ul_no_lid_vis | `autobio/assets/container/centrifuge_1500ul_no_lid_vis.obj` |
| <img src="previews/autobio/standalone/centrifuge-15ml-screw-vis.png" width="160" alt="centrifuge_15ml_screw_vis"> | centrifuge_15ml_screw_vis | `autobio/assets/container/centrifuge_15ml_screw_vis` |
| <img src="previews/autobio/standalone/centrifuge-50ml-vis.png" width="160" alt="centrifuge_50ml_vis"> | centrifuge_50ml_vis | `autobio/assets/container/centrifuge_50ml_vis.obj` |
| <img src="previews/autobio/standalone/centrifuge-50ml-screw-vis.png" width="160" alt="centrifuge_50ml_screw_vis"> | centrifuge_50ml_screw_vis | `autobio/assets/container/centrifuge_50ml_screw_vis` |
| <img src="previews/autobio/standalone/cryovial-1-8ml-vis.png" width="160" alt="cryovial_1-8ml_vis"> | cryovial_1-8ml_vis | `autobio/assets/container/cryovial_1-8ml_vis` |
| <img src="previews/autobio/standalone/pcr-plate-96well-vis.png" width="160" alt="pcr_plate_96well_vis"> | pcr_plate_96well_vis | `autobio/assets/container/pcr_plate_96well_vis.obj` |
| <img src="previews/autobio/standalone/tip-200ul-vis.png" width="160" alt="tip_200ul_vis"> | tip_200ul_vis | `autobio/assets/container/tip_200ul_vis` |
| <img src="previews/autobio/standalone/centrifuge-10slot-vis.png" width="160" alt="centrifuge_10slot_vis"> | centrifuge_10slot_vis | `autobio/assets/rack/centrifuge_10slot_vis.obj` |
| <img src="previews/autobio/standalone/centrifuge-plate-60well-vis.png" width="160" alt="centrifuge_plate_60well_vis"> | centrifuge_plate_60well_vis | `autobio/assets/rack/centrifuge_plate_60well_vis.obj` |
| <img src="previews/autobio/standalone/pipette-rack-tri-vis.png" width="160" alt="pipette_rack_tri_vis"> | pipette_rack_tri_vis | `autobio/assets/rack/pipette_rack_tri_vis.obj` |
| <img src="previews/autobio/standalone/tip-box-24slot-vis.png" width="160" alt="tip_box_24slot_vis"> | tip_box_24slot_vis | `autobio/assets/rack/tip_box_24slot_vis.obj` |
| <img src="previews/autobio/standalone/pipette.png" width="160" alt="pipette"> | pipette | `autobio/assets/tool/pipette` |
| <img src="previews/autobio/standalone/centrifuge-eppendorf-5430.png" width="160" alt="centrifuge_eppendorf_5430"> | centrifuge_eppendorf_5430 | `autobio/assets/instrument/centrifuge_eppendorf_5430` |
| <img src="previews/autobio/standalone/centrifuge-eppendorf-5910-ri.png" width="160" alt="centrifuge_eppendorf_5910_ri"> | centrifuge_eppendorf_5910_ri | `autobio/assets/instrument/centrifuge_eppendorf_5910_ri` |
| <img src="previews/autobio/standalone/centrifuge-tiangen-tgear-mini.png" width="160" alt="centrifuge_tiangen_tgear_mini"> | centrifuge_tiangen_tgear_mini | `autobio/assets/instrument/centrifuge_tiangen_tgear_mini` |
| <img src="previews/autobio/standalone/thermal-cycler-biorad-c1000.png" width="160" alt="thermal_cycler_biorad_c1000"> | thermal_cycler_biorad_c1000 | `autobio/assets/instrument/thermal_cycler_biorad_c1000` |
| <img src="previews/autobio/standalone/thermal-mixer-eppendorf-c.png" width="160" alt="thermal_mixer_eppendorf_c"> | thermal_mixer_eppendorf_c | `autobio/assets/instrument/thermal_mixer_eppendorf_c` |
| <img src="previews/autobio/standalone/vortex-mixer-genie-2.png" width="160" alt="vortex_mixer_genie_2"> | vortex_mixer_genie_2 | `autobio/assets/instrument/vortex_mixer_genie_2` |
| <img src="previews/autobio/standalone/aloha2.png" width="160" alt="aloha2"> | aloha2 | `autobio/assets/robot/aloha2` |
| <img src="previews/autobio/standalone/dexhand021.png" width="160" alt="dexhand021"> | dexhand021 | `autobio/assets/robot/dexhand021` |
| <img src="previews/autobio/standalone/robotiq.png" width="160" alt="robotiq"> | robotiq | `autobio/assets/robot/robotiq` |
| <img src="previews/autobio/standalone/ur5e.png" width="160" alt="ur5e"> | ur5e | `autobio/assets/robot/ur5e` |

## 3. LabUtopia

- 组织方式：`scene-first USD`
- 主入口是 `scene`，不是对象级独立 mesh
- 当前 benchmark 里使用的主要是 `scene object reference`
- 下面的对象预览图目前使用的是“scene 缩略图 + 对象标签”，因为当前还没有把这些对象从 USD scene 里独立抽取出来

### 3.1 LabUtopia scenes

| Preview | Type | Scene | Path |
| --- | --- | --- | --- |
| <img src="previews/labutopia/scenes/lab-001.png" width="160" alt="lab_001"> | chemistry main scene | lab_001 | `assets/chemistry_lab/lab_001/lab_001.usd` |
| <img src="previews/labutopia/scenes/lab-003.png" width="160" alt="lab_003"> | chemistry main scene | lab_003 | `assets/chemistry_lab/lab_003/lab_003.usd` |
| <img src="previews/labutopia/scenes/scene1-hard.png" width="160" alt="Scene1_hard"> | chemistry main scene | Scene1_hard | `assets/chemistry_lab/hard_task/Scene1_hard.usd` |
| <img src="previews/labutopia/scenes/clock.png" width="160" alt="clock"> | chemistry special scene | clock | `assets/chemistry_lab/lab_003/clock.usd` |
| <img src="previews/labutopia/scenes/navigation-lab-01.png" width="160" alt="navigation_lab_01"> | navigation scene | navigation_lab_01 | `assets/navigation_lab/navigation_lab_01/lab.usd` |

### 3.2 Chemistry USD files visible in the repo

| Preview | Classification | Path |
| --- | --- | --- |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-lab-001-lab-001-usd.png" width="160" alt="assets/chemistry_lab/lab_001/lab_001.usd"> | main scene | `assets/chemistry_lab/lab_001/lab_001.usd` |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-lab-003-lab-003-usd.png" width="160" alt="assets/chemistry_lab/lab_003/lab_003.usd"> | main scene | `assets/chemistry_lab/lab_003/lab_003.usd` |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-scene1-hard-usd.png" width="160" alt="assets/chemistry_lab/hard_task/Scene1_hard.usd"> | main scene | `assets/chemistry_lab/hard_task/Scene1_hard.usd` |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-lab-003-clock-usd.png" width="160" alt="assets/chemistry_lab/lab_003/clock.usd"> | special scene | `assets/chemistry_lab/lab_003/clock.usd` |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-lab-004-usd.png" width="160" alt="assets/chemistry_lab/hard_task/lab_004.usd"> | auxiliary USD | `assets/chemistry_lab/hard_task/lab_004.usd` |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-hard-task-subusds-lab-015-usd.png" width="160" alt="assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd"> | SubUSD | `assets/chemistry_lab/hard_task/SubUSDs/lab_015.usd` |
| <img src="previews/labutopia/chem_usd/assets-chemistry-lab-lab-003-subusds-lab-015-usd.png" width="160" alt="assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd"> | SubUSD | `assets/chemistry_lab/lab_003/SubUSDs/lab_015.usd` |

### 3.3 LabUtopia scene object families

| Representative Preview | Family | Scene Object Paths |
| --- | --- | --- |
| <img src="previews/labutopia/scene_objects/cabinet.png" width="160" alt="cabinet"> | cabinet | `/World/Cabinet_01`<br>`/World/Cabinet_02` |
| <img src="previews/labutopia/scene_objects/drying-box.png" width="160" alt="drying box"> | drying box | `/World/DryingBox_01`<br>`/World/DryingBox_02`<br>`/World/DryingBox_03` |
| <img src="previews/labutopia/scene_objects/button.png" width="160" alt="button"> | button | `/World/DryingBox_01/button`<br>`/World/heat_device/button` |
| <img src="previews/labutopia/scene_objects/beaker.png" width="160" alt="beaker"> | beaker | `/World/beaker1`<br>`/World/beaker2`<br>`/World/beaker3`<br>`/World/beaker_2`<br>`/World/target_beaker` |
| <img src="previews/labutopia/scene_objects/conical-bottle.png" width="160" alt="conical bottle"> | conical bottle | `/World/conical_bottle02`<br>`/World/conical_bottle03`<br>`/World/conical_bottle04` |
| <img src="previews/labutopia/scene_objects/glass-rod.png" width="160" alt="glass rod"> | glass rod | `/World/glass_rod` |
| <img src="previews/labutopia/scene_objects/graduated-cylinder.png" width="160" alt="graduated cylinder"> | graduated cylinder | `/World/graduated_cylinder_03` |
| <img src="previews/labutopia/scene_objects/heat-device.png" width="160" alt="heat device"> | heat device | `/World/heat_device` |
| <img src="previews/labutopia/scene_objects/muffle-furnace.png" width="160" alt="muffle furnace"> | muffle furnace | `/World/MuffleFurnace` |
| <img src="previews/labutopia/scene_objects/rack-platform.png" width="160" alt="rack / platform"> | rack / platform | `/World/target_plat` |
| <img src="previews/labutopia/scene_objects/table-surface.png" width="160" alt="table surface"> | table surface | `/World/table/surface`<br>`/World/table/surface/mesh` |

### 3.4 LabUtopia benchmark scene object entries

| Preview | Name | Path |
| --- | --- | --- |
| <img src="previews/labutopia/catalog/labutopia-beaker-family.png" width="160" alt="Beaker Family"> | Beaker Family | `assets/chemistry_lab/lab_001/lab_001.usd#/World/beaker` |
| <img src="previews/labutopia/catalog/labutopia-conical-bottle-family.png" width="160" alt="Conical Bottle / Flask Family"> | Conical Bottle / Flask Family | `assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02` |
| <img src="previews/labutopia/catalog/labutopia-graduated-cylinder-03.png" width="160" alt="Graduated Cylinder"> | Graduated Cylinder | `assets/chemistry_lab/lab_001/lab_001.usd#/World/graduated_cylinder_03` |
| <img src="previews/labutopia/catalog/labutopia-glass-rod.png" width="160" alt="Glass Rod"> | Glass Rod | `assets/chemistry_lab/lab_003/lab_003.usd#/World/glass_rod` |
| <img src="previews/labutopia/catalog/labutopia-test-tube-rack.png" width="160" alt="Test Tube Rack"> | Test Tube Rack | `assets/chemistry_lab/lab_001/lab_001.usd#/World/test_tube_rack` |
| <img src="previews/labutopia/catalog/labutopia-drying-box-family.png" width="160" alt="Drying Box Family"> | Drying Box Family | `assets/chemistry_lab/lab_001/lab_001.usd#/World/DryingBox_01` |
| <img src="previews/labutopia/catalog/labutopia-heat-device.png" width="160" alt="Heat Device / Hot Plate"> | Heat Device / Hot Plate | `assets/chemistry_lab/lab_003/lab_003.usd#/World/heat_device` |
| <img src="previews/labutopia/catalog/labutopia-muffle-furnace.png" width="160" alt="Muffle Furnace"> | Muffle Furnace | `assets/chemistry_lab/hard_task/Scene1_hard.usd#/World/MuffleFurnace` |

### 3.5 LabUtopia support files

| Type | Count |
|---|---:|
| `.usd` | 7 |
| `.mdl` | 260 |
| `.jpg` | 75 |
| `.png` | 28 |

这些 `materials / textures / SubUSDs` 是 support files，不应该直接算作独立实验资产。

## 4. 当前 benchmark 主清单和仓库全量结构的关系

- `AutoBio` 当前 benchmark 主清单：`14 x asset + 7 x composite asset`
- `LabUtopia` 当前 benchmark 主清单：`8 x scene object reference`
- 这些数字都只是 benchmark 现在实际使用的条目，不是两个仓库的全量资产数
