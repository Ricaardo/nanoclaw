---
name: scanner-pmcc
description: Scan stocks for Poor Man's Covered Call (PMCC) suitability. Analyzes LEAPS and short call options for delta, liquidity, spread, IV, and yield. Use when user asks about PMCC candidates, diagonal spreads, or LEAPS strategies. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# PMCC Scanner

Finds optimal Poor Man's Covered Call setups by scoring symbols on option chain quality, liquidity, implied volatility, and projected yield.

## What is PMCC?

**Poor Man's Covered Call (PMCC)** is a diagonal call spread that replicates a traditional covered call at a fraction of the capital cost.

### Structure

| Leg | Position | Typical Selection | Purpose |
|-----|----------|-------------------|---------|
| **Long Leg** | Buy deep ITM LEAPS call | Delta ~0.80, 9-18 months out | Synthetic stock replacement |
| **Short Leg** | Sell OTM near-term call | Delta ~0.20, 30-45 DTE | Income generation |

### Why Delta ~0.80 for the LEAPS?

A deep ITM LEAPS with delta ~0.80 behaves like owning ~80 shares of stock, but costs significantly less than buying 100 shares outright. Key reasons:

- **High directional exposure**: Captures ~80% of stock moves, making the position responsive to bullish moves
- **High extrinsic value retention**: Deep ITM options have mostly intrinsic value, so theta decay is slow
- **Lower capital requirement**: Typically 30-50% of the cost of 100 shares, freeing capital for other positions
- **Margin of safety**: Even if the stock drops modestly, the LEAPS retains significant intrinsic value

A delta of 0.70 is the minimum viable threshold; below that, the LEAPS loses too much value on pullbacks and behaves more like a speculative call.

### Why Delta ~0.20 for the Short Call?

The short OTM call generates recurring income against the LEAPS position:

- **Low assignment risk**: At delta 0.20, there is roughly a 20% probability of finishing ITM — most expire worthless
- **Reasonable premium**: High enough delta to collect meaningful premium (unlike delta 0.05 "lottery tickets")
- **Room for upside**: The stock can appreciate toward the short strike before you need to manage the position
- **Easy rolling**: If tested, roll up and out for a credit or small debit

### PMCC vs Traditional Covered Call

| Factor | Traditional Covered Call | PMCC |
|--------|--------------------------|------|
| Capital required | Full stock purchase (~$15,000 for $150 stock) | LEAPS cost (~$4,000-6,000) |
| Max profit | Strike - stock cost + premium | Short strike - LEAPS strike - net debit |
| Max loss | Stock goes to zero - premium | Net debit paid (LEAPS cost - short premium received) |
| Yield on capital | Lower (larger denominator) | Higher (smaller capital base) |
| Downside risk | Full stock risk minus premium | Limited to net debit |
| Complexity | Simple | Moderate (two expirations to manage) |

### Break-Even Analysis

The break-even at the LEAPS expiration is:

```
Break-even = LEAPS strike + net debit paid
```

Where `net debit = LEAPS cost - total short premium collected over the life of the position`. Each short call sold reduces the effective cost basis, moving break-even lower over time.

## When to Use This Skill

Use this skill when:
- User asks for PMCC candidates ("Which stocks are good for PMCC?")
- User wants to scan a watchlist for diagonal spread setups
- User asks about LEAPS strategies or capital-efficient income generation
- User wants to pipe bullish scanner output into options analysis
- User asks to compare PMCC suitability across multiple tickers

Example requests:
- "Scan AAPL, MSFT, GOOGL for PMCC setups"
- "Find the best PMCC candidates from my bullish scanner results"
- "Which of these stocks has the best LEAPS liquidity for PMCC?"
- "Run PMCC scan with delta 0.70 LEAPS and 0.15 short"

