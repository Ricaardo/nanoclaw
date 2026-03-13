---
name: earnings-calendar
description: Get upcoming earnings dates with timing (before/after market) and EPS estimates. Use when user asks about earnings dates, earnings calendar, when a company reports, or upcoming earnings. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Earnings Calendar

Retrieve upcoming earnings dates for stocks.

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/earnings.py SYMBOLS
```

## Arguments

- `SYMBOLS` - Ticker symbol or comma-separated list (e.g., `AAPL` or `AAPL,MSFT,GOOGL,NVDA`)

## Output

Single symbol returns:
- `symbol` - Ticker symbol
- `earnings_date` - Next earnings date (YYYY-MM-DD)
- `timing` - "BMO" (Before Market Open), "AMC" (After Market Close), or null
- `eps_estimate` - Consensus EPS estimate, or null if unavailable

Multiple symbols returns:
- `results` - Array of earnings info, sorted by date (soonest first)

## Examples

```bash
# Single symbol
uv run python scripts/earnings.py NVDA

# Multiple symbols (sorted by date)
uv run python scripts/earnings.py AAPL,MSFT,GOOGL,NVDA,META

# Portfolio earnings calendar
uv run python scripts/earnings.py CAT,GOOG,HOOD,IWM,NVDA,PLTR,QQQ,UNH
```

## Use Cases

- Check when positions have upcoming earnings risk
- Plan trades around earnings announcements
- Build an earnings calendar for watchlist

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
