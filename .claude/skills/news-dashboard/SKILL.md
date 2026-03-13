---
name: news-dashboard
description: "Unified news intelligence: macro aggregation (Finnhub), deep event impact analysis (WebSearch 6-step), and per-stock sentiment (yfinance). Three modes: --mode market (default), --mode deep, --mode stock TICKER. 当用户询问市场新闻、事件影响分析、个股新闻情绪时触发。支持美股/A股/港股/加密货币/贵金属多市场。"
---

# News Dashboard Skill

三合一新闻分析工具，整合宏观新闻聚合、深度事件影响分析和个股新闻情绪。

## When to Use This Skill

- 「市场近期有什么新闻？」→ `--mode market`（默认）
- 「最近 10 天重大事件对市场影响？」→ `--mode deep`
- 「AAPL 最近有什么新闻？」→ `--mode stock AAPL`

---

## Mode 1: Market（宏观新闻聚合）

**来源:** Finnhub API + yfinance（需 `FINNHUB_API_KEY`）

### 执行

```bash
python3 skills/news-dashboard/scripts/macro_news_dashboard.py \
  --finnhub-key "$FINNHUB_API_KEY" --lang zh
```

可选参数: `--output-dir`, `--lookback-days 3`, `--calendar-days 14`, `--watchlist SPY,QQQ,AAPL,NVDA,JPM,XLE`

### 输出 4 板块

| # | 板块 | 内容 |
|---|------|------|
| 1 | 热点话题 | Finnhub 市场新闻聚类 + 影响力评分 |
| 2 | 央行动态 | Fed/ECB/BOJ/PBOC 关键词过滤 |
| 3 | 经济日历 | 未来 14 天高/中影响事件 |
| 4 | 板块新闻 | 按 watchlist ticker 分组 |

~8-12 Finnhub + 1 yfinance 调用。

---

## Mode 2: Deep（深度事件影响分析）

**来源:** WebSearch + WebFetch（无需 API Key）

6 步结构化工作流，分析过去 10 天重大事件对股市和大宗商品的影响。

### Step 1: 新闻收集

通过 WebSearch 并行搜索 6 类新闻：

| 类别 | 搜索关键词示例 |
|------|---------------|
| 货币政策 | FOMC meeting, Fed interest rate, ECB decision |
| 经济数据 | CPI inflation, NFP jobs report, GDP |
| 巨头财报 | NVIDIA earnings, Apple earnings |
| 地缘政治 | Middle East oil, Ukraine war, trade tariffs |
| 大宗商品 | oil prices, gold prices, OPEC meeting |
| 企业新闻 | M&A announcement, bankruptcy, credit downgrade |

**优先信源:** FederalReserve.gov, SEC.gov → Bloomberg, Reuters, WSJ → CNBC, MarketWatch

收集每条新闻：日期时间、事件类型、信源可信度、初始市场反应。

### Step 2: 加载知识库

根据收集到的新闻类型，按需加载 references/ 参考文件：

- **必加载:** `market_event_patterns.md`, `trusted_news_sources.md`
- **货币政策:** 参考央行政策事件模式
- **地缘政治/商品:** 加载 `geopolitical_commodity_correlations.md`
- **巨头财报:** 加载 `corporate_news_impact.md`

### Step 3: 影响力评分

三维评估框架：

**资产价格影响（主因子）：**
- 股指: Severe ±2%+ / Major ±1-2% / Moderate ±0.5-1%
- 商品: Oil Severe ±5%+ / Gold Severe ±3%+
- 债券: 10Y Severe ±20bps+

**影响广度（乘数）：**
- 系统性 3x → 跨资产 2x → 板块级 1.5x → 个股级 1x

**前瞻意义（修正）：**
- 体制转换 +50% / 趋势确认 +25% / 孤立事件 0% / 反向信号 -25%

**计算:** `Impact Score = (价格分 × 广度乘数) × (1 + 前瞻修正)`

### Step 4: 市场反应分析

对 Impact Score >5 的事件分析：
- **即时反应:** 方向、幅度、时段（盘前/盘中/盘后）、VIX
- **多资产联动:** 股市 → 债市 → 商品 → 外汇 → 衍生品
- **模式比对:** 与知识库历史模式对比 → Consistent / Amplified / Dampened / Inverse
- **异常标记:** 市场忽视重大利空、小消息过度反应、避险资产失效

### Step 5: 相关性与因果评估

多事件交互分析：
- **叠加事件:** 同向影响（非线性放大）
- **对冲事件:** 反向影响（判断哪个主导）
- **序列事件:** 路径依赖（累积效应）
- **传导机制:** 直接渠道 → 间接渠道 → 情绪渠道 → 反馈循环

### Step 6: 报告输出

