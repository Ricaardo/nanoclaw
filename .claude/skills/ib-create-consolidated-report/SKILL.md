---
name: ib-create-consolidated-report
description: Consolidate IBRK trade CSV files from a directory into a summary report. Groups trades by symbol, underlying, date, strike, buy/sell, and open/close. Outputs both markdown and CSV. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# IB Create Consolidated Report

Reads all CSV files from a given directory (excluding subdirectories), consolidates trade data by key fields, and generates both markdown and CSV reports.

## Instructions

```bash
uv run python scripts/consolidate.py <directory> [--port PORT] [--output-dir OUTPUT_DIR]
```

## Arguments

- `directory` - Path to directory containing IBRK trade CSV files
- `--port` - IB port to fetch unrealized P&L (7497=paper, 7496=live). If not specified, auto-probes both ports (tries 7496 first, then 7497).
- `--output-dir` - Output directory for reports (default: sandbox/)

## Consolidation Logic

Groups trades by:
- **UnderlyingSymbol** - The underlying ticker (e.g., GOOG, CAT)
- **Symbol** - Full option symbol
- **TradeDate** - Date of the trade
- **Strike** - Strike price
- **Put/Call** - Option type (C or P)
- **Buy/Sell** - Trade direction
- **Open/CloseIndicator** - Whether opening or closing

Aggregates:
- **Quantity** - Sum of quantities
- **Proceeds** - Sum of proceeds
- **NetCash** - Sum of net cash
- **IBCommission** - Sum of commissions
- **FifoPnlRealized** - Sum of realized P&L

Adds column:
- **Position** - SHORT (Sell+Open), LONG (Buy+Open), CLOSE_SHORT (Buy+Close), CLOSE_LONG (Sell+Close)

## Output

Generates two files in the output directory:
- `consolidated_trades_YYYY-MM-DD_HHMM.md` - Markdown report with summary tables
- `consolidated_trades_YYYY-MM-DD_HHMM.csv` - CSV with all consolidated data

## Example Usage

```bash
# Consolidate trades from IBRK reports directory
uv run python scripts/consolidate.py "C:\Users\avrah\OneDrive\Business\Trading\IBRK reports\2stastrading2025"

# Specify custom output directory
uv run python scripts/consolidate.py "C:\path\to\reports" --output-dir "C:\output"
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
