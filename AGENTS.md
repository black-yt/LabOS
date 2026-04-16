# AGENTS 工作记录

## 1. 文件用途

这个文件用于给后续代理记录仓库级经验，内容必须公开可见且适合提交到公共仓库。

必须遵守：

- 不要记录口令、令牌、账号、私有地址、未公开数据集、机器专属敏感信息。
- 不要把本地临时命令输出原样大段贴进来。
- 只记录对后续工作真正有帮助的结构信息、踩坑经验和公开资料来源。

## 2. 仓库定位

- 这个仓库是 `LabOS` 的公开主页仓库。
- `README.md` 负责描述 benchmark 的总体设计。
- `docs/` 是 GitHub Pages 使用的静态站点目录。
- `data/protocol_v1/` 是仓库里已有的一份本地语料快照，不要默认改动。

## 3. Benchmark 设计主线

- 整体 benchmark 目前按三个部分组织：
  - 实验资产理解
  - 长程规划
  - sim2real（当前页面里先作为预览位保留）
- 设计目标是同时对齐两类来源：
  - `Nature Protocols`：提供科学语义、实验步骤细节、仪器用途理解
  - `AutoBio + LabUtopia`：提供可复用的资产、动作、具身任务对齐方式
- 其中长程规划部分参考 `SGI-WetExperiment` 的评测形式：
  - 输入包含有限动作空间
  - 输出是动作组合与参数设置
  - 在本仓库的方案里，进一步收紧为合法的 Python 函数调用，便于用 Python AST 做解析和评测

## 4. 静态站点结构

- 页面是纯静态实现：
  - `docs/index.html`
  - `docs/styles.css`
  - `docs/app.js`
- 站点使用 Three.js 公共 CDN，直接在浏览器里渲染实验仪器的 `OBJ` / `STL`。
- GitHub Pages 最简单的发布方式是：
  - 分支：`main`
  - 目录：`docs/`
- 首页直接进入 benchmark explorer，而不是单独做落地页。
- 页面支持深链接，格式例如：
  - `?section=part-1&item=asset-q1`
  - `?section=part-2&item=plan-q2`
  - `?section=part-3&item=sim-q1`

## 5. 当前页面内容

- 左侧栏用于切换三个 part。
- 每个 part 目前放了两个示例题目。
- 主视图包含：
  - 3D 仪器查看器
  - 图片或视频素材区
  - 示例题列表
  - 题目详情区
- 当前已经接入的 3D 示例资产包括：
  - 热循环仪
  - 小型离心机
  - 热混匀仪
  - 涡旋振荡器
  - 15 mL 离心管

## 6. 外部仓库与素材策略

- 外部目录一律视为只读。
- 严禁修改任何外部仓库中的代码、数据、网格模型、日志、文档、视频或脚本。
- 如果页面需要外部素材，只能把“最小必要集合”复制到当前仓库，再在当前仓库里使用。
- 当前页面里的素材主要来自一个本地只读参考工作区 `robot`，该工作区仅用于读取，不用于写入。
- 已复制到当前仓库的资源位于 `docs/assets/`，用途是公开展示 benchmark 结构，不是为了替代原始外部仓库。

## 7. 当前使用过的外部公开参考

- Nature Protocols：`https://www.nature.com/nprot/`
- SGI-WetExperiment：`https://huggingface.co/datasets/InternScience/SGI-WetExperiment`
- AutoBio：`https://github.com/autobio-bench/AutoBio`
- LabUtopia：`https://github.com/Rui-li023/LabUtopia`

## 8. 本地只读参考源说明

- 页面构建过程中读取过一个本地只读工作区 `robot`。
- 该工作区主要提供：
  - AutoBio 仪器网格模型
  - 已渲染好的示例视频片段
  - 资产组织方式的本地说明
- 后续代理如果继续做页面工作，可以继续把它当作参考源，但只能读，不能改。

## 9. 3D 资源处理经验

- 在 GitHub Pages 场景下，直接展示 `OBJ` / `STL` 是可行的。
- 对实验仪器页面来说，直接放 3D 模型比只放静态图更合适，因为：
  - 能直观看结构部件
  - 更容易和资产理解题、动作理解题对齐
  - 更方便后续扩展到 sim2real 展示
- 采用组合式加载比预先做成单个大模型更灵活：
  - 同一仪器的不同部件可以分别着色
  - 后续如果要做部件高亮、状态切换，会更方便
- 复制资源时优先选：
  - 体积适中
  - 结构清楚
  - 与 benchmark 示例题直接相关
- 如果以后继续加 3D 内容，优先复用已有公开安全的网格和视频，不要为了页面展示去改外部仿真或训练代码。

## 10. 浏览器验证经验

- 本地预览可直接使用：
  - `python3 -m http.server 8000`
- 页面级静态检查至少要做：
  - `node --check docs/app.js`
  - `git diff --check -- docs AGENTS.md`
  - `curl -I` 检查页面、模型、视频资源是否返回 `200`
- 如果要做浏览器级验证，Playwright 是可用方案。
- Three.js 通过 CDN 直接加载 `examples/jsm/*` 时，要注意这些模块内部会使用裸模块导入 `three`。
- 如果页面上只有空白 canvas 或 3D 完全不出现，而模型文件本身可以访问，优先检查是不是 `OrbitControls`、`OBJLoader`、`STLLoader` 的裸模块导入没有被浏览器解析。
- 当前仓库的修复方式是在 `docs/index.html` 里加入 `importmap`，把 `three` 映射到公共 CDN 的 `three.module.js`，这样 GitHub Pages 下的浏览器模块解析才稳定。
- 在 Ubuntu 24.04 环境下，Playwright 下载的 Chromium headless shell 可能缺系统库，实际补过的依赖包括：
  - `libnspr4`
  - `libnss3`
  - `libasound2t64`
  - 以及其依赖 `libasound2-data`、`alsa-topology-conf`、`alsa-ucm-conf`
- 可以用下面的方法定位缺库：
  - `ldd /tmp/pw-browsers/.../chrome-headless-shell | grep 'not found'`
- 安装完成后，再用 Playwright 截图验证页面是否真的能打开，而不是只停留在静态文件检查。

## 11. 公共文档写作约束

- 面向公开仓库的说明应尽量稳定、读者导向。
- 非必要不要在公开文档里写机器绝对路径。
- 如果确实要提路径，只在当前任务确有必要时写出。
- 介绍 benchmark 时，优先写清：
  - 任务定义
  - 输入输出形式
  - 评分思路
  - 各资料源各自承担的角色
- 少写过程流水账，多写结构性结论。

## 12. 后续代理建议

- 如果继续扩展 GitHub Pages，优先保持静态化和轻依赖。
- 如果继续补题目，先保持每个 part 有代表性样例，再逐步扩到完整数据组织。
- 如果继续补具身展示，优先复用已经复制到仓库内的公开安全素材。
- 如果继续做 3D 相关改动，结束前至少确认：
  - 页面能打开
  - viewer 非空白
  - 资源路径有效
  - 移动端和桌面端都没有明显布局崩坏
