# 数据字典

生产表：`game_snapshot`。一行代表一个采集日期的一款 Steam 游戏。

| 字段 | 类型 | 含义 |
|---|---|---|
| `appid` | integer | Steam 应用唯一标识 |
| `name` | string | 商店公开游戏名 |
| `store_market` | string | 成功取得元数据的市场参数，优先 `cn`，失败后回退 `us` |
| `available_in_cn` | boolean | 中国区商店接口是否返回成功记录 |
| `supports_simplified_chinese` | boolean | 商店语言字段是否标注简体中文 |
| `all_review_count` | integer | 全语言评论总数 |
| `all_positive_count` | integer | 全语言好评数 |
| `all_negative_count` | integer | 全语言差评数 |
| `chinese_review_count` | integer | 简体中文评论总数 |
| `chinese_positive_count` | integer | 简体中文好评数 |
| `chinese_negative_count` | integer | 简体中文差评数 |
| `non_chinese_review_count` | integer | 全语言评论数减简体中文评论数 |
| `non_chinese_positive_count` | integer | 全语言好评数减简体中文好评数 |
| `chinese_review_share` | decimal | 简体中文评论数占全语言评论数的比例 |
| `all_positive_rate` | decimal | 全语言好评率 |
| `chinese_positive_rate` | decimal | 简体中文好评率 |
| `non_chinese_positive_rate` | decimal | 非简体中文好评率 |
| `positive_rate_gap` | decimal | 中文好评率减全语言好评率；保留供旧版本比较 |
| `chinese_vs_non_chinese_gap` | decimal | 中文好评率减非中文好评率；正式分析主指标 |
| `mostplayed_rank` | nullable integer | 最常游玩榜名次 |
| `topselling_rank` | nullable integer | 全球畅销榜名次 |
| `best_chart_rank` | integer | 两个榜单中的最佳名次 |
| `chart_membership` | string | 两榜、仅畅销榜或仅最常游玩榜 |
| `sample_origin` | string | `chart` 表示每日热门榜；`curated_contrast` 表示精选对照池 |
| `sample_origin_label` | string | 网站显示使用的中文样本来源标签 |
| `curated_reason` | string | 精选案例的入池理由；热门榜游戏为空 |
| `review_threshold_eligible` | boolean | 评论量是否达到稳健展示阈值，不考虑样本来源 |
| `analysis_eligible` | boolean | 是否属于热门榜且达到稳健展示阈值；精选对照池始终为否 |
| `snapshot_date` | date | 快照归属日期（UTC） |
| `collected_at_utc` | timestamp | 采集完成时间（UTC） |

其他商店字段（价格、开发商、发行商、类型和发售日期）用于未来分层分析。不同地区返回的货币不可直接混合比较。
