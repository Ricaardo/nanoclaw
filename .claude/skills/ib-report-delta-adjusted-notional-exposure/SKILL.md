---
name: ib-report-delta-adjusted-notional-exposure
description: Report delta-adjusted notional exposure across all IBKR accounts. Calculates option deltas using Black-Scholes and reports long/short exposure by account and underlying. Use when user asks about delta exposure, portfolio risk, or directional exposure. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# IB Delta-Adjusted Notional Exposure Report

Calculate and report delta-adjusted notional exposure across all Interactive Brokers accounts.

## Prerequisites

User must have TWS or IB Gateway running locally with API enabled:
- Paper trading: port 7497
- Live/Production trading: port 7496

## Instructions

### Step 1: Gather Data

```bash
uv run python scripts/delta_exposure.py [--port PORT]
```

The script returns JSON to stdout with all position deltas and summary data.

### Step 2: Format Report

Read `templates/markdown-template.md` for formatting instructions. Generate a markdown report from the JSON data and save to `sandbox/`.

**Filename**: `delta_exposure_report_{YYYYMMDD}_{HHMMSS}.md`

### Step 3: Report Results

Present the summary table (total long, short, net) and top exposures to the user. Include the saved report path.

## Arguments

- `--port` - IB port (default: 7496 for live trading, use 7497 for paper)

## JSON Output

Returns delta-adjusted notional exposure with:
- `connected` - Boolean
- `accounts` - List of account IDs
- `position_count` - Total positions
- `positions` - Array of positions with symbol, delta, delta_notional, spot price
- `summary` - Totals for long, short, and net delta notional
  - `by_account` - Long/short breakdown by account
  - `by_underlying` - Long/short/net breakdown by symbol

## Methodology

- **Equity Options**: Delta calculated via Black-Scholes with estimated IV based on moneyness
- **Futures**: Delta = 1.0 (full notional exposure)
- **Futures Options**: Delta calculated with lower IV assumption (20%)
- **Stocks**: Delta = 1.0

Delta-adjusted notional = delta x spot price x quantity x multiplier

## Examples

```bash
# Live trading (default port 7496)
uv run python scripts/delta_exposure.py

# Paper trading (port 7497)
uv run python scripts/delta_exposure.py --port 7497
```


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
