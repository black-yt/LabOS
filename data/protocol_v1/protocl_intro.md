# protocol_v1 数据详细介绍

这份文档基于对 `data/protocol_v1/` 目录中的真实文件、真实 JSONL 样本、统计文件以及构建脚本的逐项检查整理而成。目标不是重复 `README.md` 的简版说明，而是把这个目录当前到底长什么样、哪些字段真的可用、哪些文件只是构建痕迹、哪些地方和源码注释并不完全一致，尽量一次讲清楚。

## 1. 先说结论

当前仓库里所谓的 protocol 数据目录，实际对应的是：

- `data/protocol_v1/`

它不是一个“只有 Nature Protocols”的目录，而是一个统一协议语料库发布版本，里面混合了多个来源：

- STAR Protocols
- Bio-protocol
- Current Protocols
- Methods in Molecular Biology
- Nature Protocols
- JoVE
- OpenWetWare

也就是说，`protocol_v1` 是一个统一 schema 下的多源 protocol 语料库快照，不是单一来源的原始抓取结果。

当前发布版本中：

- passing protocol 总数：`5606`
- 主聚合文件：`all.jsonl`
- 按 source 拆分后的 passing 文件：`records/*.jsonl`
- 未通过 hard gate 的样本：`rejected/*.jsonl`
- 抓取 / 解析过程日志：`manifest.jsonl`
- 汇总统计：`stats.json`
- 构建代码快照：`pipeline/`
- 辅助说明文档：`docs/`

## 2. 顶层目录结构

实际目录结构如下：

```text
data/protocol_v1/
├── README.md
├── all.jsonl
├── manifest.jsonl
├── stats.json
├── docs/
│   ├── FEASIBILITY.md
│   └── SESSION_NOTES.md
├── pipeline/
│   ├── __init__.py
│   ├── europepmc.py
│   ├── f1000_run.py
│   ├── openwetware.py
│   ├── pipeline.py
│   ├── reparse.py
│   ├── report.py
│   ├── run.py
│   ├── schema.py
│   ├── storage.py
│   └── parsers/
│       ├── __init__.py
│       ├── base.py
│       ├── bioprot.py
│       ├── curprot.py
│       ├── f1000.py
│       ├── jove.py
│       ├── mimb.py
│       ├── nprot.py
│       └── star.py
├── records/
│   ├── bioprot.jsonl
│   ├── curprot.jsonl
│   ├── jove.jsonl
│   ├── mimb.jsonl
│   ├── nprot.jsonl
│   ├── oww.jsonl
│   └── star.jsonl
└── rejected/
    ├── bioprot.jsonl
    ├── curprot.jsonl
    ├── jove.jsonl
    ├── mimb.jsonl
    ├── nprot.jsonl
    ├── oww.jsonl
    └── star.jsonl
```

这个结构可以分成四层来理解：

1. `all.jsonl` / `records/` / `rejected/`
   - 这是最终数据发布层。
2. `manifest.jsonl` / `stats.json`
   - 这是构建过程和汇总统计层。
3. `pipeline/`
   - 这是构建代码快照层。
4. `docs/`
   - 这是项目过程文档层。

## 3. 每个文件 / 子目录是干什么的

### 3.1 `all.jsonl`

- 整个 corpus 的 passing 样本总表。
- 一行一个 protocol。
- 当前共 `5606` 行。
- 实测它和 `records/*.jsonl` 的关系是：
  - 行数一致
  - `id` 集合一致
  - 顺序也一致

也就是说，当前版本的 `all.jsonl` 可以理解为：

> `records/` 下所有 passing source 文件按固定顺序拼接后的单文件视图。

如果你只是想读“最终可用的 protocol 数据”，优先读这个文件就够了。

### 3.2 `records/`

- 按 source 切开的 passing 样本。
- 当前有 7 个 source 文件：
  - `star.jsonl`
  - `bioprot.jsonl`
  - `curprot.jsonl`
  - `mimb.jsonl`
  - `jove.jsonl`
  - `nprot.jsonl`
  - `oww.jsonl`

它的意义主要有两个：

1. 方便按 source 单独分析。
2. 方便做 source-aware benchmark 构造。

如果你只关心某个来源，例如只看 Nature Protocols，那么就直接看：

- `data/protocol_v1/records/nprot.jsonl`

### 3.3 `rejected/`

- 保存所有未通过 hard gate 的样本。
- 不是垃圾桶，而是审计和后续 parser 改进的重要材料。
- 每个样本都会带 `qc_flags`，标记为什么被拒绝。

