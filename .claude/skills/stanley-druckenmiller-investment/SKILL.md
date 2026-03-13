---
name: stanley-druckenmiller-investment
description: Druckenmiller Strategy Synthesizer - Integrates 8 upstream skill outputs (Market Breadth, Uptrend Analysis, Market Top, Macro Regime, FTD Detector, VCP Screener, Theme Detector, CANSLIM Screener) into a unified conviction score (0-100), pattern classification, and allocation recommendation. Use when user asks about overall market conviction, portfolio positioning, asset allocation, strategy synthesis, or Druckenmiller-style analysis. Triggers on queries like "What is my conviction level?", "How should I position?", "Run the strategy synthesizer", "Druckenmiller analysis", "総合的な市場判断", "確信度スコア", "ポートフォリオ配分", "ドラッケンミラー分析". 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Druckenmiller Strategy Synthesizer

## Purpose

Synthesize outputs from 8 upstream analysis skills (5 required + 3 optional) into a single composite conviction score (0-100), classify the market into one of 4 Druckenmiller patterns, and generate actionable allocation recommendations. This is a **meta-skill** that consumes structured JSON outputs from other skills — it requires no API keys of its own.

## When to Use This Skill

**English:**
- User asks "What's my overall conviction?" or "How should I be positioned?"
- User wants a unified view synthesizing breadth, uptrend, top risk, macro, and FTD signals
- User asks about Druckenmiller-style portfolio positioning
- User requests strategy synthesis after running individual analysis skills
- User asks "Should I increase or decrease exposure?"
- User wants pattern classification (policy pivot, distortion, contrarian, wait)

**Japanese:**
- 「総合的な市場判断は？」「今のポジショニングは？」
- ブレッドス、アップトレンド、天井リスク、マクロの統合判断
- 「エクスポージャーを増やすべき？減らすべき？」
- 「ドラッケンミラー分析を実行して」
- 個別スキル実行後の戦略統合レポート

---

## Input Requirements

### Required Skills (5)

| # | Skill | JSON Prefix | Role |
|---|-------|-------------|------|
| 1 | Market Breadth Analyzer | `market_breadth_` | Market participation breadth |
| 2 | Uptrend Analyzer | `uptrend_analysis_` | Sector uptrend ratios |
| 3 | Market Top Detector | `market_top_` | Distribution / top risk (defense) |
| 4 | Macro Regime Detector | `macro_regime_` | Macro regime transition (1-2Y structure) |
| 5 | FTD Detector | `ftd_detector_` | Bottom confirmation / re-entry (offense) |

### Optional Skills (3)

| # | Skill | JSON Prefix | Role |
|---|-------|-------------|------|
| 6 | VCP Screener | `vcp_screener_` | Momentum stock setups (VCP) |
| 7 | Theme Detector | `theme_detector_` | Theme / sector momentum |
| 8 | CANSLIM Screener | `canslim_screener_` | Growth stock setups + M(Market Direction) |

Run the required skills first. The synthesizer reads their JSON output from `reports/`.

---

## Execution Workflow

### Phase 1: Verify Prerequisites

Check that the 5 required skill JSON reports exist in `reports/` and are recent (< 72 hours). If any are missing, run the corresponding skill first.

### Phase 2: Execute Strategy Synthesizer

```bash
python3 skills/stanley-druckenmiller-investment/scripts/strategy_synthesizer.py \
  --reports-dir reports/ \
  --output-dir reports/ \
  --max-age 72
```

The script will:
1. Load and validate all upstream skill JSON reports
2. Extract normalized signals from each skill
3. Calculate 7 component scores (weighted 0-100)
4. Compute composite conviction score
5. Classify into one of 4 Druckenmiller patterns
6. Generate target allocation and position sizing
7. Output JSON and Markdown reports

### Phase 3: Present Results

Present the generated Markdown report, highlighting:
- Conviction score and zone
- Detected pattern and match strength
- Strongest and weakest components
- Target allocation (equity/bonds/alternatives/cash)
- Position sizing parameters
- Relevant Druckenmiller principle

### Phase 4: Provide Druckenmiller Context

