---
name: market-breadth
description: Unified market breadth diagnosis combining S&P 500 breadth index analysis (6 components) and uptrend ratio sector analysis (5 components). Three modes: --mode breadth (200MA-based breadth index), --mode sector (uptrend ratio sector participation + rotation), --mode full (combined, default). Generates 0-100 composite scores. No API key required. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Market Breadth Skill

## Purpose

Unified market breadth diagnosis combining two complementary data sources:

1. **Breadth Mode** — S&P 500 Breadth Index (200-Day MA based), 6-component scoring from TraderMonty's breadth CSV
2. **Sector Mode** — Uptrend Ratio Dashboard (~2,800 stocks, 11 sectors), 5-component scoring from Monty's uptrend CSV
3. **Full Mode** (default) — Runs both analyses and presents a combined view

**Score direction:** 100 = Maximum health (broad participation), 0 = Critical weakness.

**No API key required** — uses freely available CSV data from GitHub Pages.

## When to Use This Skill

- User asks "Is the market rally broad-based?" or "How healthy is market breadth?"
- User wants to assess market participation rate or advance-decline health
- User asks about uptrend ratios, sector participation, or sector rotation
- User wants exposure guidance based on breadth conditions
- User asks whether the market is narrowing (fewer stocks participating)
- 「市場のブレッドスは健全？」「上昇の裾野は広い？」

## Prerequisites

- **Python 3.8+** with `requests` library
- **Internet access** to reach GitHub Pages URLs
- **No API keys required**

## Difference from Related Skills

| Aspect | Market Breadth | Breadth Chart Analyst | Market Top Detector |
|--------|---------------|----------------------|-------------------|
| Data Source | CSV (automated) | Chart images (manual) | FMP API (paid) |
| API Required | None | None | FMP key |
| Output | Quantitative 0-100 | Qualitative analysis | Risk score 0-100 |
| Score Direction | Higher = healthier | N/A | Higher = riskier |

---

## Execution Workflow

### Mode Selection

| Mode | Flag | What It Runs |
|------|------|-------------|
| **full** (default) | `--mode full` | Both breadth + sector analyses |
| **breadth** | `--mode breadth` | S&P 500 Breadth Index only (6 components) |
| **sector** | `--mode sector` | Uptrend Ratio sector analysis only (5 components) |

### Phase 1: Execute Scripts

**Breadth mode** (S&P 500 Breadth Index, 6 components):
```bash
python3 skills/market-breadth/scripts/market_breadth_analyzer.py \
  --detail-url "https://tradermonty.github.io/market-breadth-analysis/market_breadth_data.csv" \
  --summary-url "https://tradermonty.github.io/market-breadth-analysis/market_breadth_summary.csv"
```

**Sector mode** (Uptrend Ratio Dashboard, 5 components):
```bash
python3 skills/market-breadth/scripts/uptrend_analyzer.py
```

**Full mode** (default): Run both scripts above, then combine results.

### Phase 2: Present Results

Present the generated Markdown report(s) to the user, highlighting:
- Composite score(s) and health zone(s)
- Exposure guidance (equity allocation recommendation)
- Strongest and weakest components
- Sector heatmap (sector mode / full mode)
- Key breadth levels to watch (breadth mode / full mode)
- Any data freshness or confidence warnings

---

## Breadth Mode — 6-Component Scoring System

Uses TraderMonty's breadth dataset (S&P 500 stocks above 200DMA).

| # | Component | Weight | Key Signal |
|---|-----------|--------|------------|
| 1 | Breadth Level & Trend | **25%** | Current 8MA level + 200MA trend + 8MA direction modifier |
| 2 | 8MA vs 200MA Crossover | **20%** | Momentum via MA gap and direction |
| 3 | Peak/Trough Cycle | **20%** | Position in breadth cycle |
| 4 | Bearish Signal | **15%** | Backtested bearish signal flag + Pink Zone |
| 5 | Historical Percentile | **10%** | Current vs full history distribution |
| 6 | S&P 500 Divergence | **10%** | Multi-window (20d + 60d) price vs breadth divergence |

**Weight Redistribution:** If any component lacks data, its weight is proportionally redistributed.

**Score History:** Composite scores are persisted across runs in `market_breadth_history.json` (max 20 entries, trend detection).

### Health Zone Mapping

| Score | Zone | Equity Exposure | Action |
|-------|------|-----------------|--------|
| 80-100 | Strong | 90-100% | Full position, growth/momentum favored |
| 60-79 | Healthy | 75-90% | Normal operations |
| 40-59 | Neutral | 60-75% | Selective positioning, tighten stops |
| 20-39 | Weakening | 40-60% | Profit-taking, raise cash |
| 0-19 | Critical | 25-40% | Capital preservation, watch for trough |

### Breadth Data Sources