这个目录很重要，因为它回答了两个问题：

1. 当前 release 为什么没把某些 source 做大。
2. 后续如果要“救回”更多数据，应该优先改哪类 parser。

例如：

- `jove` 大量失败，主要是 `reagents<3` 和 `no_equipment_or_materials`
- `oww` 大量失败，除了材料和步骤不足外，还有大量 `no_id`

### 3.4 `manifest.jsonl`

- 每次 save 都会 append 一行的抓取 / 解析日志。
- 字段很少，但很关键。
- 当前共 `12103` 行。

真实字段为：

- `id`
- `source`
- `qc_pass`
- `qc_score`
- `qc_flags`
- `doi`
- `pmcid`
- `ts`

要特别注意：

1. `manifest.jsonl` 不是最终发布数据。
2. 它有重复 `id`。
3. 它记录的是“构建历史”，不是“最终可用样本唯一清单”。

实测：

- 总行数：`12103`
- 唯一 `id`：`8624`
- 重复行数：`3479`

因此：

- 不能把 `manifest.jsonl` 当作最终数据集读入。
- 也不能直接拿它的总行数当 protocol 数量。

### 3.5 `stats.json`

- 对 passing 数据做的聚合统计。
- 当前包含：
  - `total`
  - `by_source`
  - `qc_score_histogram`
  - `generated_at`
  - `by_license_bucket`

这份文件非常适合拿来做 corpus 级概览，但不适合做字段级细查，因为它只保留了摘要统计，不保留样本细节。

### 3.6 `pipeline/`

- 这是构建这份语料时使用的代码快照。
- 它不是“当前线上系统”，而是“这次 release 对应的构建快照”。

里面最关键的文件是：

- `schema.py`
  - 定义统一 dataclass 和 `validate()` 规则。
- `pipeline.py`
  - 定义 source 查询、抓取、解析、校验、存储主流程。
- `storage.py`
  - 定义 append-only 的落盘逻辑和 manifest 写入逻辑。
- `report.py`
  - 生成统计报告。
- `parsers/*.py`
  - 每个 source 的解析器实现。
- `openwetware.py`
  - OpenWetWare 的专用抓取与解析逻辑。

### 3.7 `docs/`

- 这是构建过程文档，不是正式 schema 文档。
- 包含：
  - `FEASIBILITY.md`
  - `SESSION_NOTES.md`

这两份文档对理解“为什么选这些 source、哪些 source 没做成、历史上发生过什么问题”很有帮助。

但要注意：

- 它们记录的是阶段性构建过程。
- 某些数字已经和当前 release 不完全一致。

因此，它们适合用来理解背景，不适合直接拿来当最终统计真值。

## 4. 当前数据规模

### 4.1 passing 样本

`records/` 当前各 source 的 passing 数如下：

| source | passing | rejected | 合计尝试数 | 通过率 |
|---|---:|---:|---:|---:|
| `star` | 3941 | 368 | 4309 | 91.5% |
| `bioprot` | 950 | 47 | 997 | 95.3% |
| `curprot` | 191 | 20 | 211 | 90.5% |
| `mimb` | 142 | 81 | 223 | 63.7% |
| `jove` | 112 | 2016 | 2128 | 5.3% |
| `nprot` | 20 | 8 | 28 | 71.4% |
| `oww` | 250 | 452 | 702 | 35.6% |
| **总计** | **5606** | **2992** | **8598** | — |

可以直观看出：

1. `star` 是绝对主力。
2. `bioprot`、`curprot` 通过率很高。
3. `jove` 当前 parser 下通过率极低。
4. `nprot` 当前 release 中量非常小，只有 `20` 条 passing。

这意味着：

- 如果你的 benchmark 计划强依赖 Nature Protocols 大规模样本，这个目录当前并不支持。
- 至少以这个 release 来看，`nprot` 只是一个很小的 OA 子集，而不是几千篇全文协议。

### 4.2 `stats.json` 中的中位数

`stats.json` 给出的 passing 样本按 source 的主要统计如下：

| source | count | median_reagents | median_steps |
|---|---:|---:|---:|
| `star` | 3941 | 28.2 | 73.6 |
| `bioprot` | 950 | 50.9 | 47.8 |
| `curprot` | 191 | 42.8 | 76.9 |
| `mimb` | 142 | 28.9 | 54.0 |
| `jove` | 112 | 8.6 | 44.1 |
| `nprot` | 20 | 29.1 | 65.3 |
| `oww` | 250 | 9.5 | 21.1 |

