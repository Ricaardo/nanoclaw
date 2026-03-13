---
name: greeks
description: Calculate option Greeks (delta, gamma, theta, vega) and implied volatility for specific options. Use when user asks about Greeks, delta, gamma, theta, vega, IV, or option sensitivity analysis. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Option Greeks

Calculate Greeks for options using Black-Scholes model. Computes IV from market price via Newton-Raphson.

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/greeks.py --spot SPOT --strike STRIKE --type call|put [--expiry YYYY-MM-DD | --dte DTE] [--price PRICE] [--date YYYY-MM-DD] [--vol VOL] [--rate RATE]
```

## Arguments

- `--spot` - Underlying spot price (required)
- `--strike` - Option strike price (required)
- `--type` - Option type: call or put (required)
- `--expiry` - Expiration date YYYY-MM-DD (use this OR --dte)
- `--dte` - Days to expiration (alternative to --expiry)
- `--date` - Calculate as of this date instead of today (YYYY-MM-DD)
- `--price` - Option market price (for IV calculation)
- `--vol` - Override volatility as decimal (e.g., 0.30 for 30%)
- `--rate` - Risk-free rate (default: 0.05)

## Output

Returns JSON with:
- `spot` - Underlying spot price
- `strike` - Strike price
- `days_to_expiry` - Days until expiration
- `iv` - Implied volatility (calculated from market price)
- `greeks` - delta, gamma, theta, vega, rho

## Examples

```bash
# With expiry date and market price (calculates IV)
uv run python scripts/greeks.py --spot 630 --strike 600 --expiry 2026-05-15 --type call --price 72.64

# With DTE directly
uv run python scripts/greeks.py --spot 630 --strike 600 --dte 30 --type call --price 40

# As of a future date
uv run python scripts/greeks.py --spot 630 --strike 600 --expiry 2026-05-15 --date 2026-03-01 --type call --price 50
```

Explain what each Greek means for the position.

## Dependencies

- `scipy`


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
