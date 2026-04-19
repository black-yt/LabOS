# JoVE 调查记录

## 1. 结论

JoVE 值得关注，但**不适合当作未经授权的大规模主爬取源**。对当前 benchmark 而言，它更适合做一个**补充型、白名单式**数据源：

- 对 `Level 1: Asset Understanding` 价值很高
- 对 `Level 2: Long-Horizon Planing` 有中等价值
- 对 `Level 3: Sim2Real` 只有较弱的间接价值

核心原因不是内容质量，而是两点：

1. JoVE 的强项是“视频 + 教学解释 + 一部分 protocol 文本”，非常适合补充仪器理解和实验场景语义。
2. JoVE 官方条款明确限制机器人、爬虫、自动化抓取和站内内容聚合，很多内容还有订阅门槛，因此不能把它当作一个可以随意全站抓的开放协议库。

## 2. 官方内容形态

### 2.1 Science Education / Lab Manual / Lab Equipment

JoVE 的公开教学页和实验教学视频，对 `Level 1` 最有价值。

- [Basic Biology](https://www.jove.com/education/science-education/basic-biology)
  - 公开页面直接展示 `92 Videos`
  - 同页还写有 `450+ Multiple Choice Questions`
  - 目录中能看到大量基础实验仪器和操作主题，例如：
    - `An Introduction to the Centrifuge`
    - `Introduction to the Microplate Reader`
    - `An Introduction to the Micropipettor`
    - `An Introduction to Working in the Hood`
    - `Introduction to the Spectrophotometer`

- 代表性页面：
  - [Working with Centrifuges: Operation and Safety Measures](https://www.jove.com/v/10365/working-with-centrifuges-operation-and-safety-measures)
  - [Fume Hoods and Laminar Flow Cabinets](https://www.jove.com/v/11461/fume-hoods-and-laminar-flow-cabinets-laboratory-ventilation-safety)
  - [An Introduction to the Micropipettor](https://www.jove.com/v/10728/an-introduction-to-the-micropipettor)
  - [Introduction to the Spectrophotometer](https://www.jove.com/v/10029/introduction-to-the-spectrophotometer)

这些页面和主题非常贴近我们 `Level 1` 的目标：输入实验仪器图像和一个问题，输出选项答案。  
JoVE 这种内容的价值主要体现在：

- 能补充仪器的用途、适用场景、注意事项、安全规范
- 能帮助构造“设备识别 + 正确使用方式”的选择题
- 能帮助构造 reasoning steps，因为它本身就是教学解释型内容

### 2.2 Encyclopedia of Experiments / Journal Protocols

JoVE 不是只有教学视频，也有研究实验 protocol 内容。

- [Encyclopedia of Experiments](https://www.jove.com/research/encyclopedia-of-experiments)
  - 公开页显示大约 `2.3k+ videos`
  - 强调 experiment 的 practice 与 theory 结合

- 代表性 free access 页面：
  - [Isolation and Culturing of Primary Murine Adipocytes from Lean and Obese White Adipose Tissue](https://www.jove.com/v/67846/isolation-culturing-primary-murine-adipocytes-from-lean-obese)
  - 搜索摘要可见其公开结构包含 `Full Text`、`Summary`、`Abstract`、`Introduction`、`Protocol`、`Representative Results`、`Discussion`、`Materials`、`References`

这类内容对 `Level 2` 有帮助，因为它不仅有实验背景，也往往有较完整的 procedure 叙述、材料表和实验上下文。

### 2.3 Methods Collections

JoVE 还会按实验主题组织 protocol 集合，这对后续做定向采集很有用。

- [Methods Collections](https://app.jove.com/methods-collections)
- [3D Cell Culture: Methods, Applications, and Imaging](https://app.jove.com/methods-collections/1621/3d-cell-culture-methods-applications-and-imaging)

这一层的价值不在于直接做题，而在于：

- 帮助按主题组织协议
- 帮助发现某个实验方向下的相关 protocol 页面
- 适合做白名单采集入口，而不是全站乱抓

## 3. 对 benchmark 三个 level 的价值判断

### 3.1 Level 1: Asset Understanding

这是 JoVE 最值得用的地方，而且价值很高。

原因：

1. 它天然覆盖实验仪器、基础操作、安全规范。
2. 它本身就带有“教学解释”属性，非常适合生成 reasoning steps。
3. 它的题型和我们要做的“多视图 asset + 问题 + 选项”很匹配。

可直接利用的题目方向：

- 仪器的主要用途
- 哪种操作是正确的
- 哪种使用方式有安全风险
- 某种实验场景下应该使用哪类设备
- 仪器读数或结果判断的基础常识

但这里有一个边界要注意：  
JoVE 公开站点更偏“视频教学内容”，而我们 `Level 1` 需要的是**标准化 benchmark item**。所以它更像是一个**题目来源**，不是一个可以直接搬来的现成 benchmark 数据集。

### 3.2 Level 2: Long-Horizon Planing

JoVE 对 `Level 2` 有价值，但不能取代 `Protocols + AutoBio + LabUtopia` 的主框架。

它的主要帮助有三类：

1. 补实验背景和任务语义  
   JoVE 的 protocol 页通常会把实验目的、背景、关键步骤讲得比较清楚。

2. 补步骤链的自然语言表达  
   可以帮助把高层实验目标映射到更自然、更符合实际实验习惯的步骤描述。

3. 补设备与动作的实验语义  
   即使动作空间最终来自 `AutoBio` 和 `LabUtopia`，JoVE 仍然可以提供“为什么这一步需要某设备、某容器、某处理方式”的生物学语境。

但它不能直接替代主数据源的原因也很明确：

- 我们最终的 `Level 2` 输出是**代码形式的动作序列**
- 动作空间来自 `AutoBio` 和 `LabUtopia`
- 评测方式需要做 Python AST / 代码结构分析

JoVE 本身不是按这套形式组织的，因此它更适合作为：

- protocol 背景补充源
- step semantics 补充源
- 某些实验方向的补样本来源

而不是作为唯一主语料。

### 3.3 Level 3: Sim2Real

JoVE 对 `Level 3` 的直接价值较低。

原因：

- JoVE 的核心是人类实验视频和实验教学
- `Level 3` 真正需要的是和 `AutoBio` 一致的仿真/轨迹/具身执行评测逻辑
- 它不能直接提供机器人可执行的动作轨迹或仿真环境接口

它唯一的间接价值是：

- 帮助确认真实实验里更长链条 protocol 的自然顺序
- 帮助补真实实验场景中的设备上下文
- 帮助核对具身任务是否贴近真实 wet-lab 工作流

所以在优先级上，JoVE 不应成为 `Level 3` 的主数据来源。

## 4. 抓取风险与法律边界

这是 JoVE 最需要谨慎的部分。

### 4.1 官方条款层面

[JoVE Policies / Terms](https://www.jove.com/about/policies) 明确限制：

- 使用机器人、爬虫、自动化装置或自动化流程访问站点
- 通过 web scraping 的方式收集站内内容
- 对站内内容做系统化聚合、索引、镜像或再分发

因此，**未经授权的大规模程序化抓取不合适**。  
如果后续真的要系统性利用 JoVE，合理路径应该是：

1. 只采集公开可访问的少量白名单页面
2. 或者拿到机构许可 / 书面授权 / 官方合作接口

### 4.2 访问控制层面

实际访问中，JoVE 还会出现机器人验证与订阅访问限制。  
这意味着即使不谈法律条款，从工程角度看也不适合做“全站自动抓取”。

### 4.3 版权与再分发层面

即使能访问到页面，也不能想当然地把视频、截图、转录文本、题库内容直接并入公开 benchmark。  
尤其是视频帧、缩略图、转录文本和完整题目内容，后续都要单独看授权边界。

## 5. 与当前仓库已有 `protocol_v1` 的关系

本仓库已经处理过一部分 JoVE 来源，但结果说明：**现有链路并不能充分吃到 JoVE 的真实价值**。

相关记录：

- [protocol_v1 总体说明](../protocol_v1/README.md)
- [protocol_v1 详细介绍](../protocol_v1/protocl_intro.md)

关键事实如下：

1. 当前 `protocol_v1` 中，JoVE 只保留了 `112 / 2148` 条 passing 样本。  
   见 [data/protocol_v1/README.md#L84](../protocol_v1/README.md#L84)

2. 当前文档明确写到：很多 JoVE 的 Table of Materials 在补充 PDF 中，而 EuroPMC 不会完整镜像。  
   这意味着如果只靠当前这条解析链，会丢掉很多材料表和设备信息。

3. 你当前本地统计中，`jove` 的 passing rate 只有 `5.3%`。  
   见 [data/protocol_v1/protocl_intro.md#L246](../protocol_v1/protocl_intro.md#L246)

4. 当前本地统计还指出：`jove` 的 `equipment` 很弱，112 条里只有 8 条非空。  
   见 [data/protocol_v1/protocl_intro.md#L527](../protocol_v1/protocl_intro.md#L527)

这说明两件事：

- JoVE 不是没价值
- 只是你当前的 PMC / XML / materials 解析链条，无法把它的主要价值完整提出来

换句话说，JoVE 的价值主要在它的**原生站点内容形态**，尤其是教学视频、设备页面、实验视频和 collection 索引，而不是当前 `protocol_v1` 里那批被动镜像下来的稀疏文本。

## 6. 建议的利用策略

### 6.1 建议做：白名单式、小规模、目标明确的采集

优先考虑三类对象：

1. `Level 1` 相关的公开仪器教学页
2. `Level 2` 相关的 free access protocol 页
3. `Methods Collections` 这类索引页，用于发现主题和组织白名单

### 6.2 不建议做：全站无差别抓取

不建议的原因包括：

- 条款不合适
- 技术上有反爬和订阅限制
- 版权与再分发边界不清楚
- 大规模抓下来后，很多内容也未必能直接进入公开 benchmark

### 6.3 在当前 benchmark 中的合理定位

JoVE 最合理的角色是：

- 为 `Level 1` 提供设备使用与实验教学素材
- 为 `Level 2` 提供步骤语义、实验背景和设备上下文
- 为整体 benchmark 增加真实实验视频语境

而不是替代：

- `Protocols` 提供的详细实验步骤文本
- `AutoBio` 和 `LabUtopia` 提供的 assets 与 actions

## 7. 推荐的白名单采集范围

如果后续真的要用，建议只做下面这几类。

### 7.1 可以重点考虑

- `Science Education` 中与基础实验设备直接相关的公开页面
- `Basic Biology` 等教学目录页中的仪器类主题
- `Free Access` 的 JoVE protocol 页面
- `Methods Collections` 索引页与专题页

### 7.2 建议暂时不要碰

- 需要订阅才能看的全文视频内容
- 大规模下载视频文件
- 大规模抓取转录文本
- 直接抓题库
- 把站内媒体资源重新分发到公开仓库

## 8. 如果未来要落成数据，建议保留的最小元数据

如果后续真的做白名单式整理，建议每个 JoVE 条目至少保留：

```json
{
  "id": "jove:<slug-or-article-id>",
  "url": "https://www.jove.com/...",
  "title": "...",
  "content_type": "science_education|lab_equipment|protocol|methods_collection",
  "access_type": "public|free_access|subscription",
  "benchmark_level": ["level1", "level2"],
  "instrument_keywords": ["centrifuge", "micropipette"],
  "task_keywords": ["cell culture", "spectrophotometry"],
  "notes": "why this page is useful"
}
```

注意，这里建议优先保留的是**元数据与人工判断结果**，而不是直接存原始媒体内容。

## 9. 最终判断

一句话总结：

**JoVE 值得用，但只能选择性用；最适合补 `Level 1`，其次补 `Level 2`，不适合作为当前 benchmark 的主协议语料库或可随意全站抓取的数据源。**

## 10. 相关链接

- [JoVE Basic Biology](https://www.jove.com/education/science-education/basic-biology)  
  公开教学目录，可用于判断 `Level 1` 的设备类素材密度

- [Working with Centrifuges: Operation and Safety Measures](https://www.jove.com/v/10365/working-with-centrifuges-operation-and-safety-measures)  
  典型仪器教学页面，适合设备用途与安全题

- [Fume Hoods and Laminar Flow Cabinets](https://www.jove.com/v/11461/fume-hoods-and-laminar-flow-cabinets-laboratory-ventilation-safety)  
  典型实验室安全与设备使用页面

- [An Introduction to the Micropipettor](https://www.jove.com/v/10728/an-introduction-to-the-micropipettor)  
  典型基础实验器材教学页面

- [Introduction to the Spectrophotometer](https://www.jove.com/v/10029/introduction-to-the-spectrophotometer)  
  典型仪器认知与使用页面

- [JoVE Encyclopedia of Experiments](https://www.jove.com/research/encyclopedia-of-experiments)  
  研究实验视频入口，适合判断 protocol 补充价值

- [JoVE Methods Collections](https://app.jove.com/methods-collections)  
  按主题组织的 protocol 集合入口，适合做白名单采集导航

- [3D Cell Culture: Methods, Applications, and Imaging](https://app.jove.com/methods-collections/1621/3d-cell-culture-methods-applications-and-imaging)  
  具体 collection 示例，说明 JoVE 会把协议按技术主题组织

- [Isolation and Culturing of Primary Murine Adipocytes from Lean and Obese White Adipose Tissue](https://www.jove.com/v/67846/isolation-culturing-primary-murine-adipocytes-from-lean-obese)  
  free access 的 protocol 示例，适合判断 `Level 2` 的补充价值

- [JoVE Policies / Terms](https://www.jove.com/about/policies)  
  需要重点核对的条款页面，尤其是自动化抓取、内容聚合和再分发边界

- [protocol_v1 README](../protocol_v1/README.md)  
  当前仓库里关于 JoVE 解析情况的总体说明

- [protocol_v1 详细介绍](../protocol_v1/protocl_intro.md)  
  当前仓库里关于 JoVE 通过率、材料表缺失和 equipment 稀疏问题的详细统计
