# AGENTS 工作记录

## 1. 文件用途

这个文件用于给后续代理记录仓库级经验，内容必须公开可见且适合提交到公共仓库。

必须遵守：

- 不要记录口令、令牌、账号、私有地址、未公开数据集、机器专属敏感信息。
- 不要把本地临时命令输出原样大段贴进来。
- 只记录对后续工作真正有帮助的结构信息、踩坑经验和公开资料来源。
- 除非用户在当前对话里明确说了 `push`，否则不要执行 `git commit`，也不要执行 `git push`；完成修改后只做检查并汇报当前状态。

## 2. 仓库定位

- 这个仓库是 `LabOS` 的公开主页仓库。
- `README.md` 负责描述 benchmark 的总体设计。
- `README.md` 当前应保持固定的编号结构：
  - `1. 数据构造管线`
  - `2. Level 1`
  - `3. Level 2`
  - `4. Level 3`
  - 每个 level 默认写成“整体介绍 / 输入 / 输出 / 指标”
  - 在不改章节骨架的前提下，应尽量把任务定义、数据来源、输出约束和指标计算方式写清楚，不能只停留在一句话定义
- `docs/` 是 GitHub Pages 使用的静态站点目录。
- `data/protocol_v1/` 就是 protocol 数据源本身，也就是爬取下来的 `Nature Protocols` 语料，不要默认改动。

## 3. Benchmark 设计主线

- 整体 benchmark 目前按三个部分组织：
  - 实验资产理解
  - 长程规划
  - sim2real（当前页面里先作为预览位保留）
- 设计目标是同时对齐三个数据源：
  - `protocol` / `protocol_v1`：也就是爬取下来的 `Nature Protocols` 语料，提供科学语义、实验步骤细节、仪器用途理解
  - `AutoBio`：提供一部分可复用的资产、动作、具身任务对齐方式
  - `LabUtopia`：提供另一部分可复用的资产、动作、长链动作组织方式
- README 里的主框图应保持为三列直连结构：
  - 第一列：`Protocols`、`AutoBio`、`LabUtopia`
  - 第二列：`Steps`、`Assets`、`Actions`
  - 第三列：`Level 1: Asset Understanding`、`Level 2: Long-Horizon Planing`、`Level 3: Sim2Real`
  - 连线规则：
    - `Protocols -> Steps`
    - `AutoBio -> Assets`、`AutoBio -> Actions`
    - `LabUtopia -> Assets`、`LabUtopia -> Actions`
    - `Steps + Assets -> Level 1`
    - `Steps + Actions -> Level 2`
    - `Steps + Assets + Actions -> Level 3`
- 其中长程规划部分参考 `SGI-WetExperiment` 的评测形式：
  - 输入包含有限动作空间
  - 输出是动作组合与参数设置
  - 在本仓库的方案里，进一步收紧为合法的 Python 函数调用，便于用 Python AST 做解析和评测
- 当前 README 中三个 level 的任务定义需要保持一致：
  - `Level 1`
    - 输入是单个 `asset` 的三视图，加上一道选择题和候选项
    - 输出分成两部分：`reasoning_steps: list[string]` 与单字母 `answer`
    - 指标固定为 `Reasoning Step Accuracy` 与 `Answer Exact Match Accuracy`
  - `Level 2`
    - 输入固定为三部分：实验背景、实验约束与要求、动作空间
    - 其中动作空间来自 `AutoBio` 与 `LabUtopia`，并以 Python 函数定义形式给出
    - 实验约束不能直接泄露标准答案步骤
    - 输出是代码形式的动作序列
    - 评分逻辑对齐 `SGI-Bench` 的 `evaluation/task_3_wet_experiment/step_2_score.py`
    - 但实现上不再用正则解析自定义结构，而是直接解析 Python AST
    - 主指标写成 `Action Sequence Similarity` 与 `Parameter Accuracy`
    - `Action Sequence Similarity` 采用 SGI 脚本同款的 Kendall tau 风格顺序相似度，不是 LCS
    - `Parameter Accuracy` 不是逐 token 文本匹配，而是逐步检查动作名、参数键集合、raw/generated 引用类型以及变量依赖映射
  - `Level 3`
    - 评测逻辑与 `AutoBio` 官方仓库保持一致
    - 输入接口应对齐 `autobio/evaluator.py` 的 runtime observation 形式
    - 输出接口应对齐策略返回的低层 action chunk，而不是自然语言或符号步骤
    - 当前变化点只是任务链条更长、步骤更多、依赖更深

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

