# 热力图进阶（相关分析高级画法）

> **触发词**："热力图进阶"、"相关分析进阶图"、"Mantel 图"、"皮尔逊整合矩阵"。用户提到这些词时，**优先读取本文件**，再参考 `chart_knowledge_base.md`（Part 2 热力图/矩阵散点图）与 `plot_recipes.md` §8。
>
> 来源：公众号文章《Mantel test 相关性热图美化》（R ggcor）与《整合数据分布+拟合线+置信区间+相关系数的皮尔逊相关可视化》（Python），2026-08 学习入库。

## A. Mantel test 相关性热图（环境/生态数据标配）

**适用场景**：环境理化数据 vs 物种/样本；需要同时展示"变量间相关"与"变量-分组间显著关联"（如土壤因子与菌群、水体指标与群落）。

**图结构**：

- 矩阵单元格：Pearson（或 Spearman）相关系数，方块/圆形/星形等形状均可，推荐方块（`geom_square`）；发散色渐变，**必须 `midpoint=0` 且高低色对称**（示例：低 `#42B540FF` 绿 → 中 白 → 高 `#00468BFF` 蓝）。
- 连线条：Mantel 检验结果——**线粗细 = Mantel's r**（示例分档 0.5 / 1 / 2），**线颜色 = p 值**（示例：`< 0.01` 深蓝、`0.01–0.05` 橙、`≥ 0.05` 绿）。
- 图例三项：`Pearson's r`（fill 色条）、`Mantel's r`（size）、`Mantel's p`（colour）。

**Python 等价要点**（R `ggcor::quickcor` + `anno_link` 的替代）：

- 相关矩阵：`sns.heatmap(corr, cmap='RdBu_r'/'coolwarm', center=0)` 或自定义发散色。
- Mantel 检验：`scipy.stats` 无现成函数；可用 `skbio.stats.distance.mantel`（如已安装）或自实现（距离矩阵 + 置换检验）；论文中必须写明置换次数与 p 值口径。
- 连线叠加：用 `matplotlib.collections.LineCollection` 或逐条 `plot` 叠加在热图之上，`linewidth` 映射 r 分档、`color` 映射 p 阈值。
- 图例：自定义三条图例（colorbar + LineCollection legend）。

```python
# Mantel 连线映射（示意）：给定 (from, to, r, p) 列表
# width = {r < 0.5: 0.5, r < 0.8: 1, else: 2}（分档可按数据调整）
# color = {p < 0.01: '#00468B', p < 0.05: '#F26F21', else: '#42B540'}
# 叠加方式：ax.add_collection(LineCollection(segments, linewidths=widths, colors=colors))
```

**硬性规则（覆盖来源默认）**：图内无标题；三条图例名称与阈值在图注中说明；发散色必须中点对称；显著性阈值（0.01/0.05）与置换次数必须在图注或正文交代。

## B. 皮尔逊相关整合矩阵（分布 + 拟合线 + 置信区间 + 相关系数）

**适用场景**：3–8 个连续变量，希望一张图同时回答"单变量分布、两两线性趋势、统计显著性、相关强度"。

**图结构**：

- **对角线**：单变量直方图 + KDE（分布形态）。
- **下三角**：散点 + 线性拟合线 + **95% 置信区间**（`statsmodels OLS`，`fill_between`）。
- **上三角**：皮尔逊相关系数热图/数字标注 + **显著性星标**：`p < 0.05 → *`、`p < 0.01 → **`、`p < 0.001 → ***`（不显著标 `ns` 或留空）。

```python
# B 整合矩阵（Python/matplotlib + statsmodels，可直接改数据运行）
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from scipy import stats

rng = np.random.default_rng(8)
n = 200
base = rng.normal(0, 1, n)
df = pd.DataFrame({
    'A': base + rng.normal(0, 0.5, n),
    'B': base + rng.normal(0, 0.3, n),
    'C': -base + rng.normal(0, 0.4, n),
    'D': rng.normal(0, 1, n),
})
cols = list(df.columns)
k = len(cols)

def stars(p):
    return '***' if p < 0.001 else '**' if p < 0.01 else '*' if p < 0.05 else 'ns'

fig, axes = plt.subplots(k, k, figsize=(7.0, 7.0))
for i, yi in enumerate(cols):
    for j, xj in enumerate(cols):
        ax = axes[i, j]
        if i == j:                                   # 对角线：直方图 + KDE
            ax.hist(df[yi], bins=20, color='#9ECAE1', edgecolor='white', density=True)
            ax.tick_params(labelleft=False, labelbottom=False)
        elif i > j:                                  # 下三角：散点 + 拟合线 + 95%CI
            ax.scatter(df[xj], df[yi], s=10, alpha=0.5, color='#0F6BBD', edgecolor='none')
            X = sm.add_constant(df[xj])
            model = sm.OLS(df[yi], X).fit()
            xv = np.linspace(df[xj].min(), df[xj].max(), 100)
            pred = model.get_prediction(sm.add_constant(xv))
            ax.plot(xv, pred.predicted_mean, color='#D55E00', lw=1.2)
            ax.fill_between(xv, pred.conf_int()[:, 0], pred.conf_int()[:, 1],
                            color='#D55E00', alpha=0.15)
            ax.tick_params(labelleft=False, labelbottom=False)
        else:                                        # 上三角：r + 显著性星标
            r, p = stats.pearsonr(df[xj], df[yi])
            ax.text(0.5, 0.5, f'{r:.2f}{stars(p)}', ha='center', va='center',
                    fontsize=8.5, color='#083C5F')
            ax.set_xticks([]); ax.set_yticks([])
            ax.set_facecolor('#F5F7FA')
        if i == k - 1:
            ax.set_xlabel(xj, fontsize=8.5)
        if j == 0:
            ax.set_ylabel(yi, fontsize=8.5)
fig.tight_layout()
# 图内不写标题（用户定制）；星标规则写进图注
export_figure(fig, 'figs/09_advanced_corr_matrix', formats=['png'],
              size_inches=(7.0, 7.0), dpi=300)
```

**硬性规则**：变量 > 8 时放弃整合矩阵，退化用上三角热力图（§8a）；样本量过小（<30）时置信区间不可靠，先核样本量；图内无标题；星标阈值在图注说明。

## 与基础热力图的关系

- 基础相关热力图：`chart_knowledge_base.md` Part 2（特征 5–30，发散色，半矩阵）+ `plot_recipes.md` §8a。
- 需要"更高级的展示/统计检验"时：优先本文件 A（Mantel 连线）或 B（整合矩阵），按数据类型与论证目的二选一，不要同时堆两种。
