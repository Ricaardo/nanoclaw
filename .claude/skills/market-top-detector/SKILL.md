---
name: market-top-detector
description: Detects market top probability using O'Neil Distribution Days, Minervini Leading Stock Deterioration, and Monty Defensive Sector Rotation. Generates a 0-100 composite score with risk zone classification. Use when user asks about market top risk, distribution days, defensive rotation, leadership breakdown, or whether to reduce equity exposure. Focuses on 2-8 week tactical timing signals for 10-20% corrections. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Market Top Detector Skill

## Purpose

Detect the probability of a market top formation using a quantitative 6-component scoring system (0-100). Integrates three proven market top detection methodologies:

1. **O'Neil** - Distribution Day accumulation (institutional selling)
2. **Minervini** - Leading stock deterioration pattern
3. **Monty** - Defensive sector rotation signal

Unlike the Bubble Detector (macro/multi-month evaluation), this skill focuses on **tactical 2-8 week timing signals** that precede 10-20% market corrections.

## When to Use This Skill

**English:**
- User asks "Is the market topping?" or "Are we near a top?"
- User notices distribution days accumulating
- User observes defensive sectors outperforming growth
- User sees leading stocks breaking down while indices hold
- User asks about reducing equity exposure timing
- User wants to assess correction probability for the next 2-8 weeks

**Japanese:**
- 「天井が近い？」「今は利確すべき？」
- ディストリビューションデーの蓄積を懸念
- ディフェンシブセクターがグロースをアウトパフォーム
- 先導株が崩れ始めているが指数はまだ持ちこたえている
- エクスポージャー縮小のタイミング判断
- 今後2〜8週間の調整確率を評価したい

## Difference from Bubble Detector

| Aspect | Market Top Detector | Bubble Detector |
|--------|-------------------|-----------------|
| Timeframe | 2-8 weeks | Months to years |
| Target | 10-20% correction | Bubble collapse (30%+) |
| Methodology | O'Neil/Minervini/Monty | Minsky/Kindleberger |
| Data | Price/Volume + Breadth | Valuation + Sentiment + Social |
| Score Range | 0-100 composite | 0-15 points |

---

## Execution Workflow

### Phase 1: Data Collection via WebSearch

Before running the Python script, collect the following data using WebSearch.
**Data Freshness Requirement:** All data must be from the most recent 3 business days. Stale data degrades analysis quality.

```
1. S&P 500 Breadth (200DMA above %)
   AUTO-FETCHED from TraderMonty CSV (no WebSearch needed)
   The script fetches this automatically from GitHub Pages CSV data.
   Override: --breadth-200dma [VALUE] to use a manual value instead.
   Disable: --no-auto-breadth to skip auto-fetch entirely.

2. [REQUIRED] S&P 500 Breadth (50DMA above %)
   Valid range: 20-100
   Primary search: "S&P 500 percent stocks above 50 day moving average"
   Fallback: "market breadth 50dma site:barchart.com"
   Record the data date

3. [REQUIRED] CBOE Equity Put/Call Ratio
   Valid range: 0.30-1.50
   Primary search: "CBOE equity put call ratio today"
   Fallback: "CBOE total put call ratio current"
   Fallback: "put call ratio site:cboe.com"
   Record the data date

4. [OPTIONAL] VIX Term Structure
   Values: steep_contango / contango / flat / backwardation
   Primary search: "VIX VIX3M ratio term structure today"
   Fallback: "VIX futures term structure contango backwardation"
   Note: Auto-detected from FMP API if VIX3M quote available.
   CLI --vix-term overrides auto-detection.

5. [OPTIONAL] Margin Debt YoY %
   Primary search: "FINRA margin debt latest year over year percent"
   Fallback: "NYSE margin debt monthly"
   Note: Typically 1-2 months lagged. Record the reporting month.
```

### Phase 2: Execute Python Script

Run the script with collected data as CLI arguments:

