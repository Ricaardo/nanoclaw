---
name: earnings-trade-analyzer
description: Analyze recent post-earnings stocks using a 5-factor scoring system (Gap Size, Pre-Earnings Trend, Volume Trend, MA200 Position, MA50 Position). Scores each stock 0-100 and assigns A/B/C/D grades. Use when user asks about earnings trade analysis, post-earnings momentum screening, earnings gap scoring, or finding best recent earnings reactions. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Earnings Trade Analyzer - Post-Earnings 5-Factor Scoring

Analyze recent post-earnings stocks using a 5-factor weighted scoring system to identify the strongest earnings reactions for potential momentum trades.

## When to Use

- User asks for post-earnings trade analysis or earnings gap screening
- User wants to find the best recent earnings reactions
- User requests earnings momentum scoring or grading
- User asks about post-earnings accumulation day (PEAD) candidates

## Prerequisites

- FMP API key (set `FMP_API_KEY` environment variable or pass `--api-key`)
- Free tier (250 calls/day) is sufficient for default screening (lookback 2 days, top 20)
- Paid tier recommended for larger lookback windows or full screening

## Workflow

### Step 1: Run the Earnings Trade Analyzer

Execute the analyzer script:

```bash
# Default: last 2 days of earnings, top 20 results
python3 skills/earnings-trade-analyzer/scripts/analyze_earnings_trades.py --output-dir reports/

# Custom lookback and market cap filter
python3 skills/earnings-trade-analyzer/scripts/analyze_earnings_trades.py \
  --lookback-days 5 \
  --min-market-cap 1000000000 \
  --top 30 \
  --output-dir reports/

# With entry quality filter
python3 skills/earnings-trade-analyzer/scripts/analyze_earnings_trades.py \
  --apply-entry-filter \
  --output-dir reports/
```

### Step 2: Review Results

1. Read the generated JSON and Markdown reports
2. Load `references/scoring_methodology.md` for scoring interpretation context
3. Focus on Grade A and B stocks for actionable setups

### Step 3: Present Analysis

For each top candidate, present:
- Composite score and letter grade (A/B/C/D)
- Earnings gap size and direction
- Pre-earnings 20-day trend
- Volume ratio (20-day vs 60-day average)
- Position relative to 200-day and 50-day moving averages
- Weakest and strongest scoring components

### Step 4: Provide Actionable Guidance

Based on grades:
- **Grade A (85+):** Strong earnings reaction with institutional accumulation - consider entry
- **Grade B (70-84):** Good earnings reaction worth monitoring - wait for pullback or confirmation
- **Grade C (55-69):** Mixed signals - use caution, additional analysis needed
- **Grade D (<55):** Weak setup - avoid or wait for better conditions

## Output

- `earnings_trade_analyzer_YYYY-MM-DD_HHMMSS.json` - Structured results with schema_version "1.0"
- `earnings_trade_analyzer_YYYY-MM-DD_HHMMSS.md` - Human-readable report with tables

## Resources

- `references/scoring_methodology.md` - 5-factor scoring system, grade thresholds, and entry quality filter rules


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