- 左侧栏用于切换三个 level。
- 每个 part 目前放了两个示例题目。
- 主视图包含：
  - Level 1：单个 3D 仪器
  - Level 2：多个仪器同时展示
  - Level 3：视频
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
- SGI-Bench `step_2_score.py`：`https://github.com/InternScience/SGI-Bench/blob/main/evaluation/task_3_wet_experiment/step_2_score.py`
- AutoBio `autobio/evaluate.py`：`https://github.com/autobio-bench/AutoBio/blob/main/autobio/evaluate.py`
- AutoBio `autobio/evaluator.py`：`https://github.com/autobio-bench/AutoBio/blob/main/autobio/evaluator.py`
- AutoBio `autobio/task.py`：`https://github.com/autobio-bench/AutoBio/blob/main/autobio/task.py`
- AutoBio `autobio/mani_thermal_cycler.py`：`https://github.com/autobio-bench/AutoBio/blob/main/autobio/mani_thermal_cycler.py`
- AutoBio thermal cycler close Sim2Real 视频：`https://huggingface.co/datasets/autobio-bench/thermal_cycler_close-mujoco`
- AutoBio insert Sim2Real 视频：`https://huggingface.co/datasets/autobio-bench/insert-mujoco`
- 当前页面接入过的公开原始视频直链包括：
  - thermal cycler close front：`https://huggingface.co/datasets/autobio-bench/thermal_cycler_close-mujoco/resolve/main/videos/chunk-000/image/episode_000000.mp4`
  - thermal cycler close wrist：`https://huggingface.co/datasets/autobio-bench/thermal_cycler_close-mujoco/resolve/main/videos/chunk-000/wrist_image/episode_000000.mp4`
  - insert front：`https://huggingface.co/datasets/autobio-bench/insert-mujoco/resolve/main/videos/chunk-000/image/episode_000000.mp4`
  - insert wrist：`https://huggingface.co/datasets/autobio-bench/insert-mujoco/resolve/main/videos/chunk-000/wrist_image/episode_000000.mp4`

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
- 页面左侧展示逻辑目前是分 level 的：
  - Level 1 左侧是单个 3D 资产
  - Level 2 左侧是多仪器视图
  - Level 3 左侧是多视频视图
- Level 3 的视频实现现在按 `videoSources` 动态渲染，不再把视频卡片数量写死在 `index.html` 里。
- 当前仓库内已落地的 Level 3 视频副本位于 `docs/assets/videos/`，这样 GitHub Pages 可以直接稳定提供静态文件。
- 对低分辨率仿真视频，页面上应限制展示尺寸，不要把视频区域放得过大；当前实现通过限制 `video-grid` 的最大宽度和视频高度来避免画面发糊。
- 如果用户明确要求“视频框就是原始视频大小”，不要再用固定 `aspect-ratio` 或 `object-fit: contain` 容器；更合适的做法是按视频元数据里的原始宽度渲染卡片，并只在视口更窄时缩小。
- Level 2 的公开页面展示里，不再直接铺开有限动作空间的 `def ...` 定义，也不需要展示带参数的整段参考程序；更适合只保留动作顺序，用小圆角矩形卡片承载动作名，再用排列顺序或箭头表达流程。

## 10. 浏览器验证经验

- 本地预览可直接使用：
  - `python3 -m http.server 8000`
- 页面级静态检查至少要做：
  - `node --check docs/app.js`
  - `git diff --check -- docs AGENTS.md`
  - `curl -I` 检查页面、模型、视频资源是否返回 `200`
- 如果 Level 3 视频改成新的 Hugging Face 来源，优先把最小必要集合下载到仓库内，再在页面里引用仓库内副本，避免运行时依赖跨站视频资源。
- 如果要做浏览器级验证，Playwright 是可用方案。
- 当前环境里直接跑 `npx playwright ...` 可能会因为默认 `~/.npm` 缓存目录不可写而失败；可改用：
  - `env npm_config_cache=/tmp/.npm PLAYWRIGHT_BROWSERS_PATH=/tmp/pw-browsers npx playwright ...`