```bash
python3 skills/market-top-detector/scripts/market_top_detector.py \
  --api-key $FMP_API_KEY \
  --breadth-50dma [VALUE] --breadth-50dma-date [YYYY-MM-DD] \
  --put-call [VALUE] --put-call-date [YYYY-MM-DD] \
  --vix-term [steep_contango|contango|flat|backwardation] \
  --margin-debt-yoy [VALUE] --margin-debt-date [YYYY-MM-DD] \
  --output-dir reports/ \
  --context "Consumer Confidence=[VALUE]" "Gold Price=[VALUE]"
# 200DMA breadth is auto-fetched from TraderMonty CSV.
# Override with --breadth-200dma [VALUE] if needed.
# Disable with --no-auto-breadth to skip auto-fetch.
```

The script will:
1. Fetch S&P 500, QQQ, VIX quotes and history from FMP API
2. Fetch Leading ETF (ARKK, WCLD, IGV, XBI, SOXX, SMH, KWEB, TAN) data
3. Fetch Sector ETF (XLU, XLP, XLV, VNQ, XLK, XLC, XLY) data
4. Calculate all 6 components
5. Generate composite score and reports

### Phase 3: Present Results

Present the generated Markdown report to the user, highlighting:
- Composite score and risk zone
- Data freshness warnings (if any data older than 3 days)
- Strongest warning signal (highest component score)
- Historical comparison (closest past top pattern)
- What-if scenarios (sensitivity to key changes)
- Recommended actions based on risk zone
- Follow-Through Day status (if applicable)
- Delta vs previous run (if prior report exists)

---

## 6-Component Scoring System

| # | Component | Weight | Data Source | Key Signal |
|---|-----------|--------|-------------|------------|
| 1 | Distribution Day Count | **25%** | FMP API | Institutional selling in last 25 trading days |
| 2 | Leading Stock Health | **20%** | FMP API | Growth ETF basket deterioration |
| 3 | Defensive Sector Rotation | **15%** | FMP API | Defensive vs Growth relative performance |
| 4 | Market Breadth Divergence | **15%** | Auto (CSV) + WebSearch | 200DMA (auto) / 50DMA (WebSearch) breadth vs index level |
| 5 | Index Technical Condition | **15%** | FMP API | MA structure, failed rallies, lower highs |
| 6 | Sentiment & Speculation | **10%** | FMP + WebSearch | VIX, Put/Call, term structure |

## Risk Zone Mapping

| Score | Zone | Risk Budget | Action |
|-------|------|-------------|--------|
| 0-20 | Green (Normal) | 100% | Normal operations |
| 21-40 | Yellow (Early Warning) | 80-90% | Tighten stops, reduce new entries |
| 41-60 | Orange (Elevated Risk) | 60-75% | Profit-taking on weak positions |
| 61-80 | Red (High Probability Top) | 40-55% | Aggressive profit-taking |
| 81-100 | Critical (Top Formation) | 20-35% | Maximum defense, hedging |

---

## API Requirements

**Required:** FMP API key (free tier sufficient: ~33 calls per execution)
**Optional:** WebSearch data for breadth and sentiment (improves accuracy)

## Output Files

- JSON: `market_top_YYYY-MM-DD_HHMMSS.json`
- Markdown: `market_top_YYYY-MM-DD_HHMMSS.md`

## Reference Documents

### `references/market_top_methodology.md`
- Full methodology with O'Neil, Minervini, and Monty frameworks
- Component scoring details and thresholds
- Historical validation notes

### `references/distribution_day_guide.md`
- Detailed O'Neil Distribution Day rules
- Stalling day identification
- Follow-Through Day (FTD) mechanics

### `references/historical_tops.md`
- Analysis of 2000, 2007, 2018, 2022 market tops
- Component score patterns during historical tops
- Lessons learned and calibration data

### When to Load References
- **First use:** Load `market_top_methodology.md` for full framework understanding
- **Distribution day questions:** Load `distribution_day_guide.md`
- **Historical context:** Load `historical_tops.md`
- **Regular execution:** References not needed - script handles scoring


### 加密市场信号组件
当用户关注加密市场时，可扩展以下信号：
- BTC 主导率变化（BTC Dominance）
- 稳定币市值变化（USDT/USDC 供应量）
- 加密恐惧贪婪指数
- DeFi TVL 变化趋势

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
