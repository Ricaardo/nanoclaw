---
name: risk-assessment
description: Assess risk metrics for a stock or position including volatility, beta, VaR, and drawdown analysis. Use when user asks about risk, volatility, beta, VaR, value at risk, drawdown, or position sizing. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Risk Assessment

Calculate risk metrics for stocks and positions.

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/risk.py SYMBOL [--period PERIOD] [--position-size SIZE]
```

## Arguments

- `SYMBOL` - Ticker symbol
- `--period` - Analysis period: 1mo, 3mo, 6mo, 1y (default: 1y)
- `--position-size` - Dollar amount for position-specific metrics (optional)

## Output

Returns JSON with:
- `volatility` - Historical volatility (annualized)
- `beta` - Beta vs SPY
- `var_95` - 95% Value at Risk (daily)
- `var_99` - 99% Value at Risk (daily)
- `max_drawdown` - Maximum drawdown in period
- `sharpe_ratio` - Risk-adjusted return
- `position_risk` - If position-size provided, dollar VaR

Explain what the risk metrics mean and suggest position sizing if relevant.

## Dependencies

- `numpy`
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
