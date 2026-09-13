# Steam 中文评论与本地化观察站

> 谁在被中文玩家看见？——追踪 Steam 热门游戏的简体中文支持、中文评论参与度与评价落差。

[![Quality checks](https://github.com/WhiterHJ/steam-cn-localization-analysis/actions/workflows/quality.yml/badge.svg)](https://github.com/WhiterHJ/steam-cn-localization-analysis/actions/workflows/quality.yml)
[![Refresh data](https://github.com/WhiterHJ/steam-cn-localization-analysis/actions/workflows/update-data.yml/badge.svg)](https://github.com/WhiterHJ/steam-cn-localization-analysis/actions/workflows/update-data.yml)

这是一个自动采集、自动分析并公开展示的专题数据产品，不要求访客上传数据。它读取 Steam 全球畅销榜和最常游玩榜，构建游戏级公开快照，并生成无需后端的交互式中文数据故事。

## 首期发现

2026-09-12 UTC 快照包含146款有效游戏，其中131款达到稳健展示阈值：

- 88.36%的热门游戏标注支持简体中文；
- 95.21%的游戏至少出现1条简体中文评论；
- 稳健样本的中文评论占比中位数为12.34%；
- 中文好评率相对非中文好评率的中位差为−9.23个百分点；
- 支持简体中文组的中文评论占比中位数为13.02%，未标注组为2.57%。组间差异显著，但这是观察性关联，不是因果估计。

完整解释见[首期分析报告](docs/analysis_report.md)，指标边界见[研究方法](docs/methodology.md)。

## 当前研究边界

- “中文评论”指评论时选择的语言，不等同于玩家国籍或所在地区。
- 评论数量用于衡量公开评论参与度，不等同于销量、玩家数或收入。
- 项目分析的是进入所选 Steam 榜单的热门游戏，不能代表全部 Steam 游戏。
- 观察性数据只能说明相关关系，不能证明增加简体中文支持会导致销量或好评率变化。

## 公开成果

- 交互网站：[在线访问](https://whiterhj.github.io/steam-cn-localization-analysis/)
- 可复现的数据采集、清洗、统计分析与网站代码
- [游戏级公开快照](data/published/snapshots)
- [数据字典](docs/data_dictionary.md)、[指标口径](docs/methodology.md)和研究限制
- [DuckDB SQL](sql)与阶段性分析报告

## 数据源

- [Steam Charts](https://store.steampowered.com/charts/)
- [Steam 用户评论接口](https://partner.steamgames.com/doc/store/getreviews)
- Steam 商店公开页面与商品信息

## 当前进度

- [x] 建立项目章程与研究边界
- [x] 验证10款游戏的商店信息采集
- [x] 验证全语言与简体中文评论汇总
- [x] 建立缓存、重试、指标计算和质量检查
- [x] 自动采集并去重 Steam 热门榜单样本
- [x] 建立生产数据模型与公开快照
- [x] 完成描述统计、组间检验与结论边界审查
- [x] 构建并在桌面/移动端验收交互式数据故事网站
- [x] 创建远程仓库并启用 GitHub Pages
- [ ] 发布首个 Release

可行性验证结果见[数据源可行性报告](docs/feasibility_report.md)。

## 本地开发

项目使用 Python 3.12。完整流程说明见[运维文档](docs/operations.md)。

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m steam_cn_insights --project-root .
```

采集当前Steam畅销榜和最常游玩榜：

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m steam_cn_insights charts --project-root .
```

将榜单候选转换为经过验证的游戏与评论指标快照：

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m steam_cn_insights snapshot --project-root .
```

生成 Parquet、DuckDB、统计摘要和网站数据：

```powershell
.\.venv\Scripts\python.exe -m steam_cn_insights analyze --project-root .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

## 数据与隐私

项目不发布 SteamID 或大批评论原文。公开快照只包含游戏级商店信息与评论汇总。代码使用 MIT License；Steam 来源数据仍受其各自条款约束。本项目与 Valve 或 Steam 无隶属关系。
