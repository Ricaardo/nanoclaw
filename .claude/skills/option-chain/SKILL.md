---
name: option-chain
description: Get option chain data including calls and puts with strikes, bids, asks, volume, open interest, and implied volatility. Use when user asks about options, option prices, calls, puts, or option chain for a specific expiration date. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Option Chain

Fetch option chain data from Yahoo Finance for a specific expiration date.

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

First, get available expiration dates:
```bash
uv run python scripts/options.py SYMBOL --expiries
```

Then fetch the chain for a specific expiry:
```bash
uv run python scripts/options.py SYMBOL --expiry YYYY-MM-DD
```

## Arguments

- `SYMBOL` - Ticker symbol (e.g., AAPL, SPY, TSLA)
- `--expiries` - List available expiration dates only
- `--expiry YYYY-MM-DD` - Fetch chain for specific date

## Output

Returns JSON with:
- `calls` - Array of call options with strike, bid, ask, volume, openInterest, impliedVolatility
- `puts` - Array of put options with same fields
- `underlying_price` - Current stock price for reference

Present data as a table. Highlight high volume/OI strikes and notable IV levels.

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