- 如果只是做移动端截图验证，优先继续用 Chromium 并手动指定手机视口，例如：
  - `--browser chromium --viewport-size "390,844"`
- 不要默认用 `--device "iPhone 13"` 这类预设；在当前环境下它可能触发额外的 WebKit 浏览器依赖，导致无关的缺包报错。
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

## 11. 评测逻辑经验

- Level 2 不能再写成“顺序相似度 + 参数准确率”这种只讲名字、不讲算法的描述；需要明确说明其来源和计算方式。
- 对照 `SGI-Bench` 的 `step_2_score.py`，真正的 Level 2 评分逻辑有三层：
  - 先把程序解析成 step list，每一步包含 `action / input / output`
  - `Action Sequence Similarity` 比较的是动作顺序，SGI 用的是 Kendall tau 风格相似度
  - `Parameter Accuracy` 比较的是动作接口和依赖链是否一致，而不是纯字符串完全匹配
- 在 LabOS 里，因为动作输出本来就是 Python 代码，最稳妥的实现方式是：
  - 用 Python AST 抽取函数调用
  - 识别每一步的输出变量
  - 区分某个参数是在引用原始输入，还是在引用前序步骤生成变量
  - 用预测输出变量到标准输出变量的映射去检查后续依赖
- 对齐 SGI 时要注意：
  - 如果预测步骤数和标准步骤数不同，SGI 的顺序相似度会直接记 `0`
  - `Parameter Accuracy` 会把动作名错误、参数键错误、变量类型错误、依赖映射错误，以及多出 / 缺失步骤都记入 `error_count`
  - SGI 额外会计算 `final_score = (action_sequence_similarity + parameter_accuracy) / 2`，但公开文档里仍应先把基础指标解释清楚
- Level 3 不能只写“沿用 AutoBio 评测逻辑”；需要说明具体沿用了什么。
- 对照 AutoBio 官方代码：
  - `autobio/task.py` 定义了任务注册、`time_limit`、`early_stop` 和 `check()`
  - `autobio/evaluator.py` 定义了 runtime observation 结构，包括 `prompt`、`observation/state`、`observation/image`、`observation/wrist_image` 和可选历史图像
  - `autobio/evaluator.py` 也定义了 rollout 逻辑：策略输出二维 action chunk，逐行写入 `data.ctrl[action_indices]`，每行 action 默认推进 10 个 simulator steps
  - `autobio/evaluate.py` 负责按多个 seed 跑 episode，并把每个 episode 的二值结果保存下来
  - 具体任务文件如 `autobio/mani_thermal_cycler.py` 会给出 `task_info['prefix']`、`state_indices`、`action_indices`、`camera_mapping` 和 `check()` 的任务完成条件
- 因此，LabOS 的 Level 3 如果要保持“和 AutoBio 一致”，就应该保持：
  - episode 级 rollout
  - `task.check()` 作为成功判据
  - `time_limit` 与 `early_stop` 控制 episode 终止
  - 仿真 warning / FatalError 直接记失败
  - 最终按多 seed episode 的平均 success rate 报告结果
- LabOS 的扩展点不在评测器骨架，而在任务本身：
  - 把单个短任务扩展成更长的 protocol 段
  - 让 `prompt` 覆盖更长的实验目标
  - 让 `check()` 覆盖多阶段子目标
  - 让 `time_limit` 足以容纳更长的执行链

## 12. 公共文档写作约束

- 面向公开仓库的说明应尽量稳定、读者导向。
- 非必要不要在公开文档里写机器绝对路径。
- 如果确实要提路径，只在当前任务确有必要时写出。
- 介绍 benchmark 时，优先写清：
  - 任务定义
  - 输入输出形式
  - 评分思路
  - 各资料源各自承担的角色
- 少写过程流水账，多写结构性结论。

## 13. 后续代理建议

- 如果继续扩展 GitHub Pages，优先保持静态化和轻依赖。
- 如果继续补题目，先保持每个 part 有代表性样例，再逐步扩到完整数据组织。
- 如果继续补具身展示，优先复用已经复制到仓库内的公开安全素材。
- 如果继续做 3D 相关改动，结束前至少确认：
  - 页面能打开
  - viewer 非空白
  - 资源路径有效
  - 移动端和桌面端都没有明显布局崩坏