Load appropriate reference documents to provide philosophical context:
- **High conviction:** Emphasize concentration and "fat pitch" principles
- **Low conviction:** Emphasize capital preservation and patience
- **Pattern-specific:** Apply relevant case study from `references/case-studies.md`

---

## 7-Component Scoring System

| # | Component | Weight | Source Skill(s) | Key Signal |
|---|-----------|--------|----------------|------------|
| 1 | Market Structure | **18%** | Breadth + Uptrend | Market participation health |
| 2 | Distribution Risk | **18%** | Market Top (inverted) | Institutional selling risk |
| 3 | Bottom Confirmation | **12%** | FTD Detector | Re-entry signal after correction |
| 4 | Macro Alignment | **18%** | Macro Regime | Regime favorability |
| 5 | Theme Quality | **12%** | Theme Detector | Sector momentum health |
| 6 | Setup Availability | **10%** | VCP + CANSLIM | Quality stock setups |
| 7 | Signal Convergence | **12%** | All 5 required | Cross-skill agreement |

## 4 Pattern Classifications

| Pattern | Trigger Conditions | Druckenmiller Principle |
|---------|-------------------|----------------------|
| Policy Pivot Anticipation | Transitional regime + high transition probability | "Focus on central banks and liquidity" |
| Unsustainable Distortion | Top risk >= 60 + contraction/inflationary regime | "How much you lose when wrong matters most" |
| Extreme Sentiment Contrarian | FTD confirmed + high top risk + bearish breadth | "Most money made in bear markets" |
| Wait & Observe | Low conviction + mixed signals (default) | "When you don't see it, don't swing" |

## Conviction Zone Mapping

| Score | Zone | Exposure | Guidance |
|-------|------|----------|----------|
| 80-100 | Maximum Conviction | 90-100% | Fat pitch - swing hard |
| 60-79 | High Conviction | 70-90% | Standard risk management |
| 40-59 | Moderate Conviction | 50-70% | Reduce position sizes |
| 20-39 | Low Conviction | 20-50% | Preserve capital, minimal risk |
| 0-19 | Capital Preservation | 0-20% | Maximum defense |

---

## Output Files

- `druckenmiller_strategy_YYYY-MM-DD_HHMMSS.json` — Structured analysis data
- `druckenmiller_strategy_YYYY-MM-DD_HHMMSS.md` — Human-readable report

## API Requirements

**None.** This skill reads JSON outputs from other skills. No API keys required.

## Reference Documents

### `references/investment-philosophy.md`
- Core Druckenmiller principles: concentration, capital preservation, 18-month horizon
- Quantitative rules: daily vol targets, max position sizing
- Load when providing philosophical context for conviction assessment

### `references/market-analysis-guide.md`
- Signal-to-action mapping framework
- Macro regime interpretation for allocation decisions
- Load when explaining component scores or allocation rationale

### `references/case-studies.md`
- Historical examples: 1992 GBP, 2000 tech bubble, 2008 crisis
- Pattern classification examples with actual market conditions
- Load when user asks about historical parallels

### `references/conviction_matrix.md`
- Quantitative signal-to-action mapping tables
- Market Top Zone x Macro Regime matrix
- Load when user needs precise exposure numbers for specific signal combinations

### When to Load References
- **First use:** Load `investment-philosophy.md` for framework understanding
- **Allocation questions:** Load `market-analysis-guide.md` + `conviction_matrix.md`
- **Historical context:** Load `case-studies.md`
- **Regular execution:** References not needed — script handles scoring

---

## Relationship to Other Skills

| Skill | Relationship | Time Horizon |
|-------|-------------|-------------|
| Market Breadth Analyzer | Input (required) | Current snapshot |
| Uptrend Analyzer | Input (required) | Current snapshot |
| Market Top Detector | Input (required) | 2-8 weeks tactical |
| Macro Regime Detector | Input (required) | 1-2 years structural |
| FTD Detector | Input (required) | Days-weeks event |
| VCP Screener | Input (optional) | Setup-specific |
| Theme Detector | Input (optional) | Weeks-months thematic |
| CANSLIM Screener | Input (optional) | Setup-specific |
| **This Skill** | **Synthesizer** | **Unified conviction** |


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
