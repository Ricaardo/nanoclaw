# Unit Economics Analysis

description: Analyze unit economics for PE targets — ARR cohorts, LTV/CAC, net retention, payback periods, revenue quality, and margin waterfall. Essential for software/SaaS, recurring revenue, and subscription businesses. Use when evaluating revenue quality, building a cohort analysis, or assessing customer economics. Triggers on "unit economics", "cohort analysis", "ARR analysis", "LTV CAC", "net retention", "revenue quality", or "customer economics". 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。

## Workflow

### Step 1: Identify Business Model

Determine the revenue model to tailor the analysis:
- **SaaS / Subscription**: ARR, net retention, cohorts
- **Recurring services**: Contract value, renewal rates, upsell
- **Transaction / usage-based**: Revenue per transaction, volume trends, take rate
- **Hybrid**: Break down by revenue stream

### Step 2: Core Metrics

#### ARR / Revenue Quality
- **ARR bridge**: Beginning ARR → New → Expansion → Contraction → Churn → Ending ARR
- **ARR by cohort**: Vintage analysis — how does each annual cohort retain and grow?
- **Revenue concentration**: Top 10/20/50 customers as % of total
- **Revenue by type**: Recurring vs. non-recurring vs. professional services
- **Contract structure**: ACV distribution, multi-year %, auto-renewal %

#### Customer Economics
- **CAC (Customer Acquisition Cost)**: Total S&M spend / new customers acquired
- **LTV (Lifetime Value)**: (ARPU × Gross Margin) / Churn Rate
- **LTV:CAC ratio**: Target >3x for healthy businesses
- **CAC payback period**: Months to recover acquisition cost
- **Blended vs. segmented**: Break down by customer segment (enterprise vs. SMB vs. mid-market)

#### Retention & Expansion
- **Gross retention**: % of beginning ARR retained (excludes expansion)
- **Net retention (NDR)**: % of beginning ARR retained including expansion
- **Logo churn**: % of customers lost
- **Dollar churn**: % of revenue lost (often different from logo churn)
- **Expansion rate**: Upsell + cross-sell as % of beginning ARR

#### Cohort Analysis
Build a cohort matrix showing:

| Cohort | Year 0 | Year 1 | Year 2 | Year 3 | Year 4 |
|--------|--------|--------|--------|--------|--------|
| 2020 | $1.0M | $1.1M | $1.2M | $1.1M | |
| 2021 | $1.5M | $1.7M | $1.8M | | |
| 2022 | $2.0M | $2.3M | | | |
| 2023 | $3.0M | | | | |

Show both absolute $ and indexed (Year 0 = 100%) views.

#### Margin Waterfall
- Revenue → Gross Profit → Contribution Margin → EBITDA
- Fully loaded unit economics: what does it cost to acquire, serve, and retain a customer?
- Gross margin by revenue stream (subscription vs. services vs. other)

### Step 3: Benchmarking

Compare unit economics to relevant benchmarks:
- **SaaS Rule of 40**: Growth rate + EBITDA margin > 40%
- **SaaS Magic Number**: Net new ARR / prior period S&M spend > 0.75x
- **NDR benchmarks**: Best-in-class >120%, good >110%, concerning <100%
- **LTV:CAC**: Best-in-class >5x, good >3x, concerning <2x
- **Gross retention**: Best-in-class >95%, good >90%, concerning <85%
- **CAC payback**: Best-in-class <12mo, good <18mo, concerning >24mo

### Step 4: Revenue Quality Score

Synthesize into a revenue quality assessment:

| Factor | Score (1-5) | Notes |
|--------|-------------|-------|
| Recurring % | | |
| Net retention | | |
| Customer concentration | | |
| Cohort stability | | |
| Growth durability | | |
| Margin profile | | |
| **Overall** | | |

### Step 5: Output

- Excel workbook with ARR bridge, cohort matrix, unit economics dashboard
- Summary slide with key metrics and benchmarks
- Red flags and areas for further diligence

## Important Notes

- Always ask for raw customer-level data if available — aggregate metrics can hide problems
- NDR above 100% can mask high gross churn if expansion is strong enough — always show both
- Cohort analysis is the single most important view for revenue quality — push for this data
- Differentiate between contracted ARR and actual recognized revenue
- For usage-based models, focus on consumption trends and expansion patterns rather than traditional ARR metrics
- Professional services revenue should be evaluated separately — it's not recurring and margins are typically lower


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
