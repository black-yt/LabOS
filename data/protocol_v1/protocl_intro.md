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

## 15. 面向 Benchmark 的最小结构建议

前面几节主要是在解释：

- 当前 `protocol_v1` 目录里真实有什么
- 各字段实际覆盖率如何
- 哪些字段只是 parser / 构建痕迹

但如果后续目标是：

- 从 `all.jsonl` 继续清洗
- 构造 Level 1 / Level 2 / Level 3 benchmark
- 把 protocol 作为一个长期稳定的“中间层底座”

那么直接沿用原始 schema 其实并不合适，因为原始 schema 同时混合了：

1. 真实监督信息
2. 论文元信息
3. parser fallback 字段
4. 构建过程字段
5. QC 辅助字段

从 benchmark 的角度看，更合理的做法是先定义一层更小、更干净、语义更稳定的 protocol 中间表示。下面这一节给出建议的最小结构。

### 15.1 建议的最小结构

建议把 benchmark 用的 protocol 底座收成如下结构：

```json
{
  "id": "...",
  "title": "...",
  "background": "...",
  "materials": {
    "reagents": [
      {
        "name": "...",
        "vendor": "...",
        "identifier": "..."
      }
    ],
    "equipment": [
      {
        "name": "...",
        "vendor": "...",
        "identifier": "..."
      }
    ]
  },
  "procedure": {
    "steps": [
      {
        "idx": 1,
        "stage": "...",
        "description": "..."
      }
    ],
    "troubleshooting": [
      {
        "problem": "...",
        "solution": "..."
      }
    ]
  }
}
```

这个结构的设计目标是：

1. 只保留 benchmark 构造真正会用到的有效信息
2. 去掉论文元信息和 parser 痕迹
3. 保持和原始 `all.jsonl` 的回溯关系
4. 让后续 planning / asset mapping / question generation 都能在同一结构上工作

### 15.2 为什么顶层只保留这几个字段

#### `id`

必须保留。

作用：

- 唯一主键
- 回源到原始 `all.jsonl`
- 去重
- 和后续派生样本表建立连接

这里不再单独保留：

- `source`
- `doi`
- `pmcid`
- `pmid`

原因是：

- `source` 已经编码在 `id` 前缀里，例如 `star:...`、`nprot:...`
- 真要回到原始样本，只需要 `id`
- 对 benchmark 本体来说，多留一批 trace 字段并没有实际收益

#### `title`

必须保留。

作用：

- 表示整个 protocol 的主题
- 适合做检索、聚类、去重
- 后续构造任务背景时是最短、最稳定的摘要

#### `background`

必须保留。

这个字段不是原始 schema 直接给出的字段名，而是一个归一化后的字段。

建议构造规则：

1. 优先用原始 `abstract`
2. 如果 `abstract` 为空，则退化成 `title`

这样做的原因是：

- benchmark 构造时需要的是一个可直接给模型的背景描述
- 不希望下游每次都自己判断 `abstract` 是否为空

### 15.3 `materials` 为什么分成 `reagents` 和 `equipment`

两者不能合并。

虽然它们都属于“实验对象”，但在 benchmark 里的作用明显不同：

- `reagents`
  - 更偏试剂、样本、缓冲液、抗体、酶、培养基、试剂盒
  - 主要影响实验语义、配方、参数、约束
- `equipment`
  - 更偏仪器、设备、工具、耐用品
  - 直接关系到 Level 1 的 asset understanding 和 Level 3 的具身对象对齐

所以更优雅的结构不是把两者混成一个 `materials_items`，而是保留：

- `materials.reagents`
- `materials.equipment`

这样后续做：

- asset canonicalization
- action space 映射
- 问题构造

都会更清楚。

### 15.4 `reagents` 和 `equipment` 的 item 为什么统一成 `{name, vendor, identifier}`

原始数据里这两个字段的子结构并不相同。

原始 `reagents` item：

```json
{
  "name": "...",
  "vendor": "...",
  "catalog_id": "...",
  "rrid": "...",
  "category": "..."
}
```

原始 `equipment` item：

```json
{
  "name": "...",
  "vendor": "...",
  "model": "..."
}
```