## Instructions

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/scan.py SYMBOLS [options]
```

## Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `SYMBOLS` | Comma-separated tickers or path to JSON file from bullish scanner | (required) |
| `--min-leaps-days` | Minimum LEAPS expiration in days | 270 (9 months) |
| `--leaps-delta` | Target LEAPS delta | 0.80 |
| `--short-delta` | Target short call delta | 0.20 |
| `--output` | Save results to JSON file | (none) |

## Scoring System (max ~11 points)

| Category | Condition | Points |
|----------|-----------|--------|
| **Delta Accuracy** | LEAPS within ±0.05 of target | +2 |
| | LEAPS within ±0.10 of target | +1 |
| | Short within ±0.05 of target | +1 |
| | Short within ±0.10 of target | +0.5 |
| **Liquidity** | LEAPS vol+OI > 100 | +1 |
| | LEAPS vol+OI > 20 | +0.5 |
| | Short vol+OI > 500 | +1 |
| | Short vol+OI > 100 | +0.5 |
| **Spread** | LEAPS bid-ask spread < 5% | +1 |
| | LEAPS bid-ask spread < 10% | +0.5 |
| | Short bid-ask spread < 10% | +1 |
| | Short bid-ask spread < 20% | +0.5 |
| **IV Level** | 25-50% (ideal sweet spot) | +2 |
| | 20-60% (acceptable range) | +1 |
| **Yield** | Annualized > 50% | +2 |
| | Annualized > 30% | +1 |

### Score Interpretation

| Score | Rating | Recommendation |
|-------|--------|----------------|
| > 9 | Excellent | Strong candidate — good structure, liquidity, and yield |
| 7–9 | Good | Solid candidate — minor weaknesses in one category |
| 5–7 | Acceptable | Usable with caveats — check liquidity and spreads carefully |
| < 5 | Poor | Avoid — likely illiquid options or unfavorable IV environment |

## IV Rank / Percentile Context

Implied Volatility level is critical for PMCC profitability because it affects both legs differently.

### Why Moderate IV (25-50%) Scores Highest

The PMCC requires balancing two opposing IV effects:

| IV Environment | LEAPS (Long Leg) | Short Call (Short Leg) | Net Effect |
|----------------|-------------------|------------------------|------------|
| **Low IV (<20%)** | Cheap — good entry | Low premium — poor income | Bad: income too low to justify the position |
| **Moderate IV (25-50%)** | Reasonable cost | Decent premium | Ideal: balanced cost vs income |
| **High IV (>50%)** | Expensive — high cost basis | Rich premium — great income | Mixed: high income but high net debit |
| **Very High IV (>70%)** | Very expensive | Very rich premium | Risky: potential IV crush on both legs |

### IV Rank Interpretation Table

| IV Rank | Meaning | PMCC Implication |
|---------|---------|------------------|
| 0-20% | IV near 52-week lows | Poor short premium; wait for IV expansion |
| 20-40% | Below average IV | Acceptable; LEAPS are cheap but short premium modest |
| 40-60% | Average IV | Sweet spot for new PMCC entries |
| 60-80% | Above average IV | Good short premium but LEAPS expensive; consider if short premium offsets |
| 80-100% | IV near 52-week highs | Caution: IV crush risk; only enter if you have a strong directional view |

**Practical tip**: Enter new PMCC positions when IV Rank is 30-60%. If IV Rank is above 70%, consider selling the short call first (if already holding LEAPS) to capture elevated premium.

## Greeks Sensitivity

Understanding how Greeks affect each leg is essential for managing PMCC positions over time.

### Theta (Time Decay)

| Leg | Theta Effect | Implication |
|-----|-------------|-------------|
| **Long LEAPS** | Slow decay (long-dated, deep ITM) | Minimal daily cost; accelerates only in final 60-90 days |
| **Short Call** | Fast decay (near-term, 30-45 DTE) | This is where you earn income; theta works in your favor |
| **Net Position** | Positive theta (short decays faster) | Net income from time passage — the core profit mechanism |

**Key insight**: The PMCC is a net positive theta strategy. The short call decays 3-5x faster than the LEAPS in typical setups.

### Vega (Volatility Sensitivity)

| Leg | Vega Effect | Implication |
|-----|-------------|-------------|
| **Long LEAPS** | High positive vega (long-dated) | Benefits from IV expansion |
| **Short Call** | Lower negative vega (short-dated) | Hurt by IV expansion, but smaller magnitude |
| **Net Position** | Net long vega | PMCC benefits from rising IV; hurt by IV crush |

**Practical impact**: After entering a PMCC, an IV expansion increases the LEAPS value more than the short call, creating a paper profit. An IV crush does the opposite.

### Delta Management: When to Roll the Short Call

Roll or close the short call when:
- **Stock approaches short strike** (delta rises above 0.40-0.50): Roll up and out for a credit
- **Short call reaches 70-80% of max profit**: Close early, sell a new one at higher strike or next expiry
- **Short call has <7 DTE**: Close to avoid gamma risk and pin risk near expiration
- **IV spikes**: Consider rolling to a higher strike to capture elevated premium

### Gamma Risk

| Leg | Gamma | Risk Level |
|-----|-------|------------|
| **Long LEAPS** | Very low (long-dated) | Minimal; delta changes slowly |
| **Short Call** | Higher (near expiration) | Increasing as expiry approaches |
| **Net Position** | Slightly negative gamma near short expiry | Manage by rolling before final week |

**Warning**: In the final 5 trading days before short call expiration, gamma accelerates rapidly. A stock moving through the short strike can cause large P/L swings. Always have a plan to roll or close before expiration week.

## Yield Calculation Example

### Step-by-Step: AAPL at $185

**1. Buy LEAPS Call (January 2027, 12 months out)**
- Strike: $150 (deep ITM, delta ~0.82)
- Cost: $42.00 per share ($4,200 per contract)
- Intrinsic value: $185 - $150 = $35.00
- Extrinsic (time) value: $42.00 - $35.00 = $7.00

**2. Sell Short Call (45 DTE)**
- Strike: $195 (OTM, delta ~0.18)
- Premium received: $2.50 per share ($250 per contract)

**3. Calculate Net Debit**
```
Net debit = LEAPS cost - short premium
         = $42.00 - $2.50
         = $39.50 per share ($3,950 per contract)
