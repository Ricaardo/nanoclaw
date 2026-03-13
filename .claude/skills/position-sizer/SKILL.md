---
name: position-sizer
description: Calculate risk-based position sizes for long stock trades. Use when user asks about position sizing, how many shares to buy, risk per trade, Kelly criterion, ATR-based sizing, or portfolio risk allocation. Supports stop-loss distance calculation, volatility scaling, and sector concentration checks. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Position Sizer

## Overview

Calculate the optimal number of shares to buy for a long stock trade based on risk management principles. Supports three sizing methods:

- **Fixed Fractional**: Risk a fixed percentage of account equity per trade (default: 1%)
- **ATR-Based**: Use Average True Range to set volatility-adjusted stop distances
- **Kelly Criterion**: Calculate mathematically optimal risk allocation from historical win/loss statistics

All methods apply portfolio constraints (max position %, max sector %) and output a final recommended share count with full risk breakdown.

## When to Use

- User asks "how many shares should I buy?"
- User wants to calculate position size for a specific trade setup
- User mentions risk per trade, stop-loss sizing, or portfolio allocation
- User asks about Kelly Criterion or ATR-based position sizing
- User wants to check if a position fits within portfolio concentration limits

## Prerequisites

- No API keys required
- Python 3.9+ with standard library only

## Workflow

### Step 1: Gather Trade Parameters

Collect from the user:
- **Required**: Account size (total equity)
- **Mode A (Fixed Fractional)**: Entry price, stop price, risk percentage (default 1%)
- **Mode B (ATR-Based)**: Entry price, ATR value, ATR multiplier (default 2.0x), risk percentage
- **Mode C (Kelly Criterion)**: Win rate, average win, average loss; optionally entry and stop for share calculation
- **Optional constraints**: Max position % of account, max sector %, current sector exposure

If the user provides a stock ticker but not specific prices, use available tools to look up the current price and suggest entry/stop levels based on technical analysis.

### Step 2: Execute Position Sizer Script

Run the position sizing calculation:

```bash
# Fixed Fractional (most common)
python3 skills/position-sizer/scripts/position_sizer.py \
  --account-size 100000 \
  --entry 155 \
  --stop 148.50 \
  --risk-pct 1.0 \
  --output-dir reports/

# ATR-Based
python3 skills/position-sizer/scripts/position_sizer.py \
  --account-size 100000 \
  --entry 155 \
  --atr 3.20 \
  --atr-multiplier 2.0 \
  --risk-pct 1.0 \
  --output-dir reports/

# Kelly Criterion (budget mode - no entry)
python3 skills/position-sizer/scripts/position_sizer.py \
  --account-size 100000 \
  --win-rate 0.55 \
  --avg-win 2.5 \
  --avg-loss 1.0 \
  --output-dir reports/

# Kelly Criterion (shares mode - with entry/stop)
python3 skills/position-sizer/scripts/position_sizer.py \
  --account-size 100000 \
  --entry 155 \
  --stop 148.50 \
  --win-rate 0.55 \
  --avg-win 2.5 \
  --avg-loss 1.0 \
  --output-dir reports/
```

### Step 3: Load Methodology Reference

Read `references/sizing_methodologies.md` to provide context on the chosen method, risk guidelines, and portfolio constraint best practices.

### Step 4: Calculate Multiple Scenarios

If the user has not specified a single method, run multiple scenarios for comparison:
- Fixed Fractional at 0.5%, 1.0%, and 1.5% risk
- ATR-based at 1.5x, 2.0x, and 3.0x multipliers
- Present a comparison table showing shares, position value, and dollar risk for each

### Step 5: Apply Portfolio Constraints and Determine Final Size

Add constraints if the user has portfolio context:

```bash
python3 skills/position-sizer/scripts/position_sizer.py \
  --account-size 100000 \
  --entry 155 \
  --stop 148.50 \
  --risk-pct 1.0 \
  --max-position-pct 10 \
  --max-sector-pct 30 \
  --current-sector-exposure 22 \
  --output-dir reports/
```

Explain which constraint is binding and why it limits the position.

### Step 6: Generate Position Report

Present the final recommendation including:
- Method used and rationale
- Exact share count and position value
- Dollar risk and percentage of account
- Stop-loss price
- Any binding constraints
- Risk management reminders (portfolio heat, loss-cutting discipline)

## Output Format

### JSON Report

```json
{
  "schema_version": "1.0",
  "mode": "shares",
  "parameters": {
    "entry_price": 155.0,
    "account_size": 100000,
    "stop_price": 148.50,
    "risk_pct": 1.0
  },
  "calculations": {
    "fixed_fractional": {
      "method": "fixed_fractional",
      "shares": 153,
      "risk_per_share": 6.50,
      "dollar_risk": 1000.0,
      "stop_price": 148.50
    },
    "atr_based": null,
    "kelly": null
  },
  "constraints_applied": [],
  "final_recommended_shares": 153,
  "final_position_value": 23715.0,
  "final_risk_dollars": 994.50,
  "final_risk_pct": 0.99,
  "binding_constraint": null
}
```

### Markdown Report

Generated automatically alongside the JSON report. Contains:
- Parameters summary
- Calculation details for the active method
- Constraints analysis (if any)
- Final recommendation with shares, value, and risk

Reports are saved to `reports/` with filenames `position_sizer_YYYY-MM-DD_HHMMSS.json` and `.md`.

## Resources

- `references/sizing_methodologies.md`: Comprehensive guide to Fixed Fractional, ATR-based, and Kelly Criterion methods with examples, comparison table, and risk management principles
- `scripts/position_sizer.py`: Main calculation script (CLI interface)

## Key Principles

1. **Survival first**: Position sizing is about surviving losing streaks, not maximizing winners
2. **The 1% rule**: Default to 1% risk per trade; never exceed 2% without exceptional reason
3. **Round down**: Always round shares down to whole numbers (never round up)
4. **Strictest constraint wins**: When multiple limits apply, the tightest one determines final size
5. **Half Kelly**: Never use full Kelly in practice; half Kelly captures 75% of growth with far less risk
6. **Portfolio heat**: Total open risk should not exceed 6-8% of account equity
7. **Asymmetry of losses**: A 50% loss requires a 100% gain to recover; size accordingly


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