这个表说明：

- `star` 和 `curprot` 的步骤链都很长。
- `bioprot` 的 reagent 丰富度很高。
- `oww` 和 `jove` 更稀疏。

## 5. 数据文件之间的关系

这个目录最容易误解的地方，就是几个 JSONL 文件其实扮演的是不同角色。

### 5.1 `all.jsonl` 和 `records/`

关系是：

- `all.jsonl = records/*.jsonl` 的聚合版本

实测：

- `same_count = True`
- `same_set = True`
- `same_order = True`

所以：

- 面向训练 / 统计：读 `all.jsonl`
- 面向分 source 研究：读 `records/*.jsonl`

### 5.2 `rejected/` 和 `records/`

它们是同一套 schema 下的两条分流：

- 通过 `validate()` 的去 `records/`
- 未通过的去 `rejected/`

不是两种不同格式，只是 `qc_pass` 不同，`qc_flags` 不同。

### 5.3 `manifest.jsonl` 和前两者

`manifest.jsonl` 不是 `records + rejected` 的简单拼接，因为它记录的是 append-only 历史日志。

当前观察到的几个关键点：

1. `manifest` 有重复 `id`
2. `manifest` 中还出现了 `f1000` 和 `nmeth`
3. 但当前 release 的 `records/` 和 `rejected/` 没有对应这两个 source 文件

这说明：

- `manifest` 记录了更宽的抓取尝试历史
- 当前正式发布的数据子集比 manifest 覆盖的 source 更窄

## 6. 统一 schema：真实字段到底有哪些

虽然 `README.md` 给了一个简版表格，但真实 `all.jsonl` 里字段更完整。根据样本和 `pipeline/schema.py`，当前 passing 样本的顶层字段是：

- `id`
- `source`
- `title`
- `doi`
- `pmcid`
- `pmid`
- `license`
- `journal`
- `pub_year`
- `authors`
- `abstract`
- `domain_tags`
- `reagents`
- `equipment`
- `materials_raw`
- `steps`
- `troubleshooting`
- `timing`
- `safety`
- `references_count`
- `fetched_at`
- `parser_version`
- `qc_pass`
- `qc_score`
- `qc_flags`

也就是说，真实数据比简版 README 多出这些字段：

- `abstract`
- `domain_tags`
- `safety`
- `references_count`
- `fetched_at`

## 7. 嵌套字段结构

### 7.1 `reagents`

类型：

- `list[dict]`

每个元素结构：

| 字段 | 类型 | 含义 |
|---|---|---|
| `name` | str | 试剂名 |
| `vendor` | str | 厂商 |
| `catalog_id` | str | 货号 |
| `rrid` | str | RRID |
| `category` | str | 类别 |

实际例子：

```json
{
  "name": "8–10-week-old C57BL/6J male mice",
  "vendor": "",
  "catalog_id": "",
  "rrid": "",
  "category": ""
}
```

### 7.2 `equipment`

类型：

- `list[dict]`

每个元素结构：

| 字段 | 类型 | 含义 |
|---|---|---|
| `name` | str | 仪器名 |
| `vendor` | str | 厂商 |
| `model` | str | 型号或等价字段 |

实际例子：

```json
{
  "name": "Mouse operant self-administration chambers",
  "vendor": "",
  "model": ""
}
```

### 7.3 `steps`

类型：

- `list[dict]`

每个元素结构：

| 字段 | 类型 | 含义 |
|---|---|---|
| `step_no` | str | 步骤编号，允许 `"1"`、`"1a"`、`"2.3"` 这类形式 |
| `text` | str | 步骤文本 |
| `section` | str | 所属父 section |
| `duration` | str | 时长字段 |

实际例子：

```json
{
  "step_no": "1",
  "text": "Prepare adeno-associated viral vectors: ...",
  "section": "A. Stereotaxic surgery: DREADD approach with viral vector microinjection",
  "duration": ""
}
```

### 7.4 `troubleshooting`

类型：

- `list[dict]`

每个元素结构：

| 字段 | 类型 | 含义 |
|---|---|---|
| `problem` | str | 问题描述 |
| `solution` | str | 解决方案 |

这个字段不是每个 source 都有，而且不同 parser 的填法不完全一致。有些 source 是标准的 `problem/solution` 对，有些只是把 troubleshooting 条目粗抽成 `problem`，`solution` 留空。

## 8. 各字段当前的真实可用性