```markdown
# 市场新闻分析报告 - [日期范围]

## 执行摘要
[3-4 句：分析周期、重大事件数、主导主题、最高影响事件]

## 影响力排名表
| 排名 | 事件 | 日期 | 得分 | 受影响资产类别 | 市场反应 |

## 逐事件深度分析
### [排名]. [事件名] (Impact Score: X)
- 事件摘要 / 市场反应（即时+后续）/ 模式比对 / 板块影响

## 主题综合
- 主导叙事 / 事件关联 / 风险偏好评估 / 板块轮动 / 异常与意外

## 大宗商品深度
- 能源 / 贵金属 / 基本金属 / 农产品

## 前瞻展望
- 市场定位洞察 / 即将到来的催化剂 / 风险情景（3-5 个）

## 数据来源与方法论
```

**分析原则:**
1. 影响优于噪音 — 过滤小事件
2. 多资产视角 — 跨市场联动
3. 模式识别 — 历史比对 + 异常捕捉
4. 因果纪律 — 区分相关与因果
5. 量化反应 — 用具体 %/bps，不用模糊词
6. 信源分层 — 官方 > Tier 1 > 专业媒体

**常见陷阱:** 过度归因、近因偏差、后见之明、单因素分析、忽视幅度差异。

---

## Mode 3: Stock（个股新闻情绪）

**来源:** yfinance（无需 API Key）

### 执行

```bash
python3 skills/news-dashboard/scripts/news.py SYMBOL [--limit 10]
```

### 输出

返回 JSON：
- `articles` — 标题、来源、日期、链接
- `summary` — 整体情绪摘要

呈现关键标题，标注可能影响股价的重要新闻。

---

## Resources

### scripts/（可执行脚本）

| 脚本 | 用途 | 模式 |
|------|------|------|
| `macro_news_dashboard.py` | 宏观新闻主程序（收集+处理+报告） | market |
| `report_generator.py` | Markdown/JSON 报告生成 | market |
| `collectors/market_news_collector.py` | Finnhub 市场新闻收集 | market |
| `collectors/sector_news_collector.py` | Finnhub 板块新闻收集 | market |
| `collectors/fed_news_collector.py` | 央行新闻过滤 | market |
| `collectors/calendar_collector.py` | 经济日历收集 | market |
| `processors/news_classifier.py` | 新闻分类 | market |
| `processors/news_clusterer.py` | 新闻聚类 | market |
| `processors/impact_scorer.py` | 影响力评分 | market |
| `news.py` | 个股新闻获取（yfinance） | stock |

### references/（知识库，deep 模式按需加载）

| 文件 | 内容 |
|------|------|
| `market_event_patterns.md` | 央行/通胀/就业/GDP/地缘/财报/信用事件历史模式 |
| `geopolitical_commodity_correlations.md` | 地缘政治-商品相关性（能源/贵金属/基本金属/农产品/稀土） |
| `corporate_news_impact.md` | 巨头分析框架（Mag 7 + 金融/医疗/能源/消费/工业） |
| `trusted_news_sources.md` | 信源可信度分级（4 层） + 搜索策略 |

---

## 语言与输出规则

### 中文输出
- 所有分析报告、摘要、建议使用**中文**输出
- 保留英文的情况：ticker 代码（AAPL, 600519.SH）、专有名词首次出现时附英文（市盈率 P/E）、数据源名称
- 数字格式：使用国际通用格式（1,234.56），不使用中文万/亿换算（除非用户要求）

### 多市场 Ticker 识别
根据输入的 ticker 格式自动识别市场并选择数据源：
| 格式 | 示例 | 市场 | 数据源 |
|------|------|------|--------|
| 1-5 位大写字母 | AAPL, MSFT | 美股 | WebSearch / yfinance / FMP |
| 6位数字.SH/.SZ | 600519.SH, 000858.SZ | A 股 | AKShare / 东方财富 |
| 4-5位数字.HK | 00700.HK, 09988.HK | 港股 | AKShare |
| BTC, ETH 等 | BTC, ETH, SOL | 加密货币 | AKShare / CoinGecko |
| XAU, XAG | XAU, GLD | 贵金属 | AKShare |

### Dashboard JSON 输出（可选）
当用户请求 dashboard 格式时，在报告末尾额外输出 Recharts 兼容 JSON：
```json
{
  "title": "分析标题",
  "generated_at": "ISO8601时间戳",
  "charts": [
    {"id": "chart_1", "type": "line|bar|area|pie|heatmap", "title": "图表标题", "data": [...], "xKey": "date", "yKeys": ["value"]}
  ],
  "metrics": [
    {"label": "指标名", "value": "数值", "change": "+5.2%", "trend": "up|down|flat"}
  ],
  "summary": "一句话结论"
}
```
保存为 `reports/<skill_name>_dashboard_YYYYMMDD.json`
