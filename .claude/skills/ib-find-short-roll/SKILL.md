---
name: ib-find-short-roll
description: Find roll options for existing short positions OR find best covered call/put to open against long stock. Use when user asks about rolling shorts, finding roll candidates, writing covered calls, or managing option positions. Requires TWS or IB Gateway running locally. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# IB Find Short Roll

Analyze roll options for short positions or find best short options to open against long stock using real-time data from Interactive Brokers.

## Prerequisites

User must have TWS or IB Gateway running locally with API enabled:
- Paper trading: port 7497
- Live trading: port 7496

## Instructions

### Step 1: Gather Data

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/roll.py SYMBOL [--strike STRIKE] [--expiry YYYYMMDD] [--right C|P] [--port PORT] [--account ACCOUNT]
```

The script returns JSON to stdout with all position and candidate data.

### Step 2: Format Report

Read `templates/markdown-template.md` for formatting instructions. Generate a markdown report from the JSON data and save to `sandbox/`.

### Step 3: Report Results

Present key findings to the user: recommended position, credit/debit, and the saved report path.

## Behavior

1. **If short option position exists** (`mode: "roll"`): Analyzes roll candidates to different expirations/strikes
2. **If long option position exists** (`mode: "spread"`): Finds best short call/put to create a vertical spread
3. **If long stock exists** (`mode: "new_short"`): Finds best covered call (or protective put) to open
4. **If none of the above**: Returns error (use --strike/--expiry to specify manually)

## Arguments

- `SYMBOL` - Ticker symbol (e.g., GOOG, AAPL, TSLA)
- `--strike` - Current short strike price (optional, auto-detects from portfolio)
- `--expiry` - Current short expiration in YYYYMMDD format (optional, auto-detects)
- `--right` - Option type: C for call, P for put (default: C)
- `--port` - IB port (default: 7496 for live trading)
- `--account` - Specific account ID (optional)

## JSON Output

The script outputs JSON with `mode` field indicating the analysis type:

### Common Fields
- `success` - Boolean
- `generated` - Timestamp
- `mode` - "roll", "spread", or "new_short"
- `symbol` - Ticker
- `underlying_price` - Current stock price
- `earnings_date` - Next earnings date or null
- `expirations_analyzed` - List of expiry dates checked

### Mode-specific Fields
- **roll**: `current_position`, `buy_to_close`, `roll_candidates` (dict of expiry -> candidates)
- **spread**: `long_option`, `right`, `candidates_by_expiry`
- **new_short**: `long_position`, `right`, `candidates_by_expiry`

## Example Usage

```bash
# Auto-detect GOOG position (short option, long option, or long stock)
uv run python scripts/roll.py GOOG --port 7496

# Specify exact short position to roll
uv run python scripts/roll.py GOOG --strike 350 --expiry 20260206 --right C

# Find short call to sell against long call (vertical spread)
uv run python scripts/roll.py AUR --right C

# Find covered put for long stock
uv run python scripts/roll.py TSLA --right P
```

## Dependencies

- `ib-async`
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
