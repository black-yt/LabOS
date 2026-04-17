# AutoBio 与 LabUtopia 的 Assets / Actions 全量梳理

## 1. 文档目的

这份文档只做一件事：

- 把 `AutoBio` 和 `LabUtopia` 中与 benchmark 直接相关的 `assets`、`actions`、`scenes`、`tasks`、`controller`、`runtime interface` 系统梳理出来。

目标不是复述论文，而是为后续三件事服务：

1. 给 `Level 1: Asset Understanding` 提供资产池
2. 给 `Level 2: Long-Horizon Planning` 提供动作语义和组合模板
3. 给 `Level 3: Sim2Real` 提供具身执行接口与任务链条来源

## 2. 资料范围

| Source | Official Link | 本次实际查看范围 | 在 LabOS 中的用途 |
|---|---|---|---|
| AutoBio | [autobio-bench/AutoBio](https://github.com/autobio-bench/AutoBio) | 官方 README、`autobio/` 代码、`model/scene`、`model/instrument`、`model/object`、`assets/`、`instrument.py`、`evaluator.py`、`task.py` | 提供生物实验专用设备、耗材、Sim2Real runtime 接口、连续控制任务 |
| LabUtopia | [Rui-li023/LabUtopia](https://github.com/Rui-li023/LabUtopia) | 官方仓库 `config/`、`controllers/`、`controllers/atomic_actions/`、`tasks/`、`assets/`、`factories/` | 提供原子动作语义、复合 controller、长链组合模板、通用实验室场景 |

## 3. 总结先看

| 维度 | AutoBio | LabUtopia |
|---|---|---|
| 资产风格 | 生物实验专用设备和耗材更强 | 通用实验室场景、容器、家具、装置更强 |
| 动作表示 | 以连续控制 `action chunk` 为主，不直接暴露有限符号动作表 | 明确区分 `atomic actions`、`task controller`、`robot controller` |
| 适合 Level 1 | 很适合，尤其是生物设备与耗材识别 | 适合补通用场景资产与器皿 |
| 适合 Level 2 | 不适合原样当作符号动作空间，但很适合抽象成生物实验宏动作 | 非常适合做符号动作空间与长链组合模板 |
| 适合 Level 3 | 非常适合，已有评测 runtime | 适合提供任务分层思路，但最终 runtime 不应直接照搬 |

---

## 4. AutoBio

### 4.1 仓库定位

| 项目 | 内容 |
|---|---|
| 主要定位 | 数字生物实验室的仿真与 benchmark |
| 资产组织 | `assets/` 为网格和视觉资产，`model/` 为 MuJoCo 可执行 MJCF |
| 评测接口 | `autobio/evaluator.py` + `autobio/evaluate.py` |
| 任务注册 | `autobio/task.py` |
| 关键特点 | 策略输入 observation，输出连续 `action chunk`，不是符号动作序列 |

### 4.2 AutoBio 仪器资产总表

| Canonical Asset | 类别 | Model / MJCF | Mesh / Asset Dir | 设备行为类 | 典型任务 |
|---|---|---|---|---|---|
| `thermal_cycler_biorad_c1000` | 热循环仪 | `model/instrument/thermal_cycler_biorad_c1000.xml` | `assets/instrument/thermal_cycler_biorad_c1000/` | `ThermalCyclerBioradC1000` | `thermal_cycler_close/open` |
| `thermal_mixer_eppendorf_c` | 热混匀仪 | `model/instrument/thermal_mixer_eppendorf_c.xml` | `assets/instrument/thermal_mixer_eppendorf_c/` | `Thermal_mixer_eppendorf_c` | `thermal_mixer` |
| `vortex_mixer_genie_2` | 涡旋振荡器 | `model/instrument/vortex_mixer_genie_2.xml` | `assets/instrument/vortex_mixer_genie_2/` | `VortexMixerGenie2` | `vortex_mixer` |
| `centrifuge_eppendorf_5430` | 离心机 | `model/instrument/centrifuge_eppendorf_5430.xml` | `assets/instrument/centrifuge_eppendorf_5430/` | `Centrifuge_Eppendorf_5430` | `centrifuge_5430_close_lid`、`insert_centrifuge_5430` |
| `centrifuge_eppendorf_5910_ri` | 离心机 | `model/instrument/centrifuge_eppendorf_5910_ri.xml` | `assets/instrument/centrifuge_eppendorf_5910_ri/` | `Centrifuge_Eppendorf_5910` | `centrifuge_5910_lid_close` |
| `centrifuge_tiangen_tgear_mini` | 小型离心机 | `model/instrument/centrifuge_tiangen_tgear_mini.xml` | `assets/instrument/centrifuge_tiangen_tgear_mini/` | `Centrifuge_tiangen_tgear_mini` | `centrifuge_mini_close_lid` |

### 4.3 AutoBio 容器 / 耗材 / 工具资产总表

| Canonical Asset | 主要模型文件 | 类别 | 备注 |
|---|---|---|---|
| `cell_dish_100` | `cell_dish_100.xml`、`cell_dish_100.gen.xml` | 培养皿 | 通用培养皿 |
| `centrifuge_1-5ml` | `centrifuge_1-5ml.xml` | 离心管 | 1.5 mL 管体 |
| `centrifuge_1-5ml_screw` | `centrifuge_1-5ml_screw.xml`、`centrifuge_1-5ml_screw-simple.xml` | 螺旋盖离心管 | 常用于转子装载 |
| `centrifuge_10ml` | `centrifuge_10ml.xml`、`centrifuge_10ml.gen.xml` | 离心管 | 10 mL 管 |
| `centrifuge_10slot` | `centrifuge_10slot.xml`、`centrifuge_10slot.gen.xml` | 管架 | 10 孔离心管架 |
| `centrifuge_1500ul_no_lid` | `centrifuge_1500ul_no_lid.xml`、`centrifuge_1500ul_no_lid.gen.xml` | 容器 | 无盖 1500 µL 管 |
| `centrifuge_15ml` | `centrifuge_15ml.xml` | 离心管 | 15 mL 管 |
| `centrifuge_15ml_screw` | `centrifuge_15ml_screw.xml` | 螺旋盖离心管 | 15 mL 螺旋盖版本 |
| `centrifuge_50ml` | `centrifuge_50ml.xml`、`centrifuge_50ml.gen.xml` | 离心管 | 50 mL 管 |
| `centrifuge_50ml_screw` | `centrifuge_50ml_screw.xml` | 螺旋盖离心管 | `pickup / insert / screw / pipette` 高频出现 |
| `centrifuge_plate_60well` | `centrifuge_plate_60well.xml`、`centrifuge_plate_60well.gen.xml` | 转子/孔板 | 离心机载具 |
| `cryovial_1-8ml` | `cryovial_1-8ml.xml` | 冻存管 | 生物样本容器 |
| `pcr_plate_96well` | `pcr_plate_96well.xml`、`pcr_plate_96well.gen.xml` | PCR 板 | 与热循环仪直接相关 |
| `pipette` | `pipette.xml`、`pipette.gen.xml` | 工具 | 吸液枪本体 |
| `pipette_rack` | `pipette_rack.xml`、`pipette_rack.gen.xml` | 架子 | 吸头架 / 枪架 |
| `pipette_tip` | `pipette_tip.xml`、`pipette_tip.gen.xml` | 耗材 | 吸头 |
| `tip_box` | `tip_box.xml`、`tip_box.gen.xml` | 盒 | 吸头盒 |

### 4.4 AutoBio 机器人与执行器资产

| Asset / Assembly | 位置 | 角色 | 备注 |
|---|---|---|---|
| `ur5e_gripper.xml` | `model/robot/ur5e_gripper.xml` | 单臂 UR5e + 夹爪 | 多个单臂任务使用 |
| `ur5e_dexhand021_right.xml` | `model/robot/ur5e_dexhand021_right.xml` | UR5e + DexHand 右手 | `pipette` 用于精细拇指按压/吸液 |
| `aloha_left.xml` | `model/robot/aloha_left.xml` | Aloha 单臂 | `pickup`、`screw`、部分双臂任务 |
| `dualrm.xml` | `model/robot/dualrm.xml` | 双臂底座 | 双臂装配基础模型 |
| `2f85.xml` | `model/robot/2f85.xml` | Robotiq 2F85 夹爪 | UR5e 夹持端执行器 |
| `assets/robot/aloha2` | `assets/robot/aloha2/` | 网格资产 | Aloha 资产包 |
| `assets/robot/dexhand021` | `assets/robot/dexhand021/` | 网格资产 | 灵巧手资产包 |
| `assets/robot/robotiq` | `assets/robot/robotiq/` | 网格资产 | 夹爪网格 |
| `assets/robot/ur5e` | `assets/robot/ur5e/` | 网格资产 | UR5e 网格 |

### 4.5 AutoBio 任务、场景与资产映射

| Task ID | Scene XML | 语义目标 | 关键资产 | 机器人拓扑 | 公开数据集 |
|---|---|---|---|---|---|
| `thermal_cycler_close` / `thermal_cycler_open` | `model/scene/mani_thermal_cycler.xml` | 关闭/打开热循环仪盖 | `thermal_cycler_biorad_c1000`、`centrifuge_10slot` | 单臂，7 维 action | 是 |
| `pickup` | `model/scene/pickup.xml` | 从管架上取起离心管 | `centrifuge_10slot`、`centrifuge_50ml_screw` | 单臂，7 维 action | 是 |
| `insert` | `model/scene/insert.xml` | 将离心管转移到另一个管架槽位 | 两个 `centrifuge_10slot`、`centrifuge_50ml_screw` | 单臂，7 维 action | 是 |
| `screw_loose` | `model/scene/lab_screw_all.xml` 或相关 `screw` scene | 拧开离心管盖 | `centrifuge_10slot`、`centrifuge_15ml_screw/50ml_screw` | 双臂，14 维 action | 是 |
| `screw_tighten` | `model/scene/lab_screw_tighten.xml` 或相关 `screw` scene | 拧上离心管盖 | `centrifuge_10slot`、`centrifuge_15ml_screw/50ml_screw` | 双臂，14 维 action | 是 |
| `pipette` | `model/scene/mani_pipette.xml` | 一手持管，一手对齐移液并吸液 | `centrifuge_10slot`、`centrifuge_50ml_screw` | 双臂，14 维 action | 是 |
| `thermal_mixer` | `model/scene/mani_thermal_mixer.xml` | 操作热混匀仪面板参数 | `thermal_mixer_eppendorf_c`、`centrifuge_1-5ml_screw`、`centrifuge_plate_60well` | 单臂，7 维 action | 是 |
| `insert_centrifuge_5430` | `model/scene/insert_centrifuge_5430.xml` | 将第二支离心管装载到 5430 转子对称槽位 | `centrifuge_eppendorf_5430`、`centrifuge_1-5ml_screw`、`centrifuge_plate_60well` | 单臂，7 维 action | 是 |
| `centrifuge_5430_close_lid` | `model/scene/mani_centrifuge_5430.xml` | 关闭 5430 离心机盖 | `centrifuge_eppendorf_5430`、`centrifuge_10slot` | 单臂，7 维 action | 否 |
| `centrifuge_5910_lid_close` | `model/scene/mani_centrifuge_5910.xml` | 关闭 5910 离心机盖 | `centrifuge_eppendorf_5910_ri`、`centrifuge_10slot` | 单臂，7 维 action | 否 |
| `centrifuge_mini_close_lid` | `model/scene/mani_centrifuge_mini.xml` | 关闭小型离心机盖 | `centrifuge_tiangen_tgear_mini`、`centrifuge_10slot` | 单臂，7 维 action | 否 |
| `vortex_mixer` | `model/scene/vortex_mixer.xml` | 一手持管，一手操作涡旋振荡器 | `vortex_mixer_genie_2`、`centrifuge_15ml_screw`、`centrifuge_10slot` | 双臂，14 维 action | 否 |

### 4.6 AutoBio runtime observation / action 接口

#### 4.6.1 Observation 接口

| Key | 含义 |
|---|---|
| `observation/state` | 由 `task_info['state_indices']` 指定的关节/状态向量 |
| `observation/image` | 主视角固定相机 |
| `observation/wrist_image` | 第一腕部相机 |
| `observation/wrist_image_2` | 第二腕部相机，双臂任务常见 |
| `prompt` | 任务自然语言前缀 |
| `observation/{history}/...` | 可选历史图像 |

#### 4.6.2 Action 接口

| 属性 | 说明 |
|---|---|
| 输出类型 | `np.ndarray`，形状为 `[#chunk, action_dim]` |
| 写入位置 | `self.data.ctrl[self.task_info['action_indices']] = action` |
| 执行粒度 | 每一行 action 默认推进 10 个 simulator steps |
| 成功判定 | rollout 结束后调用 `task.check()` |
| 动作本质 | 连续低层控制，不是离散符号动作 |

### 4.7 AutoBio 各任务的 observation / action 规格

| Task ID | Prefix / Prompt 摘要 | `state_dim` | `action_dim` | Camera Keys | 动作本质 |
|---|---|---:|---:|---|---|
| `thermal_cycler_close/open` | 打开/关闭热循环仪盖 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `pickup` | 从架子上拿起离心管 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `insert` | 把离心管移到另一管架指定槽位 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `insert_centrifuge_5430` | 将第二支离心管装入对称转子槽位 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `centrifuge_5430_close_lid` | 关闭 5430 离心机盖 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `centrifuge_5910_lid_close` | 关闭 5910 离心机盖 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `centrifuge_mini_close_lid` | 关闭 mini 离心机盖 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `thermal_mixer` | 设定热混匀仪速度、温度、时间 | 7 | 7 | `image`, `wrist_image` | 单臂连续控制 |
| `screw_loose` | 双臂拧开离心管盖 | 14 | 14 | `image`, `wrist_image`, `wrist_image_2` | 双臂连续控制 |
| `screw_tighten` | 双臂拧上离心管盖 | 14 | 14 | `image`, `wrist_image`, `wrist_image_2` | 双臂连续控制 |
| `pipette` | 双臂移液：一手持管，一手对准并吸液 | 14 | 14 | `image`, `wrist_image`, `wrist_image_2` | 双臂连续控制，含灵巧手按压吸液 |
| `vortex_mixer` | 双臂完成振荡器混匀 | 14 | 14 | `image`, `wrist_image`, `wrist_image_2` | 双臂连续控制 |

### 4.8 AutoBio 对 Level 2 的可抽象宏动作

> 注意：下面这些不是 AutoBio 原生暴露的动作 API，而是从其任务语义中可抽出的 benchmark 级宏动作。

| AutoBio 任务/能力 | 可抽象成的 Benchmark Action | 典型参数 |
|---|---|---|
| `pickup` | `pick_tube` | `tube`, `rack`, `slot` |
| `insert` | `transfer_tube` | `tube`, `source_rack`, `target_rack`, `target_slot` |
| `screw_loose` | `unscrew_cap` | `tube`, `cap_type` |
| `screw_tighten` | `screw_cap` | `tube`, `cap_type` |
| `pipette` | `aspirate_liquid` | `source_tube`, `volume_ul`, `pipette_type` |
| `thermal_cycler_open/close` | `open_thermal_cycler_lid` / `close_thermal_cycler_lid` | `instrument` |
| `thermal_mixer` | `set_thermal_mixer` | `instrument`, `rpm`, `temperature_c`, `time_s` |
| `insert_centrifuge_5430` | `load_centrifuge_rotor` | `instrument`, `tube`, `slot` |
| `centrifuge_*_close_lid` | `close_centrifuge_lid` | `instrument` |
| `vortex_mixer` | `vortex_mix` | `tube`, `instrument`, `duration_s` |

---

## 5. LabUtopia

### 5.1 仓库定位

| 项目 | 内容 |
|---|---|
| 主要定位 | 通用实验室场景中的分层 controller benchmark |
| 场景格式 | USD / Isaac Sim |
| 动作层级 | `atomic action -> task controller -> robot controller` |
| 机器人类型 | `franka`、`ridgebase` |
| 核心优势 | 明确给出了原子动作与复合任务的组合关系 |

### 5.2 LabUtopia 场景资产总表

| Scene USD | 主要用途 | 出现 level | 备注 |
|---|---|---|---|
| `assets/chemistry_lab/lab_001/lab_001.usd` | 基础实验台、容器、柜门/抽屉、装置操作 | Level 1 / 2 / 3 / 4 | 最常用基础场景 |
| `assets/chemistry_lab/lab_003/lab_003.usd` | 搅拌、摇晃、加热等桌面操作 | Level 1 / 2 / 3 | 通用化学实验台 |
| `assets/chemistry_lab/lab_003/clock.usd` | `LiquidMixing` 特化场景 | Level 4 | 液体混合长链任务 |
| `assets/chemistry_lab/hard_task/Scene1_hard.usd` | 复杂 hard task | Level 4 | `CleanBeaker` 使用 |
| `assets/navigation_lab/navigation_lab_01/lab.usd` | 移动操作与导航 | Level 5 | 带移动底盘 |

### 5.3 LabUtopia 机器人资产总表

| Robot Type | 资产 | 用途 |
|---|---|---|
| `franka` | `assets/robots/Franka.usd`、`assets/robots/ridgeback_franka.usd` 中的 manipulator 部分 | 桌面操作主机器人 |
| `ridgebase` | `assets/robots/ridgeback_franka.usd` | 移动操作与导航 |
| `fetch` | `assets/fetch/fetch.urdf`、`assets/fetch/fetch.usd` | 仓库中存在，但当前 config 主路径没有作为默认 benchmark 主机器人使用 |

### 5.4 LabUtopia config 级任务矩阵

| Level | Config | `task_type` | `controller_type` | Scene | Robot | 语义 |
|---|---|---|---|---|---|---|
| 1 | `level1_open_door.yaml` | `openclose` | `open` | `lab_001` | `franka` | 开门 |
| 1 | `level1_close_door.yaml` | `openclose` | `close` | `lab_001` | `franka` | 关门 |
| 1 | `level1_open_drawer.yaml` | `openclose` | `open` | `lab_001` | `franka` | 开抽屉 |
| 1 | `level1_close_drawer.yaml` | `openclose` | `close` | `lab_001` | `franka` | 关抽屉 |
| 1 | `level1_pick.yaml` | `pick` | `pick` | `lab_001` | `franka` | 抓取单物体 |
| 1 | `level1_place.yaml` | `place` | `place` | `lab_001` | `franka` | 放置物体 |
| 1 | `level1_pour.yaml` | `pickpour` | `pour` | `lab_001` | `franka` | 倾倒 |
| 1 | `level1_press.yaml` | `press` | `press` | `lab_003` | `franka` | 按钮操作 |
| 1 | `level1_shake.yaml` | `shake` | `shake` | `lab_003` | `franka` | 摇晃 |
| 1 | `level1_stir.yaml` | `stir` | `stir` | `lab_003` | `franka` | 搅拌 |
| 2 | `level2_PourLiquid.yaml` | `pickpour` | `pickpour` | `lab_001` | `franka` | 先抓再倒 |
| 2 | `level2_TransportBeaker.yaml` | `place` | `pickplace` | `lab_001` | `franka` | 搬运烧杯 |
| 2 | `level2_openclose.yaml` | `openclose` | `openclose` | `lab_001` | `franka` | 开后再关 |
| 2 | `level2_HeatLiquid.yaml` | `placepress` | `placepress` | `lab_003` | `franka` | 放置后按键加热 |
| 2 | `level2_ShakeBeaker.yaml` | `shake` | `shakebeaker` | `lab_003` | `franka` | 抓取后摇晃 |
| 2 | `level2_StirGlassrod.yaml` | `stir` | `stirglassrod` | `lab_003` | `franka` | 抓取玻璃棒并搅拌 |
| 3 | `level3_PourLiquid.yaml` | `pickpour` | `pickpour` | `lab_001` | `franka` | 物体和材质更随机的抓取+倾倒 |
| 3 | `level3_TransportBeaker.yaml` | `pickplace` | `pickplace` | `lab_001` | `franka` | 物体和材质更随机的抓取+放置 |
| 3 | `level3_open.yaml` | `openclose` | `open` | `lab_001` | `franka` | 更复杂开门 |
| 3 | `level3_pick.yaml` | `pick` | `pick` | `lab_001` | `franka` | 更复杂抓取 |
| 3 | `level3_press.yaml` | `press` | `press` | `lab_003` | `franka` | 更复杂按键 |
| 3 | `level3_HeatLiquid.yaml` | `placepress` | `placepress` | `lab_003` | `franka` | 更复杂放置+按键 |
| 4 | `level4_DeviceOperation.yaml` | `device_operate` | `device_operate` | `lab_001` | `franka` | 开门、放杯、按按钮 |
| 4 | `level4_CleanBeaker.yaml` | `cleanbeaker` | `cleanbeaker` | `Scene1_hard` | `franka` | 多杯清洗长链 |
| 4 | `level4_CleanBeaker7Policy.yaml` | `cleanbeaker` | `cleanbeaker7policy` | `Scene1_hard` | `franka` | 将清洗链拆成多策略 |
| 4 | `level4_LiquidMixing.yaml` | `LiquidMixing` | `LiquidMixing` | `clock.usd` | `franka` | 多次抓取/倾倒/放置形成混液流程 |
| 4 | `level4_OpenTransportPour.yaml` | `OpenTransportPour` | `OpenTransportPour` | `lab_001` | `franka` | 开门 + 搬运 + 倾倒 |
| 5 | `level5_Navigation.yaml` | `navigation` | `navigation` | `navigation_lab` | `ridgebase` | 移动底盘导航 |
| 5 | `level5_Mobile_manipulation.yaml` | `mobile_pick` | `mobile_pick` | `navigation_lab` | `ridgebase` | 移动抓取 |

### 5.5 LabUtopia 场景中出现的核心对象资产

| 语义类别 | Canonical Asset | 典型 `/World` 路径 | 用途 |
|---|---|---|---|
| 烧杯 / 容器 | `beaker family` | `/World/beaker`、`/World/beaker1`、`/World/beaker2`、`/World/beaker3`、`/World/beaker_hard_1`、`/World/beaker_hard_2`、`/World/target_beaker` | 抓取、倾倒、放置、混合 |
| 锥形瓶 | `conical bottle family` | `/World/conical_bottle02`、`/World/conical_bottle03`、`/World/conical_bottle04` | 抓取、倾倒对象多样化 |
| 量筒 | `graduated_cylinder_03` | `/World/graduated_cylinder_03` | Level 3 倾倒变化体 |
| 玻璃棒 | `glass_rod` | `/World/glass_rod`、`/World/glass_rod/mesh` | 搅拌 |
| 柜体/门/抽屉 | `cabinet family` | `/World/Cabinet_01`、`/World/Cabinet_02`、`/World/Cabinet_01/drawer_handle_top`、`/World/Cabinet_02/drawer_handle_top` | `open/close` |
| 干燥箱 / 设备 | `drying box family` | `/World/DryingBox_01`、`/World/DryingBox_02`、`/World/DryingBox_03` | `device_operate` |
| 按钮类装置 | `button family` | `/World/DryingBox_01/button`、`/World/heat_device/button`、`/World/target_button/button`、`/World/distractor_button_1`、`/World/distractor_button_2` | `press` / `placepress` |
| 加热设备 | `heat_device` | `/World/heat_device`、`/World/heat_device/heat_device/heat_device/plat` | 加热相关任务 |
| 目标平台 | `target plat family` | `/World/target_plat`、`/World/target_plat_1`、`/World/target_plat_2` | 放置和清洗链末端目标 |
| 试管架 | `test_tube_rack` | `/World/test_tube_rack` | 支撑容器放置 |
| 桌面 / 工作面 | `table surface family` | `/World/table/surface`、`/World/table/surface/mesh`、`/World/table_hard/.../surface_1`、`surface_2` | 物体随机化与材质切换 |
| 炉/设备 | `MuffleFurnace / instrument` | `/World/MuffleFurnace`、`/World/instrument` | Level 4 较复杂设备背景 |

### 5.6 LabUtopia 原子动作总表

| Atomic Action | 文件 | 阶段数 | 关键输入 | 输出类型 | 语义备注 |
|---|---|---:|---|---|---|
| `pick` | `controllers/atomic_actions/pick_controller.py` | 6 个显式 phase（外加 start） | `picking_position`, `object_size`, `gripper_position`, `orientation` | `ArticulationAction(joint_positions)` | 靠近、下探、闭爪、抬起 |
| `place` | `controllers/atomic_actions/place_controller.py` | 5 个显式 phase | `place_position`, `gripper_position`, `orientation` | `ArticulationAction(joint_positions)` | 抬高、对位、松爪、撤离 |
| `pour` | `controllers/atomic_actions/pour_controller.py` | 6 个 phase | `target_position`, `source_size`, `current_joint_velocities`, `gripper_position` | `ArticulationAction(joint_positions / joint_velocities)` | 前两步对位，之后切到 joint7 velocity mode 倾倒和回倾 |
| `open` | `controllers/atomic_actions/open_controller.py` | 7 个显式 phase（door/drawer 分支） | `handle_position`, `revolute_joint_position`, `gripper_position` | `ArticulationAction(joint_positions)` | 支持门和抽屉两种开启动作 |
| `close` | `controllers/atomic_actions/close_controller.py` | 门 3 phase / 抽屉 4 phase | `handle_position`, `revolute_joint_position`, `gripper_position` | `ArticulationAction(joint_positions)` | 支持 door / drawer 两种关闭路径 |
| `press` | `controllers/atomic_actions/press_controller.py` | 3 个 phase | `target_position`, `current_joint_positions` | `ArticulationAction(joint_positions)` | 前伸、闭爪、沿 X 轴按压 |
| `pressZ` | `controllers/atomic_actions/pressZ_controller.py` | 3 个 phase | `target_position`, `gripper_position` | `ArticulationAction(joint_positions)` | 主要沿 Z 轴向下按压 |
| `shake` | `controllers/atomic_actions/shake_controller.py` | 9 个显式 phase（总 events 长度 10） | `current_joint_positions`, `orientation` | `ArticulationAction(joint_positions)` | 在固定中心点两侧来回摆动 |
| `stir` | `controllers/atomic_actions/stir_controller.py` | 5 个 phase | `center_position`, `gripper_position`, `orientation` | `ArticulationAction(joint_positions)` | 抬起、移到杯上方、下探、圆周搅拌、抬出 |

### 5.7 LabUtopia 顶层 controller 与动作组合关系

| `controller_type` | Controller 文件 | 原子动作组合 | 语义 |
|---|---|---|---|
| `pick` | `controllers/pick_controller.py` | `pick` | 单动作抓取 |
| `place` | `controllers/place_controller.py` | `pick -> place` | 先拿起再放置 |
| `pour` | `controllers/pour_controller.py` | `pick -> pour` | 先抓起再倾倒 |
| `press` | `controllers/press_controller.py` | `press` | 单动作按压 |
| `open` | `controllers/open_controller.py` | `open` | 开门/开抽屉 |
| `close` | `controllers/close_controller.py` | `close` | 关门/关抽屉 |
| `openclose` | `controllers/openclose_controller.py` | `open -> close` | 开后再关 |
| `shake` | `controllers/shake_controller.py` | `pick -> shake` | 抓取后摇晃 |
| `stir` | `controllers/stir_controller.py` | `pick -> stir` | 抓取后搅拌 |
| `pickpour` | `controllers/pickpour_controller.py` | `pick -> pour` | 典型 Level 2/3 倾倒模板 |
| `pickplace` | `controllers/pickplace_controller.py` | `pick -> place` | 搬运模板 |
| `placepress` | `controllers/placepress_controller.py` | `pick -> place -> pressZ` | 放置后按压 |
| `shakebeaker` | `controllers/shakebeaker_controller.py` | `pick -> shake` | 摇晃烧杯 |
| `stirglassrod` | `controllers/stirglassrod_controller.py` | `pick -> stir` | 玻璃棒搅拌 |
| `device_operate` | `controllers/device_operate_controller.py` | `open -> pick -> place -> close -> press`（代码里还包含双烧杯放置逻辑） | 设备门操作 + 放置 + 按钮 |
| `OpenTransportPour` | `controllers/opentransportpour_controller.py` | `open -> pick -> place -> pick -> pour -> place` | 开门、搬运、再倾倒 |
| `LiquidMixing` | `controllers/LiquidMixing_controller.py` | 多轮 `pick -> pour -> place`，并辅以 `pressZ` | 长链液体混合 |
| `cleanbeaker` | `controllers/cleanbeaker_controller.py` | `pick -> pour -> place -> pick -> shake -> pour -> place` | 七步清洗链 |
| `cleanbeaker7policy` | `controllers/cleanbeaker7policy_controller.py` | 与 `cleanbeaker` 语义相同，但按多策略拆分 | 多策略版本 |
| `navigation` | `controllers/navigation_controller.py` | waypoint navigation | 移动底盘导航，不是手臂原子动作序列 |
| `mobile_pick` | `controllers/mobile_pick_controller.py` | `navigation + pick` 风格 | 移动抓取 |

### 5.8 LabUtopia 动作层级总结

| 层级 | 代码位置 | 输出形式 | 备注 |
|---|---|---|---|
| Atomic Action | `controllers/atomic_actions/*.py` | `ArticulationAction` | 最接近 benchmark 有限动作空间 |
| Task Controller | `controllers/*.py` | 调度 atomic action 或 inference engine | 适合抽取长链模板 |
| Robot Controller | `controllers/robot_controllers/*.py` | `ArticulationAction` / 移动底盘控制 | 更低层执行器接口 |
| Inference Engine | `controllers/inference_engines/*.py` | 模型推理后的轨迹或 action | 推理后端，不适合直接拿来定义 Level 2 动作表 |

### 5.9 LabUtopia 对 Level 2 的候选 Python 函数动作

| LabUtopia 原子/复合语义 | 建议的 Benchmark Action | 典型参数 |
|---|---|---|
| `pick` | `pick_container` | `object_id`, `grasp_site`, `approach_pose` |
| `place` | `place_container` | `object_id`, `target_site` |
| `pour` | `pour_liquid` | `source_container`, `target_container`, `tilt_angle`, `duration_s` |
| `open` | `open_door_or_drawer` | `asset_id`, `handle_id`, `door_type` |
| `close` | `close_door_or_drawer` | `asset_id`, `handle_id`, `door_type` |
| `press` / `pressZ` | `press_button` | `button_id`, `axis`, `press_depth` |
| `shake` | `shake_container` | `object_id`, `amplitude`, `repeat_n` |
| `stir` | `stir_with_rod` | `rod_id`, `container_id`, `radius`, `repeat_n` |
| `pickplace` | `transport_container` | `object_id`, `source_site`, `target_site` |
| `pickpour` | `pick_and_pour` | `source_container`, `target_container` |
| `placepress` | `place_then_activate` | `object_id`, `target_site`, `button_id` |
| `device_operate` | `operate_device_with_loading` | `device_id`, `door`, `objects`, `button_id` |

---

## 6. AutoBio 与 LabUtopia 的交叉映射

### 6.1 资产交叉表

| 统一语义资产 | AutoBio | LabUtopia | 结论 |
|---|---|---|---|
| 管 / 管架 / 样品容器 | 很强：`centrifuge_*`, `cryovial`, `10slot` | 弱，更多是 beaker / bottle / cylinder | 生物样品容器优先复用 AutoBio |
| PCR / 热循环相关设备 | 很强：`thermal_cycler`, `pcr_plate_96well` | 基本没有对应生物专用设备 | 直接用 AutoBio |
| 离心机与转子装载 | 很强：`5430`, `5910`, `mini`, rotor | 基本没有 | 直接用 AutoBio |
| 热混匀仪 / 涡旋仪 | 很强 | 基本没有 | 直接用 AutoBio |
| 烧杯 / 量筒 / 玻璃棒 | 弱 | 很强 | 通用液体操作资产优先用 LabUtopia |
| 柜门 / 抽屉 / 干燥箱 / 加热装置 | 几乎没有 | 很强 | 设备操作类模板优先用 LabUtopia |
| 移动底盘场景 | 没有 | 有 `ridgebase` | Level 5 风格的扩展参考可用 LabUtopia |
| 机器人与 wrist 视角 | Aloha / UR5e / DexHand 更贴近实验台具身操作 | Franka / Ridgebase 更偏通用操作基线 | Level 3 runtime 更应对齐 AutoBio，动作语义模板可借 LabUtopia |

### 6.2 动作交叉表

| 统一动作语义 | AutoBio 是否直接有任务 | LabUtopia 是否有原子/复合 controller | 对 LabOS 的意义 |
|---|---|---|---|
| `pick` | 是 | 是 | 两边都能支持 |
| `place` | 间接，通常作为低层轨迹一部分 | 是 | 符号层优先参考 LabUtopia |
| `pour` | 没有通用倾倒基元 | 是 | 倾倒类动作优先参考 LabUtopia |
| `open` / `close` | 设备盖开关任务有，但不是统一原子 API | 是 | 抽象层优先参考 LabUtopia |
| `press` | 热混匀仪面板本质上含按钮操作 | 是 | 统一成更通用 `press_button` |
| `shake` / `stir` | `vortex_mixer` 提供设备混匀，但不是手持 shake/stir 基元 | 是 | 通用液体操作优先参考 LabUtopia |
| `aspirate` | 是，`pipette` | 没有对应生物专用吸液动作 | 生物移液动作优先参考 AutoBio |
| `screw_loosen` / `screw_tighten` | 是 | 没有 | 螺旋盖动作优先参考 AutoBio |
| `load_centrifuge_rotor` | 是 | 没有 | 生物专用动作优先参考 AutoBio |
| `set_device_panel` | 是，`thermal_mixer` | 部分可近似为 `press` | 生物设备面板操作优先参考 AutoBio |

### 6.3 对 LabOS benchmark 的直接建议

| Benchmark Level | 资产来源 | 动作来源 | 最合适的对齐方式 |
|---|---|---|---|
| `Level 1: Asset Understanding` | AutoBio 为主，LabUtopia 补通用器皿与设备外观 | 不需要动作执行接口，只需资产用途知识 | Nature Protocols 提供用途与使用知识；AutoBio/LabUtopia 提供视觉资产 |
| `Level 2: Long-Horizon Planning` | 两边都用 | LabUtopia atomic actions 为主，AutoBio 宏动作补生物专用动作 | 输出 Python 函数调用序列 |
| `Level 3: Sim2Real` | AutoBio 为主 | AutoBio runtime 为主；LabUtopia 的组合逻辑可用于构造更长链任务 | 最终执行接口对齐 AutoBio `observation -> action chunk` |

---

## 7. 最终结论

| 结论 | 说明 |
|---|---|
| AutoBio 不是合适的 Level 2 原生动作表 | 它暴露的是连续控制接口，不是有限符号动作空间 |
| LabUtopia 非常适合作为 Level 2 的动作语义底座 | 它已经把 `pick/place/pour/open/close/press/shake/stir` 和复合组合写出来了 |
| AutoBio 非常适合作为 Level 3 的执行底座 | 它已有 observation、camera mapping、`action_indices`、`task.check()` 这一整套 runtime |
| 两者在资产层互补 | AutoBio 强生物设备，LabUtopia 强通用实验室场景和器皿 |
| 最合理的整合方式 | `Nature Protocols` 提供步骤与科学约束，`LabUtopia` 提供可组合动作语义，`AutoBio` 提供生物设备和 sim2real 执行接口 |