下面这一节比 schema 本身更重要，因为它回答的是：

> 字段“存在”和字段“好用”不是一回事。

### 8.1 整体非空率

对 `all.jsonl` 的 `5606` 条 passing 样本实测：

| 字段 | 非空率 |
|---|---:|
| `doi` | 95.5% |
| `pmcid` | 95.5% |
| `pmid` | 95.0% |
| `license` | 100.0% |
| `journal` | 100.0% |
| `pub_year` | 95.5% |
| `authors` | 95.5% |
| `abstract` | 95.5% |
| `domain_tags` | 0.0% |
| `reagents` | 100.0% |
| `equipment` | 91.1% |
| `materials_raw` | 87.7% |
| `steps` | 100.0% |
| `troubleshooting` | 75.1% |
| `timing` | 0.3% |
| `safety` | 0.0% |
| `references_count` | 0.0% |
| `fetched_at` | 100.0% |
| `parser_version` | 100.0% |
| `qc_flags` | 4.5% |

### 8.2 可以直接依赖的字段

通常可以直接用的字段：

- `id`
- `source`
- `title`
- `license`
- `journal`
- `reagents`
- `steps`
- `parser_version`
- `qc_pass`
- `qc_score`

这些字段在当前 release 里基本都有值，而且结构稳定。

### 8.3 条件性可用的字段

可用，但要按 source 区分：

- `equipment`
- `materials_raw`
- `troubleshooting`
- `timing`
- `pmid`
- `authors`
- `abstract`

例如：

- `nprot` 的 `timing` 很强，20 条里有 18 条非空
- `star` 的 `troubleshooting` 很强，3941 条里 3889 条非空
- `jove` 的 `equipment` 很弱，112 条里只有 8 条非空
- `mimb` 的 `equipment` 几乎一直为空，但 `materials_raw` 一直存在

### 8.4 当前基本是预留位的字段

下面这些字段在 schema 里有，但当前 release 几乎没真正填起来：

- `domain_tags`
- `safety`
- `references_count`

实测：

- `domain_tags`：`0/5606`
- `safety`：`0/5606`
- `references_count`：`0/5606`

因此，如果后续做 benchmark，不要默认这些字段可用。

## 9. QC gate 和评分机制

`pipeline/schema.py::validate()` 定义了 hard gate。

当前规则是：

1. `len(reagents) >= 3`
2. `len(equipment) >= 1` 或 `len(materials_raw) >= 150`
3. `len(steps) >= 3`
4. `title` 非空

此外还会额外打 `no_id` flag：

- 如果 `doi` 和 `pmcid` 都为空，则加 `no_id`

但需要注意一个很关键的细节：

- `no_id` 不会让样本 fail
- 它只会进入 `qc_flags`

也就是说：

- `qc_flags` 非空，并不一定代表这个样本在 `rejected/`

当前 passing 数据里就有一个典型例子：

- `oww` 的 250 条 passing 全部带 `qc_flags=["no_id"]`

这和顶层 `README.md` 中“passing 行的 `qc_flags` 总是空”并不完全一致。真实数据以 JSONL 为准。

### 9.1 `qc_score` 怎么算

`qc_score` 是一个 0 到 1 的加权 completeness 分数，不是 hard gate 本身。

源码中的大致权重是：

- reagent 数量：0.3
- equipment 数量：0.2
- step 数量：0.3
- troubleshooting 存在：0.1
- timing 存在：0.05
- abstract 存在：0.05

因此：

- `qc_score` 高，不一定说明语义质量高
- 它主要反映“结构完整度”

## 10. 各 source 的结构特点

这部分不是凭 README 猜的，而是根据 `pipeline/parsers/*.py` 的真实实现整理的。

### 10.1 `star`

来源特点：

- 结构化程度最高。
- 关键资源表 `Key resources table` 可直接抽 reagent / equipment。
- 步骤来自 `Step-by-step method details`。

parser 逻辑：

- `Key resources table` 解析成 `reagents` 和 `equipment`
- `Materials and equipment` 抽成 `materials_raw`
- `Troubleshooting` 可抽成结构化问题-方案
- `Timing` 可抽，但当前 release 中实际几乎都为空

特点总结：

- 当前 release 的主力来源
- 结构稳定
- 适合做长步骤 protocol benchmark

### 10.2 `bioprot`

来源特点：

- 更偏 prose 风格
- `Materials and reagents`、`Equipment`、`Procedure` 都是文章正文中的结构块

parser 逻辑：

