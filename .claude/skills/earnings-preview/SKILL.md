# Earnings Preview

description: Build pre-earnings analysis with estimate models, scenario frameworks, and key metrics to watch. Use before a company reports quarterly earnings to prepare positioning notes, set up bull/bear scenarios, and identify what will move the stock. Triggers on "earnings preview", "what to watch for [company] earnings", "pre-earnings", "earnings setup", or "preview Q[X] for [company]". 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。

## Workflow

### Step 1: Gather Context

- Identify the company and reporting quarter
- Pull consensus estimates via web search (revenue, EPS, key segment metrics)
- Find the earnings date and time (pre-market vs. after-hours)
- Review the company's prior quarter earnings call for any guidance or commentary

### Step 2: Key Metrics Framework

Build a "what to watch" framework specific to the company:

**Financial Metrics:**
- Revenue vs. consensus (total and by segment)
- EPS vs. consensus
- Margins (gross, operating, net) — expanding or contracting?
- Free cash flow
- Forward guidance vs. consensus

**Operational Metrics** (sector-specific):
- Tech/SaaS: ARR, net retention, RPO, customer count
- Retail: Same-store sales, traffic, basket size
- Industrials: Backlog, book-to-bill, price vs. volume
- Financials: NIM, credit quality, loan growth, fee income
- Healthcare: Scripts, patient volumes, pipeline updates

### Step 3: Scenario Analysis

Build 3 scenarios with stock price implications:

| Scenario | Revenue | EPS | Key Driver | Stock Reaction |
|----------|---------|-----|------------|----------------|
| Bull | | | | |
| Base | | | | |
| Bear | | | | |

For each scenario:
- What would need to happen operationally
- What management commentary would signal this
- Historical context — how has the stock moved on similar prints?

### Step 4: Catalyst Checklist

Identify the 3-5 things that will determine the stock's reaction:

1. [Metric] vs. [consensus/whisper number] — why it matters
2. [Guidance item] — what the buy-side expects to hear
3. [Narrative shift] — any strategic changes, M&A, restructuring

### Step 5: Output

One-page earnings preview with:
- Company, quarter, earnings date
- Consensus estimates table
- Key metrics to watch (ranked by importance)
- Bull/base/bear scenario table
- Catalyst checklist
- Trading setup: recent stock performance, implied move from options

## Important Notes

- Consensus estimates change — always note the source and date of estimates
- "Whisper numbers" from buy-side surveys are often more relevant than published consensus
- Historical earnings reactions help calibrate expectations (search for "[company] earnings reaction history")
- Options-implied move tells you what the market expects — compare to your scenarios

## 执行增强

### 自动化数据采集

使用以下工具自动收集财报前数据：

#### 共识预期获取
```bash
# 使用 fundamentals skill 获取 EPS/Revenue 估计
python3 skills/fundamentals/scripts/get_fundamentals.py TICKER
```

#### 隐含波动获取
```bash
# 使用 option-chain skill 获取期权隐含波动
python3 skills/option-chain/scripts/get_option_chain.py TICKER
```

#### 历史财报反应
使用 WebSearch 搜索: "[TICKER] earnings reaction history last 4 quarters"

### 隐含波动解读

| Implied Move | 历史平均 | 信号 |
|-------------|---------|------|
| IM > 历史均值×1.5 | — | 市场预期大波动，考虑跨式策略 |
| IM ≈ 历史均值 | — | 正常预期 |
| IM < 历史均值×0.7 | — | 市场低估波动，低成本对冲机会 |

### 输出格式示例

```json
{
  "ticker": "AAPL",
  "quarter": "Q1 FY2026",
  "earnings_date": "2026-01-30",
  "timing": "AMC",
  "consensus": {"revenue_b": 124.5, "eps": 2.35},
  "implied_move_pct": 4.2,
  "historical_avg_move_pct": 3.8,
  "scenarios": {
    "bull": {"revenue_b": 128, "eps": 2.50, "stock_reaction": "+6-8%"},
    "base": {"revenue_b": 125, "eps": 2.36, "stock_reaction": "-1 to +2%"},
    "bear": {"revenue_b": 121, "eps": 2.20, "stock_reaction": "-5-8%"}
  },
  "catalyst_checklist": ["iPhone revenue growth", "Services margins", "China demand", "AI capex guidance"]
}
```

### 数据补全
当自动数据源不可用时，使用 WebSearch 搜索:
- "[TICKER] Q[X] earnings consensus estimate"
- "[TICKER] earnings whisper number"
- "[TICKER] options implied move earnings"

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