在 benchmark 用的最小结构里，建议统一写成：

```json
{
  "name": "...",
  "vendor": "...",
  "identifier": "..."
}
```

原因如下。

#### 第一，`name` 是核心语义字段，必须留

无论是 reagent 还是 equipment，真正稳定、最重要的字段都是：

- `name`

这个字段后续会直接参与：

- 实体归一化
- 题目构造
- step 对齐
- asset / action 映射

#### 第二，`vendor` 保留成本低，但价值很高

真实数据里：

- `reagent.vendor` 非空率约 `80.1%`
- `equipment.vendor` 非空率约 `90.0%`

它不是绝对刚需，但很值得保留，因为它对：

- 去重
- 更细粒度对齐
- 同名不同品牌区分

都很有帮助。

#### 第三，把 `catalog_id` 和 `model` 统一为 `identifier` 更优雅

原始数据里：

- reagent 的规格字段叫 `catalog_id`
- equipment 的规格字段叫 `model`

但从 benchmark 角度看，这两个字段在更高层都在回答同一个问题：

> 这个对象更具体是哪一个版本 / 规格 / 产品实例？

因此，把它们统一成：

- `identifier`

会让结构更整洁，也更利于下游代码统一处理。

也就是说：

- `reagent.identifier` 通常来自原始 `catalog_id`
- `equipment.identifier` 通常来自原始 `model`

#### 第四，为什么 `rrid` 和 `category` 不进最小版

原始 `reagents` 里还有：

- `rrid`
- `category`

但当前 release 中：

- `rrid` 覆盖率很低，只在少量 STAR 样本里有
- `category` 的可用性也强烈依赖 source，跨源稳定性一般

因此，它们可以在以后做 richer schema 时再加回去，但不适合进入最小版。

### 15.5 `steps` 为什么建议写成 `{idx, stage, description}`

这是整个最小结构里最重要的一层。

原始 `steps` 子结构是：

```json
{
  "step_no": "...",
  "text": "...",
  "section": "...",
  "duration": "..."
}
```

建议映射成：

```json
{
  "idx": 1,
  "stage": "...",
  "description": "..."
}
```

#### `idx`

`idx` 是重新编号后的整数顺序。

保留它是为了：

- 明确 step 序
- 避免受原始 `step_no` 形式波动影响
- 方便后续直接做顺序级处理

原始 `step_no` 可以不进入最小版，因为：

- 有些 source 用 `1a`、`2.3`
- 有些 source 基本没有稳定编号
- 对 benchmark 主体来说，顺序比原始编号样式更重要

如果后续确实要保留原始编号，可以在 richer schema 中再加：

- `orig_step_no`

但不属于最小必要字段。

#### `description`

原始 `text` 建议改名为：

- `description`

原因是：

- `text` 太像 parser 原始字段
- `description` 更贴近“这一步在做什么”的语义
- 更适合作为 benchmark 输入输出中的自然语言描述字段

#### `stage`

原始 `section` 建议改名为：

- `stage`

这是本次讨论中最关键的命名决策之一。

### 15.6 为什么 `section` 不是 `action`

这里必须明确：

- 原始数据里的 `section`
- 不是具身原子动作
- 也不是 Level 2 最终 action space 里的 python function

它更像：

- protocol 中的高层阶段
- subtask
- 多个细步骤的语义标题

来自真实数据的例子包括：

- `Preparation of the plate coating and cell plating`
- `A. Stereotaxic surgery: DREADD approach with viral vector microinjection`
- `AMPure XP Cleanup. Timing: 1 h`
- `Design and expression of protein constructs`
- `Plate Vero-E6 cells for infection`

这些标题显然都不是：

- `grasp_tube`
- `move_to_slot`
- `close_lid`

这类具身原子 action。

它们描述的是：

- 一个任务块
- 一个实验阶段
- 一串动作的高层组合语义

因此，如果直接把 `section` 改名成 `action`，会造成两个问题：

1. 混淆 protocol 高层阶段和具身原子动作
2. 让 Level 2 / Level 3 的动作空间语义变得不清楚

更合适的理解层级应该是：

1. `title/background`
   - 整个 protocol / 整个任务
