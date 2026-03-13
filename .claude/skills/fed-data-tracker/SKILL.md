---
name: fed-data-tracker
description: "Tracks Federal Reserve key data including interest rates, balance sheet, TGA/RRP, inflation, employment and dollar index. Pure data dashboard with no scoring. Use when user asks about Fed data, interest rates, Fed balance sheet, QT progress, inflation data, or employment situation. 当用户用中文询问美联储数据、利率、资产负债表、QT进展、通胀数据、就业数据时触发。"
---

# Fed Data Tracker Skill

## Purpose

Pure data dashboard that displays Federal Reserve key metrics in a single view. No scoring — just organized, up-to-date data across 6 panels.

**API key required:** FRED (free tier: 120 req/min).

## When to Use This Skill

**English:**
- User asks "What are current interest rates?" or "What's the Fed balance sheet?"
- User wants QT progress, TGA/RRP levels, or inflation data
- User asks about employment situation or dollar index
- User wants a comprehensive Fed data snapshot

**中文:**
- 「当前利率是多少？」「美联储资产负债表？」
- 「QT 进展如何？」「TGA/RRP 余额？」
- 「最新通胀数据？」「就业情况如何？」

## Prerequisites

- **Python 3.8+** with `requests` library
- **FRED API key** (free) — set via `--api-key` or `FRED_API_KEY` env var
- Optional: `yfinance` for dollar index fallback

---

## Execution Workflow

### Phase 1: Execute Python Script

```bash
python3 skills/fed-data-tracker/scripts/fed_data_tracker.py --api-key "$FRED_API_KEY" --lang zh
```

Optional: `--sections rates|balance_sheet|reserves|inflation|employment|dollar|all` `--output-dir ./reports`

### Phase 2: Present Results

Present the 6 data panels to the user with latest values and changes.

---

## 6 Data Panels

| # | Panel | FRED Series | Output |
|---|-------|-------------|--------|
| 1 | Interest Rates | FEDFUNDS, DFF, SOFR, GS2/5/10/30, DGS1MO/3MO | Current + week/month/quarter changes + 2s10s/3m10y spreads |
| 2 | Balance Sheet | WALCL, TREAST, WSHOMCB | Total assets/Treasuries/MBS (trillions) + QT pace |
| 3 | TGA & RRP | WTREGEN, RRPONTSYD | Balances + week/month changes |
| 4 | Inflation | CPIAUCSL, CPILFESL, PCEPI, PCEPILFE | YoY%/MoM%/3-month annualized vs 2% target |
| 5 | Employment | UNRATE, PAYEMS, ICSA | Unemployment rate/NFP change/Initial claims 4-week avg |
| 6 | Dollar | DTWEXBGS (yfinance UUP fallback) | Level + 30d/90d change + 2-year percentile |

~15-20 FRED API calls per run.

## Output Files

- JSON: `fed_data_YYYY-MM-DD_HHMMSS.json`
- Markdown: `fed_data_YYYY-MM-DD_HHMMSS.md`

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