```

**4. Monthly Yield**
```
Monthly yield = short premium / net debit × 100
              = $2.50 / $39.50 × 100
              = 6.33% per month
```

**5. Annualized Yield (if repeated monthly)**
```
Annualized yield = monthly yield × 12
                 = 6.33% × 12
                 = 75.9% annualized
```

> **Important**: Annualized yield assumes you can sell ~12 short calls over the LEAPS lifetime at similar premiums. Actual yield will vary with IV changes, stock movement, and rolling adjustments. A realistic expectation is 60-70% of the theoretical annualized yield.

**6. Max Profit on This Setup**
```
Max profit = (short strike - LEAPS strike) - net debit
           = ($195 - $150) - $39.50
           = $45.00 - $39.50
           = $5.50 per share ($550 per contract)
```

**7. Break-Even at LEAPS Expiration**
```
Break-even = LEAPS strike + net debit
           = $150 + $39.50
           = $189.50
```

## Output

Returns JSON with:
- `criteria` — Scan parameters used (delta targets, min days, etc.)
- `results` — Array sorted by score descending:
  - `symbol`, `price`, `iv_pct`, `pmcc_score`
  - `leaps` — expiry, strike, delta, bid/ask, spread%, volume, OI
  - `short` — expiry, strike, delta, bid/ask, spread%, volume, OI
  - `metrics` — net_debit, short_yield%, annual_yield%, capital_required
- `errors` — Symbols that failed (no options, insufficient data)

## Examples

```bash
# Scan specific symbols
uv run python scripts/scan.py AAPL,MSFT,GOOGL,NVDA

# Use output from bullish scanner
uv run python scripts/scan.py bullish_results.json

# Custom delta targets (more conservative LEAPS, tighter short)
uv run python scripts/scan.py AAPL,MSFT --leaps-delta 0.70 --short-delta 0.15

# Longer LEAPS (1 year minimum)
uv run python scripts/scan.py AAPL,MSFT --min-leaps-days 365

# Save results for further analysis
uv run python scripts/scan.py AAPL,MSFT,GOOGL --output pmcc_results.json
```

## Key Constraints

- Short strike **must be above** LEAPS strike (debit diagonal, not credit)
- Options with bid = 0 (illiquid) are automatically skipped
- Moderate IV (25-50%) scores highest — see IV section above for rationale
- LEAPS with less than `--min-leaps-days` to expiration are excluded

## Troubleshooting

| Problem | Cause | Solution |
|---------|-------|----------|
| **"No LEAPS found"** | Stock has no long-dated options, or expiration is below `--min-leaps-days` threshold | Lower `--min-leaps-days` to 180; verify the stock has LEAPS (not all stocks do — typically only large-cap, liquid names) |
| **Low scores across all candidates** | IV environment unfavorable (too low or too high) | Check current IV Rank; if <20%, short premiums are too thin for meaningful income; wait for higher IV |
| **"Spread too wide" (high spread%)** | Illiquid options market for that strike/expiry | Use limit orders (mid-price) instead of market orders; consider more liquid alternatives with similar exposure |
| **Large gap between theoretical and actual yield** | Bid-ask spread eating into premium | Focus on candidates with spread < 5% on both legs; avoid weekly expirations on low-volume names |
| **Scanner returns errors for some symbols** | No options available, or data source issue | Verify the ticker has listed options; some small-cap or international stocks lack US-listed options |
| **LEAPS delta too far from target** | Available strikes don't align with target delta | Adjust `--leaps-delta` to match the nearest available deep ITM strike; consider adjacent strikes |

## Limitations

1. **Options eligibility required**: Only works for stocks/ETFs with listed options. Many small-cap stocks, international ADRs, and most A-share/HK stocks lack US-style LEAPS.

2. **LEAPS availability varies**: Not all optionable stocks have LEAPS (expirations >9 months). LEAPS are typically added in September for January expirations 2+ years out. Some stocks may only have monthlies out to 6 months.

3. **Assignment risk on short leg**: American-style options can be exercised early. If the short call goes deep ITM (especially near ex-dividend dates), early assignment is possible. This forces you to exercise the LEAPS to deliver shares, collapsing the position.

4. **Early exercise and dividend risk**: Stocks that pay dividends create early exercise risk on the short call, particularly the day before ex-dividend. If the remaining extrinsic value of the short call is less than the dividend amount, assignment likelihood increases sharply.

5. **IV crush impact**: After earnings or major events, IV can drop 20-40% in a single day. Since the PMCC is net long vega, IV crush reduces LEAPS value more than it reduces short call value, potentially causing a loss even if the stock doesn't move.

6. **Margin requirements**: Some brokers require margin for the short call leg even though the LEAPS provides coverage. Verify your broker treats this as a defined-risk spread.

7. **Scanner uses snapshot data**: Option prices, Greeks, and IV change continuously. Scanner results reflect a point-in-time snapshot — always verify quotes before entering a trade.

## Dependencies

- `numpy`
- `pandas`
- `scipy`
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