- 通过 numbered `<p>` 和 `<list-item>` 抽条目
- 还会从全文里 fallback 挖 `Reagent (Vendor, Cat#)` 模式

特点总结：

- reagent 很丰富
- step 也比较完整
- 结构不如 STAR 规则，但仍然相对稳定

### 10.3 `nprot`

来源特点：

- 对应 Nature Protocols 的 OA 子集
- 章节结构更接近：
  - `Reagents`
  - `Equipment`
  - `Reagent setup`
  - `Equipment setup`
  - `Procedure`
  - `Timing`
  - `Troubleshooting`

parser 逻辑：

- `reagents` 和 `equipment` 从对应 section 抽
- `materials_raw` 会拼接 `Reagents + Equipment + Reagent setup + Equipment setup`
- `timing` 来自 `Timing`

特点总结：

- 当前 release 里样本量非常小，只有 `20` 条 passing
- 但每条记录通常比较完整
- `timing` 是当前所有 source 里最可用的一个

### 10.4 `curprot`

来源特点：

- Current Protocols 在 PMC XML 里 section 组织比较特殊
- 步骤列表经常出现在 `specific-use="protocol-steps"` 的 list 里

parser 逻辑：

- `Materials` 可能有多个 sibling section
- `REAGENTS AND SOLUTIONS` 会额外并入 `materials_raw`
- 步骤通过遍历带数字 label 的 list-item 抽取

特点总结：

- 步骤链很长
- `materials_raw` 很强
- `equipment` 有，但不是每条都强

### 10.5 `mimb`

来源特点：

- Methods in Molecular Biology 更接近 prose-based chapter 风格
- 常见 section 是 `Materials` 和 `Methods`

parser 逻辑：

- `reagents` 从 Materials 段落抽
- `equipment` 基本不单独建模
- `steps` 从 `Methods` / `Procedure` 中的 numbered items 或段落抽取

特点总结：

- `equipment` 基本不可依赖
- 但 `materials_raw` 很稳定
- `steps` 和 `troubleshooting/notes` 仍有一定价值

### 10.6 `jove`

来源特点：

- 目标结构本来应该包括：
  - `Protocol`
  - `Table of Materials`

但很多 PMC XML 并不把 JoVE 的材料表完整保留下来。

parser 逻辑：

- 优先找 `Table of Materials`
- 如果找不到，就从全文挖 inline `Reagent (Vendor, Cat#)` 模式
- `Protocol` section 用来抽步骤

特点总结：

- 当前 parser 下通过率极低
- 主要瓶颈不是步骤，而是材料表缺失

### 10.7 `oww`

来源特点：

- OpenWetWare 不是期刊，而是 MediaWiki 社区页面
- 页面质量很异质

parser 逻辑：

- 专门走 `openwetware.py`
- 通过 MediaWiki API 拉 HTML
- 再按 `Materials/Reagents/Equipment/Procedure/Steps` 类标题做启发式切分

特点总结：

- source 异质性最大
- bibliographic metadata 最弱
- 但可以作为补充性 protocol 来源

## 11. `rejected/` 里最常见的失败原因

按 source 看，最常见的拒绝原因如下：

| source | 最常见失败原因 |
|---|---|
| `bioprot` | `reagents<3` |
| `curprot` | `steps<3` |
| `jove` | `reagents<3`、`no_equipment_or_materials` |
| `mimb` | `steps<3`、`reagents<3` |
| `nprot` | `reagents<3`、`steps<3` |
| `oww` | `no_id`、`no_equipment_or_materials`、`reagents<3` |
| `star` | `reagents<3` |

更具体地说：

- `jove` 的 2016 条 rejected 中，`2006` 条都有 `reagents<3`
- `oww` 的 452 条 rejected 全都有 `no_id`
- `star` 虽然整体通过率很高，但 rejected 的主因仍然是 `reagents<3`

因此，如果未来要“扩数据量”，优先级大致是：

1. 补 `jove` 的材料表解析
2. 处理 `oww` 的 id 问题
3. 对 `mimb` 和 `curprot` 做更强的 step 抽取

## 12. 当前 release 和 pipeline 快照之间的差异

这一节非常关键，因为如果只看源码，很容易误以为当前目录结构和 pipeline 运行目录是一模一样的。

### 12.1 `parsed/` vs `records/`

`pipeline/storage.py` 里写入目录名是：

- `parsed/`
- `rejected/`

但当前发布版本实际目录名是：

- `records/`
- `rejected/`

说明：