2. `stage`
   - protocol 内部的高层阶段
3. `description`
   - 每个具体步骤的自然语言描述
4. `action`
   - AutoBio / LabUtopia 中真正可执行、可评分的有限动作空间

所以，`section` 改成 `stage` 比改成 `action` 更准确，也更优雅。

### 15.7 为什么 `troubleshooting` 要保留

原始 schema 里有：

- `troubleshooting`

它不能删掉，原因主要有两个。

#### 第一，Level 1 会用到

`troubleshooting` 很适合构造：

- 仪器使用错误题
- 常见失败原因题
- 安全 / 注意事项题
- 纠错题

#### 第二，Level 2 也可能用到

它可以作为：

- 约束条件
- negative rule
- 失败恢复提示

所以 `troubleshooting` 虽然不是每条记录都很强，但在最小版里仍然值得保留。

保留形式建议和原始结构一致：

```json
{
  "problem": "...",
  "solution": "..."
}
```

不要压成字符串列表，因为：

- `problem` 和 `solution` 在下游题目构造里角色不同

### 15.8 新 key 和老 key 的对应关系

下面给出建议的最小结构与原始 `all.jsonl` key 的对应关系。

| 最小结构 key | 原始 key | 处理方式 |
|---|---|---|
| `id` | `id` | 原样保留 |
| `title` | `title` | 原样保留 |
| `background` | `abstract` / `title` | 优先 `abstract`，空则退化成 `title` |
| `materials.reagents[].name` | `reagents[].name` | 原样保留 |
| `materials.reagents[].vendor` | `reagents[].vendor` | 原样保留 |
| `materials.reagents[].identifier` | `reagents[].catalog_id` | 重命名并统一 |
| `materials.equipment[].name` | `equipment[].name` | 原样保留 |
| `materials.equipment[].vendor` | `equipment[].vendor` | 原样保留 |
| `materials.equipment[].identifier` | `equipment[].model` | 重命名并统一 |
| `procedure.steps[].idx` | 派生字段 | 由 step 顺序重新编号 |
| `procedure.steps[].stage` | `steps[].section` | 重命名 |
| `procedure.steps[].description` | `steps[].text` | 重命名 |
| `procedure.troubleshooting[].problem` | `troubleshooting[].problem` | 原样保留 |
| `procedure.troubleshooting[].solution` | `troubleshooting[].solution` | 原样保留 |

### 15.9 哪些原始字段明确不进入最小版

建议从最小版中移除以下字段：

- `source`
- `doi`
- `pmcid`
- `pmid`
- `license`
- `journal`
- `pub_year`
- `authors`
- `domain_tags`
- `materials_raw`
- `timing`
- `safety`
- `references_count`
- `fetched_at`
- `parser_version`
- `qc_pass`
- `qc_score`
- `qc_flags`
- `steps[].step_no`
- `steps[].duration`
- `reagents[].rrid`
- `reagents[].category`

这些字段并不是完全无价值，而是：

- 对 benchmark 本体不是最小必要条件
- 或者当前覆盖率不足
- 或者属于构建 / 审计 / parser 过程信息

其中：

- `qc_pass`、`qc_score`、`qc_flags`
  - 只适合保留在预处理阶段
  - 不应进入最终 benchmark 用的最小协议底座

### 15.10 为什么这个结构既最小又优雅

这个结构之所以适合做 benchmark 中间层，是因为它把 protocol 信息压到了三个稳定层级：

1. 顶层语义：
   - `id`
   - `title`
   - `background`
2. 实体层：
   - `materials.reagents`
   - `materials.equipment`
3. 流程层：
   - `procedure.steps`
   - `procedure.troubleshooting`

它的优点是：

- 比原始 `all.jsonl` 干净很多
- 比完全平铺更有结构感
- 不会和后续的具身动作空间发生语义冲突
- 既适合做 Level 1 题目构造，也适合做 Level 2 / Level 3 的 planning 和对齐

如果后续需要 richer schema，可以在这个最小结构之上再扩：

- `orig_step_no`
- `identifier_type`
- `stage_fn`
- `canonical_name`
- `source`

但这些都不属于第一版最小必要字段。

### 15.11 当前唯一版本的筛选规则

