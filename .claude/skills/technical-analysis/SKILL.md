---
name: technical-analysis
description: Compute technical indicators like RSI, MACD, Bollinger Bands, SMA, EMA for a stock. Use when user asks about technical analysis, indicators, RSI, MACD, moving averages, overbought/oversold, or chart analysis. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Technical Analysis

Compute technical indicators using pandas-ta. Supports multi-symbol analysis and earnings data.

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/technicals.py SYMBOL [--period PERIOD] [--indicators INDICATORS] [--earnings]
```

## Arguments

- `SYMBOL` - Ticker symbol or comma-separated list (e.g., `AAPL` or `AAPL,MSFT,GOOGL`)
- `--period` - Historical period: 1mo, 3mo, 6mo, 1y (default: 3mo)
- `--indicators` - Comma-separated list: rsi,macd,bb,sma,ema,atr,adx (default: all)
- `--earnings` - Include earnings data (upcoming date + history)

## Output

Single symbol returns:
- `price` - Current price and recent change
- `indicators` - Computed values for each indicator
- `risk_metrics` - Volatility (annualized %) and Sharpe ratio
- `signals` - Buy/sell signals based on indicator levels
- `earnings` - Upcoming date and EPS history (if `--earnings`)

Multiple symbols returns:
- `results` - Array of individual symbol results

## Interpretation

- RSI > 70 = overbought, RSI < 30 = oversold
- MACD crossover = momentum shift
- Price near Bollinger Band = potential reversal
- Golden cross (SMA20 > SMA50) = bullish
- ADX > 25 = strong trend
- Sharpe ratio > 1 = good risk-adjusted returns, > 2 = excellent
- Volatility (annualized) = standard deviation of returns scaled to annual basis

## Examples

```bash
# Single symbol with all indicators
uv run python scripts/technicals.py AAPL

# Multiple symbols
uv run python scripts/technicals.py AAPL,MSFT,GOOGL

# With earnings data
uv run python scripts/technicals.py NVDA --earnings

# Specific indicators only
uv run python scripts/technicals.py TSLA --indicators rsi,macd
```

---

# Correlation Analysis

Compute price correlation matrix between multiple symbols for diversification analysis.

## Instructions

```bash
uv run python scripts/correlation.py SYMBOLS [--period PERIOD]
```

## Arguments

- `SYMBOLS` - Comma-separated ticker symbols (minimum 2)
- `--period` - Historical period: 1mo, 3mo, 6mo, 1y (default: 3mo)

## Output

- `symbols` - List of symbols analyzed
- `period` - Time period used
- `correlation_matrix` - Nested dict with correlation values between all pairs

## Interpretation

- Correlation near 1.0 = highly correlated (move together)
- Correlation near -1.0 = negatively correlated (move opposite)
- Correlation near 0 = uncorrelated (independent movement)
- For diversification, prefer low/negative correlations

## Examples

```bash
# Portfolio correlation
uv run python scripts/correlation.py AAPL,MSFT,GOOGL,AMZN

# Sector comparison
uv run python scripts/correlation.py XLF,XLK,XLE,XLV --period 6mo

# Check hedge effectiveness
uv run python scripts/correlation.py SPY,GLD,TLT
```

## Dependencies

- `numpy`
- `pandas`
- `pandas-ta`
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