- 这是一次发布时的目录重命名 / 整理
- 不能机械地按 `storage.py` 里的路径去理解当前目录

### 12.2 `docs/SESSION_NOTES.md` 的统计与当前 release 不完全一致

`SESSION_NOTES.md` 里有一版更早的统计，例如：

- STAR `3928`
- Bio-protocol `931`
- 总 passing `4879`

但当前 release 实际是：

- STAR `3941`
- Bio-protocol `950`
- 总 passing `5606`

所以：

- `SESSION_NOTES.md` 更像构建过程中的阶段记录
- 当前发布目录的真值应以 `records/*.jsonl`、`all.jsonl`、`stats.json` 为准

### 12.3 `manifest.jsonl` 比正式发布数据更宽

当前 manifest 中有：

- `f1000`
- `nmeth`

但正式发布的数据文件中没有这两个 source。

说明：

- manifest 记录了更宽的抓取尝试
- 当前 release 没有把这些 source 纳入最终 records/rejected 切片

## 13. 真实数据中的一些实现细节

### 13.1 `materials_raw` 有长度裁剪

源码里不同 parser 对 `materials_raw` 的截断上限并不完全相同：

- 有些 source 截到 `5000`
- 有些 source 截到 `8000`

实测当前 passing 数据里：

- `materials_raw` 最大长度正好是 `8000`

因此：

- `materials_raw` 不应被视为“完整原文段落”
- 它更像一个用于 gate 和 fallback 的结构化补充字段

### 13.2 某些 parser 会人为合成 `materials_raw`

如果 `materials_raw` 太短，但已经抽到了足够多的 reagent，部分 parser 会把 reagent 列表拼成一段字符串，塞回 `materials_raw`，以满足 gate。

这意味着：

- `materials_raw` 不一定总是原文摘录
- 有时它是 parser 生成的 fallback 文本

### 13.3 `timing` 只在极少数 source 真正有值

实测：

- 全 corpus 里 `timing` 只有 `18/5606`
- 主要集中在 `nprot`

如果后续 benchmark 很依赖 step-level timing，不要默认这个字段可以直接拿来用。

## 14. 对 benchmark 构造最有用的读取方式

### 14.1 如果你要做统一 protocol QA / planning

直接读：

- `data/protocol_v1/all.jsonl`

理由：

- 已经是 passing 样本全集
- schema 统一
- 无需自己拼接 source 文件

### 14.2 如果你要单独研究 Nature Protocols

直接读：

- `data/protocol_v1/records/nprot.jsonl`
- `data/protocol_v1/rejected/nprot.jsonl`

理由：

- 前者是当前 release 中真正可用的 OA 子集
- 后者可以帮助你理解为什么只有 20 条 pass

### 14.3 如果你要做 parser 改进

重点看：

- `rejected/*.jsonl`
- `pipeline/parsers/*.py`
- `manifest.jsonl`

理由：

- `rejected` 告诉你失败模式
- `parsers` 告诉你当前启发式
- `manifest` 告诉你历史运行范围

### 14.4 如果你要做高质量 wet-lab benchmark

优先 source：

1. `star`
2. `bioprot`
3. `curprot`
4. `nprot`（量少但质量高）

谨慎使用：

1. `jove`
2. `oww`
3. `mimb`

不是说后者没有价值，而是它们当前 release 里的结构稳定性明显不如前者。

## 15. 最后给一个务实判断

从真实数据来看，`protocol_v1` 更适合被理解成：

> 一个以 STAR 为主体、融合多个 OA 协议来源、经过统一 hard gate 清洗后的实验 protocol 语料库快照。

它当前最强的能力是：

- 提供统一 schema
- 提供长步骤实验 protocol
- 提供 reagent / equipment / steps 三级结构
- 提供 rejected 样本用于 parser 改进

它当前最明显的限制是：

- Nature Protocols 量很小，远不是大规模全量集
- `domain_tags` / `safety` / `references_count` 这些字段基本还没真正做起来
- `materials_raw` 有截断和 fallback 合成，不能直接当原文替代
- `manifest.jsonl` 是构建日志，不是最终可直接训练的样本表

如果后续要围绕它继续做 benchmark，最稳妥的做法是：

1. 把 `all.jsonl` 作为统一入口
2. 把 `records/nprot.jsonl` 单独看作 Nature Protocols OA 子集
3. 在正式建 benchmark 前，先按 source 做一次字段可用性审计
4. 对任何强依赖 `timing`、`safety`、`domain_tags` 的设计，先假设这些字段当前不可用
