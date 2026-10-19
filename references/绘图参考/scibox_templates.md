# 国赛论文流程图模板接入：sci-box（scibox-diagram）

本技能内置 `tools/drawio/scibox-diagram/`（源自 [jihe520/sci-box](https://github.com/jihe520/sci-box)，脚本与模板为原仓库自有内容，Tabler 图标为 MIT 许可，见 `ATTRIBUTION.md`）。提供四套论文级 draw.io 模板，配合 `tools/drawio/`（drawio-skill 通用工具链）完成渲染、校验、预览、导出与微调。

## 四套模板与国赛论文落位

| 模板 id | 版式 | 国赛典型落位 | 适合表达 |
| --- | --- | --- | --- |
| `roadmap-5band` | 954×1296 竖版五带 | 第 8 部分 问题分析：整体技术路线图 `fig_roadmap` | 提出问题 → 数据与指标 → 方法与机制 → 结果对比 → 评价推广，一页看懂全文骨架 |
| `framework-3col` | 1026 宽三栏（左阶段链 / 中内容块 / 右方法清单） | 问题分析：研究内容全景图（或模型总览） | 每个阶段对应哪些研究内容、用什么方法 |
| `stageflow-3col` | 1000 宽三栏（左方法链 / 中彩色流程块 / 右阶段说明） | 第 2 部分 数据预处理流程 / 第 3 部分 分问求解流程 `fig_flow_qN` | 阶段推进、决策分支、成果分发的执行流程 |
| `taskflow-land` | 1360 宽横版任务块（块内流水线 + 做法细节） | 多问任务拆解（任务一…任务四），适合 16:9 / 答辩 / 横排 | 每步写清方法、参数、结论 |

## 选择规则（先看这里）

1. 问题分析“整体思路”优先 `roadmap-5band`：其五带语义与国赛优秀论文技术路线图最常见的“提出问题→数据准备→模型方法→结果对比→评价推广”叙事一致，放 `fig_roadmap`。
2. 需要“阶段 × 内容 × 方法”三向对应 → `framework-3col`；需要“分阶段执行流程（含判断分支/成果分发/可回溯迭代）” → `stageflow-3col`。
3. 题目被拆成并列任务、每步要写方法与结论 → `taskflow-land`。
4. 以上都不是（算法伪代码流程、模型内部结构、指标体系树等）→ 走 `tools/drawio/SKILL.md` 通用工作流手写 XML，不要硬套模板。
5. 同类型非数据图全篇 ≤3 张：技术路线图全篇 1 张，每问求解流程图至多 1 张，同类不连续堆图。

## 使用步骤

1. 读 `tools/drawio/scibox-diagram/SKILL.md` 与对应模板参考 `tools/drawio/scibox-diagram/references/<template>.md`（先读“语义约定”再读“字数预算”；语义放错比超框严重，例如带① `items` 是并列子问题、带② 左右两侧分别汇入“数据链”与“指标链”）。
2. 复制 `tools/drawio/scibox-diagram/assets/<template>/example.json` 到 `PROJECT_ROOT/figures/` 改写：数值必须来自题面或真实运行结果，术语与正文一致，`____` 与 ①② 占位符必须替换或删除。
3. 渲染（工作目录为 `PROJECT_ROOT/figures/`；脚本路径用 `SKILL_ROOT/tools/drawio/scibox-diagram/scripts/`）：
   - `python scripts/roadmap_5band.py content.json -o fig_roadmap.drawio`
   - `python scripts/framework_3col.py content.json -o fig_framework.drawio`
   - `python scripts/stageflow_3col.py content.json -o fig_stageflow.drawio`
   - `python scripts/taskflow_land.py content.json -o fig_taskflow.drawio`
   （Windows 用 `python`；macOS/Linux 用 `python3`。渲染器写文件前会逐槽校验字数，超框会报具体预算。）
4. 静态体检：`python <SKILL_ROOT>/tools/drawio/scibox-diagram/scripts/check_layout.py fig_roadmap.drawio`，正常应 FAIL 0 / WARN 0；`--strict` 作门禁。
5. 预览与导出：优先 `export_figure.py fig_roadmap.drawio`（1:1 PNG + 矢量 PDF，需 draw.io 命令行；本脚本已带 Windows 安装目录兜底查找）；CLI 不可用时用 `preview_html.py fig_roadmap.drawio` 生成浏览器预览。导出后必须肉眼过两轮：① 文字溢出/压线；② 箭头方向与语义；③ 同族元素对齐同宽；④ 数值有无抄错。

## 用户硬性规则（覆盖模板默认）

- 图内无标题：模板自带的标题条属于图形元素，按 content JSON 填成图内容本身；不要在渲染图上再叠加“图1 xxx”。图题放图下方，正文“先引导 → 插图 → 紧随其后的分析”，连续两张图之间没有文字判为硬错误。
- 模板产物同样过全文图表门禁：图后必有分析段、同类型 ≤3、配色与全文一致（要换色时用 `tools/drawio/scripts/restyle.py` 或精确改 `fillColor`，保持模板色系的语义分层）、字号按最终印刷尺寸 ≥7.5pt。
- 落位：`.drawio` 与导出 PNG/PDF 放 `PROJECT_ROOT/figures/`，文件名与正文引用一致；保留 content JSON 作为可复现源。
- 尺寸提醒：954px 宽、16px 字号的图压到 A4 版心（约 `0.97\textwidth`）正文约 6.5pt，偏小；优先整页横排（`sidewaysfigure`）或改用横版 `taskflow-land` / 精简版，不要把 6.5pt 小字直接塞进正文。

## 与现有 drawio 工具链的分工

- scibox-diagram：四套论文级模板 + 渲染器 + 中文版式体检（`check_layout.py` 用中文字宽模型，全角=字号、半角=字号/2）。
- tools/drawio（drawio-skill）：通用 XML 工作流、validate/autolayout/shapesearch、样式预设、导出与 PNG 修复、浏览器降级。
- 模板产物微调（换色、改方向、加图标）用 drawio-skill 的脚本与 XML 编辑，不要重新手写整图。
