---
name: ib-portfolio-action-report
description: Generate a comprehensive portfolio action report with earnings dates and risk assessment. Use when user asks for portfolio review, action items, earnings risk, or position management across IB accounts. Requires TWS or IB Gateway running locally. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# IB Portfolio Action Report

Generate a comprehensive portfolio action report that analyzes all positions across Interactive Brokers accounts, fetches earnings dates, and provides traffic-light risk indicators (🔴🟡🟢) for each position.

## Prerequisites

User must have TWS or IB Gateway running locally with API enabled:
- Paper trading: port 7497
- Live trading: port 7496

## Instructions

### Step 1: Gather Data

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/report.py [--port PORT] [--account ACCOUNT]
```

The script returns JSON to stdout with analyzed portfolio data including risk levels, earnings dates, technical indicators, and spread groupings.

### Step 2: Format Report

Read `templates/markdown-template.md` for formatting instructions. Generate a markdown report from the JSON data and save to `sandbox/`.

**Filename**: `ib_portfolio_action_report_{ACCOUNT}_{YYYY-MM-DD}_{HHmm}.md`

### Step 3: Report Results

Present critical findings to the user: red/yellow items requiring attention, top priority actions, and the saved report path.

## Arguments

- `--port` - IB port (default: 7496 for live trading)
- `--account` - Specific account ID to analyze (optional, defaults to all accounts)

## JSON Output

The script returns structured JSON with:
- `generated` - Timestamp
- `accounts` - List of account IDs
- `summary` - Red/yellow/green counts
- `spreads` - All positions grouped into spreads with risk level, urgency, and recommendations
- `technicals` - Technical indicators per symbol (RSI, trend, SMAs, MACD, ADX)
- `earnings` - Earnings dates per symbol
- `prices` - Current prices per symbol
- `earnings_calendar` - Upcoming earnings with account/position info
- `account_summary` - Position and risk counts per account

## Report Sections

1. **Critical Summary**: Count of positions by risk level (🔴/🟡/🟢)
2. **Immediate Action Required**: Positions expiring within 2 days
3. **Urgent - Expiring Within 1 Week**: Short-term positions needing attention
4. **Critical Earnings Alert**: Positions with earnings this week
5. **Earnings Next Week**: Upcoming earnings exposure
6. **Expiring in 2 Weeks**: Medium-term expirations
7. **Longer-Dated Positions**: Core holdings with spread analysis
8. **Top Priority Actions**: Numbered action items by urgency
9. **Position Size Summary**: Account-level breakdown
10. **Earnings Calendar**: Next 30 days of earnings dates
11. **Technical Analysis Summary**: RSI, trend, SMAs, MACD, ADX for each underlying

## Example Usage

```bash
# All accounts on live trading port
uv run python scripts/report.py --port 7496

# Specific account
uv run python scripts/report.py --port 7496 --account U790497
```

## Dependencies

- `ib-async`
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