- **Detail CSV:** `market_breadth_data.csv` (~2,500 rows, 2016-present)
  - Columns: Date, S&P500_Price, Breadth_Index_Raw/200MA/8MA, Trend, Bearish_Signal, Peak/Trough flags
- **Summary CSV:** `market_breadth_summary.csv` (8 aggregate metrics)
- **Live Dashboard:** https://tradermonty.github.io/market-breadth-analysis/

---

## Sector Mode — 5-Component Scoring System

Uses Monty's Uptrend Ratio Dashboard (~2,800 US stocks, 11 GICS sectors).

| # | Component | Weight | Key Signal |
|---|-----------|--------|------------|
| 1 | Market Breadth (Overall) | **30%** | Uptrend ratio level + trend direction |
| 2 | Sector Participation | **25%** | Uptrend sector count + ratio spread |
| 3 | Sector Rotation | **15%** | Cyclical vs Defensive balance |
| 4 | Momentum | **20%** | EMA(3)-smoothed slope + acceleration (10v10) |
| 5 | Historical Context | **10%** | Percentile rank in history + confidence |

### Scoring Zones (7-Level Detail)

| Score | Zone | Zone Detail | Exposure |
|-------|------|-------------|----------|
| 80-100 | Strong Bull | Strong Bull | Full (100%) |
| 70-79 | Bull | Bull-Upper | Normal (90-100%) |
| 60-69 | Bull | Bull-Lower | Normal (80-90%) |
| 40-59 | Neutral | Neutral | Reduced (60-80%) |
| 30-39 | Cautious | Cautious-Upper | Defensive (45-60%) |
| 20-29 | Cautious | Cautious-Lower | Defensive (30-45%) |
| 0-19 | Bear | Bear | Preservation (0-30%) |

### Warning System

| Warning | Condition | Penalty |
|---------|-----------|---------|
| **Late Cycle** | Commodity avg > both Cyclical and Defensive | -5 |
| **High Spread** | Max-min sector ratio spread > 40pp | -3 |
| **Divergence** | Intra-group std > 8pp, spread > 20pp, or trend dissenters | -3 |

Penalties stack (max -10) + multi-warning discount (+1 when >= 2 active).

### Sector Data Sources

- **Timeseries CSV:** `uptrend_ratio_timeseries.csv` (all + 11 sectors, 2023/08~present)
- **Sector Summary:** `sector_summary.csv` (latest snapshot)
- **Thresholds:** Overbought = 37%, Oversold = 9.7%
- **Live Dashboard:** https://uptrend-dashboard.streamlit.app/

---

## Output Files

**Breadth mode:**
- `market_breadth_YYYY-MM-DD_HHMMSS.json` / `.md`
- `market_breadth_history.json` (rolling history)

**Sector mode:**
- `uptrend_analysis_YYYY-MM-DD_HHMMSS.json` / `.md`

---

## Resources

### Scripts (no modification needed)

**Breadth analysis (`scripts/`):**
- `market_breadth_analyzer.py` — Main orchestrator (6 components)
- `csv_client.py` — Detail/Summary CSV fetcher
- `scorer.py` — Composite scoring engine (weight redistribution)
- `history_tracker.py` — Score persistence and trend detection
- `report_generator.py` — JSON + Markdown report output
- `calculators/` — trend_level, ma_crossover, cycle, bearish_signal, historical_context, divergence

**Sector analysis (`scripts/`):**
- `uptrend_analyzer.py` — Main orchestrator (5 components)
- `data_fetcher.py` — Uptrend CSV fetcher + sector name mapping
- `uptrend_scorer.py` — Composite scoring + warning system + zone proximity
- `uptrend_report_generator.py` — JSON + Markdown report output
- `calculators/` — market_breadth, sector_participation, sector_rotation, momentum, uptrend_historical_context

### Reference Documents

- `references/breadth_analysis_methodology.md` — 6-component scoring details, thresholds, Pink Zone, divergence windows
- `references/uptrend_methodology.md` — Uptrend ratio definition, sector classification, 5-component scoring, warning system

### When to Load References
- **First use:** Load both methodology references for framework understanding
- **Regular execution:** References not needed — scripts handle scoring

---

## Cross-Referencing with Other Skills

- **Market Top Detector:** Breadth Weakening + Top Detector Orange/Red = strong topping confirmation
- **CANSLIM Screener:** Strong/Healthy breadth zones improve CANSLIM success rates
- **Sector Analyst:** Weakening breadth often coincides with offensive-to-defensive rotation
- **Technical Analyst:** For index-level chart confirmation

## Limitations

1. **Lagging indicators:** Breadth data reflects what has happened, not predictions
2. **US only:** S&P 500 (breadth) and ~2,800 US stocks (sector); no international coverage
3. **No volume data:** Both datasets are price-based only
4. **CSV update frequency:** Depends on TraderMonty's update schedule; check freshness
5. **Limited sector history:** Sector data starts Jul 2024 (~370+ points per sector)

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
