# 更新与发布说明

## 本地完整流程

```powershell
$env:PYTHONPATH = "src"
.\.venv\Scripts\python.exe -m steam_cn_insights charts --project-root . --refresh
.\.venv\Scripts\python.exe -m steam_cn_insights snapshot --project-root . --refresh
.\.venv\Scripts\python.exe -m steam_cn_insights analyze --project-root .
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
```

如需完全重放某天已经缓存的接口响应：

```powershell
.\.venv\Scripts\python.exe -m steam_cn_insights snapshot --project-root . --cache-date 2026-09-12
```

## 自动更新设计

`.github/workflows/update-data.yml` 每天在 UTC 03:17 尝试采集并部署。选择17分而不是整点，降低 GitHub Actions 高负载时的拥堵概率。

自动更新会：

1. 采集两个 Steam 榜单；
2. 拉取商店元数据及全语言/简体中文评论汇总；
3. 运行质量检查与统计分析；
4. 提交公开的游戏级快照与网页数据；
5. 将 `site/` 部署到 GitHub Pages。

这不是秒级实时系统，而是每日快照。Steam 数据源、网络或页面结构异常时，工作流会失败并保留上一版可用网站；可从 Actions 页面手动重新运行。

GitHub 对公共仓库的定时工作流有默认分支、延迟和长期无活动停用等规则，因此仓库仍保留 `workflow_dispatch` 手动入口。
