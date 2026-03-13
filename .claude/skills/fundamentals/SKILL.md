---
name: fundamentals
description: Get fundamental financial data including financials, earnings, and key metrics. Use when user asks about financials, earnings, revenue, profit, balance sheet, income statement, or company fundamentals. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Fundamentals

Fetch fundamental financial data from Yahoo Finance.

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/fundamentals.py SYMBOL [--type TYPE]
```

## Arguments

- `SYMBOL` - Ticker symbol
- `--type` - Data type: all, financials, earnings, info (default: all)

## Output

Returns JSON with:
- `info` - Key metrics (market cap, PE, EPS, dividend, etc.)
- `financials` - Recent quarterly/annual income statement data
- `earnings` - Historical and estimated earnings

Present key metrics clearly. Compare actual vs estimated earnings if relevant.

---

## Piotroski F-Score

Calculate Piotroski's F-Score to evaluate a company's financial strength using 9 fundamental criteria.

### Instructions

```bash
uv run python scripts/piotroski.py SYMBOL
```

### What is Piotroski F-Score?

Piotroski's F-Score is a fundamental analysis tool developed by Joseph Piotroski that evaluates a company's financial strength using 9 criteria. Each criterion scores 1 point if passed, 0 if failed, for a maximum score of 9.

### The 9 Criteria

1. **Positive Net Income** - Company is profitable
2. **Positive ROA** - Assets are generating returns
3. **Positive Operating Cash Flow** - Company generates cash from operations
4. **Cash Flow > Net Income** - High-quality earnings (cash exceeds accounting profit)
5. **Lower Long-Term Debt** - Decreasing leverage (improving financial position)
6. **Higher Current Ratio** - Improving liquidity
7. **No New Shares Issued** - No dilution (or share buybacks)
8. **Higher Gross Margin** - Improving profitability efficiency
9. **Higher Asset Turnover** - More efficient use of assets

### Score Interpretation

- **8-9:** Excellent - Very strong financial health
- **6-7:** Good - Strong financial health
- **4-5:** Fair - Moderate financial health
- **0-3:** Poor - Weak financial health

### Output

Returns JSON with:
- `score` - F-Score (0-9)
- `max_score` - Maximum possible score (9)
- `criteria` - Detailed breakdown of each criterion with pass/fail status and values
- `interpretation` - Text description of financial health level
- `data_available` - Boolean indicating if year-over-year comparison data is available for criteria 5-9

### Implementation Details

- Criteria 1-4 use quarterly financial data (most recent year)
- Criteria 5-9 use annual financial data for year-over-year comparisons
- Compares most recent fiscal year vs previous fiscal year

### Use Cases

Use Piotroski F-Score when:
- Evaluating fundamental financial strength
- Screening for value stocks with improving fundamentals
- Assessing financial health trends
- Comparing financial strength across companies
- Identifying companies with strong fundamentals but undervalued prices

## Dependencies

- `pandas`
- `yfinance`


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
