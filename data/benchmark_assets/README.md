# Benchmark Assets 说明

这个目录只做三件事：

1. 记录 `AutoBio` 和 `LabUtopia` 的场景/资产分类
2. 维护当前 benchmark 真正使用的核心资产清单
3. 保存 `protocol_min_v1` 和资产清单的匹配结果

## 1. 先看哪个文件

- `upstream_repo_inventory.md`
  - 上游视角的结构清单：解释 `AutoBio` 和 `LabUtopia` 里有哪些 `scene / asset / composite asset / scene object reference`
- `previews/`
  - 脚本生成的 scene / asset 预览图
- `benchmark_asset_catalog.md`
  - benchmark 视角的核心资产主表：只保留当前真正要用的 29 条条目
- `benchmark_asset_catalog.json`
  - 上面那份主表的机器可读版本，后续程序处理优先读它
- `protocol_min_v1_with_assets.jsonl`
  - 匹配到资产后的 protocol 全量记录
- `protocol_min_v1_asset_matches.jsonl`
  - 精简匹配摘要
- `protocol_min_v1_asset_matches.stats.json`
  - 匹配统计

## 2. 统一术语

这 4 个概念最容易混。可以先用一句话记：

- `scene` = 一个完整实验环境
- `asset (standalone_mesh_root)` = 一个独立对象的 mesh 根入口
- `composite asset (package_entrypoint)` = 一个独立对象，但它是“多部件打包”的对象入口
- `scene object reference (scene_prim_reference)` = 场景里面某个对象路径，不是独立文件

### 2.1 四类概念的中文解释

| 术语 | 中文解释 | 它不是什么 | 典型形式 | 真实例子 |
|---|---|---|---|---|
| `scene` | 一个完整环境入口。加载它时，出来的是一整张实验台/一个实验室，而不是单个对象。里面通常有桌子、多个仪器、容器、机器人、相机和初始布局。 | 不是单个对象文件 | `model/scene/*.xml`、`*.usd` | `autobio/model/scene/lab.xml`、`assets/chemistry_lab/lab_001/lab_001.usd` |
| `asset (standalone_mesh_root)` | 一个独立对象的 mesh 根入口。它通常直接对应一个对象的几何外形，可以单独渲染。 | 不是完整环境；也不是场景内对象路径 | `assets/.../*.obj` | `autobio/assets/container/pcr_plate_96well_vis.obj` |
| `composite asset (package_entrypoint)` | 一个独立对象，但不是一份裸 mesh，而是一个“对象入口文件”。这个入口会再引用多个 mesh、碰撞体、关节、材质或子部件，组合成完整对象。 | 不是完整环境；也不是 scene 内部路径 | `model/object/*.xml`、`model/instrument/*.xml` | `autobio/model/instrument/centrifuge_eppendorf_5430.xml` |
| `scene object reference (scene_prim_reference)` | 场景里的某个对象引用。它本身不是一个独立文件，而是“某个 scene 里面的某个对象地址”。离开那个 scene，它就不能单独成立。 | 不是独立 asset 文件 | `scene.usd#/World/...` | `assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02` |
| `support files` | 给 scene 或 asset 配套的文件，比如材质、贴图、SubUSD、碰撞网格。 | 不是 scene，也不是主对象入口 | `SubUSDs/`, `materials/`, `textures/` | `assets/chemistry_lab/lab_003/SubUSDs/materials/*.mdl` |

### 2.2 怎么判断一个路径属于哪一类

按下面顺序判断最稳：

1. 如果这个路径一加载就是完整实验环境，属于 `scene`
2. 如果这个路径长得像 `xxx.usd#/World/...`，属于 `scene object reference`
3. 如果它代表的是单个对象，而且直接就是 mesh 根文件，属于 `asset`
4. 如果它代表的是单个对象，但入口文件还会继续引用很多部件，属于 `composite asset`
5. 如果它只是材质、贴图、SubUSD、碰撞网格，属于 `support files`

### 2.3 一个最容易懂的对比例子

以 LabUtopia 的烧瓶为例：

- `assets/chemistry_lab/lab_001/lab_001.usd`
  - 这是 `scene`
  - 因为它是整个实验环境
- `assets/chemistry_lab/lab_001/lab_001.usd#/World/conical_bottle02`
  - 这是 `scene object reference`
  - 因为它只是这个场景里的一个对象

以 AutoBio 的离心机为例：

- `autobio/model/scene/mani_centrifuge_5430.xml`
  - 这是 `scene`
  - 因为它是一个任务环境入口
- `autobio/model/instrument/centrifuge_eppendorf_5430.xml`
  - 这是 `composite asset`
  - 因为它描述的是“一个离心机对象”，但这个对象由多份 mesh 和部件组成

以 AutoBio 的 PCR 板为例：

- `autobio/assets/container/pcr_plate_96well_vis.obj`
  - 这是 `asset`
  - 因为它就是一个对象的独立 mesh 根入口

## 3. 当前 benchmark 核心条目

- `AutoBio`
  - 21 条
  - `14 x asset (standalone_mesh_root)`
  - `7 x composite asset (package_entrypoint)`
- `LabUtopia`
  - 8 条
  - `8 x scene object reference (scene_prim_reference)`
  - 来自 3 个 chemistry scene：
    - `assets/chemistry_lab/lab_001/lab_001.usd`
    - `assets/chemistry_lab/lab_003/lab_003.usd`
    - `assets/chemistry_lab/hard_task/Scene1_hard.usd`

这 29 条是 benchmark 主清单，不是两个仓库的全量资产数。

## 4. 按仓库快速判断

- `AutoBio`
  - `model/scene/*.xml` = `scene`
  - `model/object/*.xml`、`model/instrument/*.xml` = `composite asset`
  - `assets/container|rack|tool/...` 的 raw mesh = `asset`
- `LabUtopia`
  - `config/*.yaml` 里的 `usd_path` = `scene`
  - `scene.usd#/World/...` = `scene object reference`
  - `SubUSDs/materials/textures` = `support files`

这里的重点只是把“路径长什么样”快速映射到分类，不重复定义。

## 5. 当前简短结论

- `AutoBio` 是 `asset-first + scene xml`
- `LabUtopia` 是 `scene-first + scene object`
- 不应该把 `LabUtopia` 当前那 8 条 benchmark 条目写成“LabUtopia 全部 assets”
- 如果后面要做统一可渲染资产库：
  - `AutoBio` 多数可以直接走对象级资产路线
  - `LabUtopia` 需要先把 `scene object` 从场景里拆出来或转换