当前仓库不再并行维护“宽松最小版”和“严格 benchmark 版”两套 protocol 中间文件，而是只维护一套：

- `protocol_min_v1`

但这里的 `min` 指的是：

- schema 足够小
- 字段语义足够稳定

不代表筛选条件会放得很松。

相反，这一版的默认过滤规则已经直接按 benchmark 需求收紧，目标是让保留下来的 protocol 更适合：

- Level 1 的资产理解题构造
- Level 2 的长程 planning 监督
- Level 3 的 sim2real 长链任务对齐

默认要求如下：

1. `id` 非空
2. `title` 非空
3. `background` 非空
4. `materials.reagents` 数量 `>= 5`
5. `materials.equipment` 数量 `>= 2`
6. `procedure.steps` 数量 `>= 20`
7. `procedure.steps.stage` 的唯一值数量 `>= 3`

这些条件分别对应不同目标。

#### 为什么 `steps >= 20`

这批 protocol 原始数据本身就很长。

从 `all.jsonl` 的实际分布看：

- `steps` 的 `p10` 已经是 `20`
- 中位数约 `56`

这意味着：

- `steps >= 3` 这种阈值几乎没有任何筛选力
- 如果想让数据真正适合 long-horizon benchmark，就至少应保留一个明显长链的下限

因此，`20` 是一个更合理的第一版门槛。

#### 为什么还要加 `unique_stages >= 3`

只看 step 数仍然不够。

有些 protocol 虽然 step 多，但本质上只是：

- 单一阶段下的细碎展开
- 或者 parser 把一段说明拆成很多连续句子

如果用于 benchmark，这类样本会带来两个问题：

1. 长度够了，但缺少真正的阶段结构
2. 不利于后续把 protocol 高层阶段映射到动作链和资产链

所以这里额外要求：

- 唯一 `stage` 数量至少为 `3`

这能保证保留下来的 protocol 不只是“长”，而且更像一个有阶段组织的完整实验流程。

#### 为什么把 `reagents` 和 `equipment` 的门槛也提高

把门槛设置为：

- `reagents >= 5`
- `equipment >= 2`

主要不是为了材料越多越好看，而是为了后续 benchmark 构造时有足够上下文。

对 `reagents` 来说：

- 太少时，很难稳定恢复实验配方、条件约束和关键输入物

对 `equipment` 来说：

- 只有 `1` 个仪器通常不足以支撑 asset understanding 和 sim2real 对齐
- 至少有 `2` 个设备，更容易形成真实的实验工作流环境

#### 为什么暂时不把 `troubleshooting` 当成硬门槛

`troubleshooting` 很有价值，但它更适合：

- 作为 Level 1 的题目来源
- 作为额外约束或错误恢复信息

而不是作为全局过滤开关。

原因是：

- 没有 troubleshooting 不代表 protocol 不适合 long-horizon planning
- 如果把它设成硬门槛，会无谓减少可用样本

所以当前做法是：

- 保留 `troubleshooting`
- 但不要求每条记录都必须有

#### 为什么暂时不按 step 文本长度硬筛

另一个可选维度是每步文本长度。

直觉上：

- 太短的 step 可能过于提纲化
- 太长的 step 可能把多个动作糅在一个自然语言段落里

但这个维度暂时不适合作为第一轮硬筛选条件，因为：

1. 不同 source 的写作风格差异很大
2. 长文本不一定差，很多协议会把参数、注意事项和动作写在一起
3. 这个问题更适合在后续 benchmark 构造阶段，通过动作可解析性再做二次筛选

因此，目前默认不过早引入：

- 平均 step 长度门槛
- 单步最大长度门槛
- 单步最小长度门槛

### 15.12 这一版的定位

所以，当前 `protocol_min_v1` 的定位可以概括为：

> 一套字段最小、但过滤已经面向 benchmark 需求收紧的 protocol 统一底座。

它不是“尽可能多留样本”的宽松清洗结果，而是：

- 保留能支撑后续任务构造的关键信息
- 提前去掉明显不适合长链 benchmark 的样本
- 给后续 asset / action / planning 对齐留出足够结构空间

## 16. 最后给一个务实判断

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
