---
name: ib-option-chain
description: Get option chain data from Interactive Brokers including calls and puts with strikes, bids, asks, volume, and implied volatility. Use when user asks about options using IBKR data, or needs real-time option quotes from their broker. Requires TWS or IB Gateway running locally. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# IB Option Chain

Fetch option chain data from Interactive Brokers for a specific expiration date.

## Prerequisites

User must have TWS or IB Gateway running locally with API enabled:
- Paper trading: port 7497
- Live trading: port 7496

## Instructions

First, get available expiration dates:
```bash
uv run python scripts/options.py SYMBOL --expiries
```

Then fetch the chain for a specific expiry:
```bash
uv run python scripts/options.py SYMBOL --expiry YYYYMMDD
```

## Arguments

- `SYMBOL` - Ticker symbol (e.g., AAPL, SPY, TSLA)
- `--expiries` - List available expiration dates only
- `--expiry YYYYMMDD` - Fetch chain for specific date (IB format: YYYYMMDD, no dashes)
- `--port` - IB port (default: 7496 for live trading)

## Output

Returns JSON with:
- `calls` - Array of call options with strike, bid, ask, lastPrice, volume, openInterest, impliedVolatility
- `puts` - Array of put options with same fields
- `underlying_price` - Current stock price for reference
- `source` - "ibkr"

Present data as a table. Highlight high volume strikes and notable IV levels.

## Dependencies

- `ib-async`


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
