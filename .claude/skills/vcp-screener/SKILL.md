---
name: vcp-screener
description: Screen S&P 500 stocks for Mark Minervini's Volatility Contraction Pattern (VCP). Identifies Stage 2 uptrend stocks forming tight bases with contracting volatility near breakout pivot points. Use when user requests VCP screening, Minervini-style setups, tight base patterns, volatility contraction breakout candidates, or Stage 2 momentum stock scanning. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# VCP Screener - Minervini Volatility Contraction Pattern

Screen S&P 500 stocks for Mark Minervini's Volatility Contraction Pattern (VCP), identifying Stage 2 uptrend stocks with contracting volatility near breakout pivot points.

## When to Use

- User asks for VCP screening or Minervini-style setups
- User wants to find tight base / volatility contraction patterns
- User requests Stage 2 momentum stock scanning
- User asks for breakout candidates with defined risk

## Prerequisites

- FMP API key (set `FMP_API_KEY` environment variable or pass `--api-key`)
- Free tier (250 calls/day) is sufficient for default screening (top 100 candidates)
- Paid tier recommended for full S&P 500 screening (`--full-sp500`)

## Workflow

### Step 1: Prepare and Execute Screening

Run the VCP screener script:

```bash
# Default: S&P 500, top 100 candidates
python3 skills/vcp-screener/scripts/screen_vcp.py --output-dir skills/vcp-screener/scripts

# Custom universe
python3 skills/vcp-screener/scripts/screen_vcp.py --universe AAPL NVDA MSFT AMZN META --output-dir skills/vcp-screener/scripts

# Full S&P 500 (paid API tier)
python3 skills/vcp-screener/scripts/screen_vcp.py --full-sp500 --output-dir skills/vcp-screener/scripts
```

### Advanced Tuning (for backtesting)

Adjust VCP detection parameters for research and backtesting:

```bash
python3 skills/vcp-screener/scripts/screen_vcp.py \
  --min-contractions 3 \
  --t1-depth-min 12.0 \
  --breakout-volume-ratio 2.0 \
  --trend-min-score 90 \
  --atr-multiplier 1.5 \
  --output-dir reports/
```

| Parameter | Default | Range | Effect |
|-----------|---------|-------|--------|
| `--min-contractions` | 2 | 2-4 | Higher = fewer but higher-quality patterns |
| `--t1-depth-min` | 8.0% | 1-50 | Higher = excludes shallow first corrections |
| `--breakout-volume-ratio` | 1.5x | 0.5-10 | Higher = stricter volume confirmation |
| `--trend-min-score` | 85 | 0-100 | Higher = stricter Stage 2 filter |
| `--atr-multiplier` | 1.5 | 0.5-5 | Lower = more sensitive swing detection |
| `--contraction-ratio` | 0.75 | 0.1-1 | Lower = requires tighter contractions |
| `--min-contraction-days` | 5 | 1-30 | Higher = longer minimum contraction |
| `--lookback-days` | 120 | 30-365 | Longer = finds older patterns |

### Step 2: Review Results

1. Read the generated JSON and Markdown reports
2. Load `references/vcp_methodology.md` for pattern interpretation context
3. Load `references/scoring_system.md` for score threshold guidance

### Step 3: Present Analysis

For each top candidate, present:
- VCP composite score and rating
- Contraction details (T1/T2/T3 depths and ratios)
- Trade setup: pivot price, stop-loss, risk percentage
- Volume dry-up ratio
- Relative strength rank

### Step 4: Provide Actionable Guidance

Based on ratings:
- **Textbook VCP (90+):** Buy at pivot with aggressive sizing
- **Strong VCP (80-89):** Buy at pivot with standard sizing
- **Good VCP (70-79):** Buy on volume confirmation above pivot
- **Developing (60-69):** Add to watchlist, wait for tighter contraction
- **Weak/No VCP (<60):** Monitor only or skip

## 3-Phase Pipeline

1. **Pre-Filter** - Quote-based screening (price, volume, 52w position) ~101 API calls
2. **Trend Template** - 7-point Stage 2 filter with 260-day histories ~100 API calls
3. **VCP Detection** - Pattern analysis, scoring, report generation (no additional API calls)

## Output

- `vcp_screener_YYYY-MM-DD_HHMMSS.json` - Structured results
- `vcp_screener_YYYY-MM-DD_HHMMSS.md` - Human-readable report

## Resources

- `references/vcp_methodology.md` - VCP theory and Trend Template explanation
- `references/scoring_system.md` - Scoring thresholds and component weights
- `references/fmp_api_endpoints.md` - API endpoints and rate limits

## VCP 方法论详解

### 什么是 VCP (Volatility Contraction Pattern)?

Mark Minervini 的 VCP 是一种价格形态，具有以下特征：

1. **Stage 2 上升趋势**: 股价位于所有关键均线之上（50MA > 150MA > 200MA），200MA 上升
2. **波动收缩**: 每次修正（T1→T2→T3）的深度递减（如 25%→15%→8%）
3. **成交量萎缩**: 基底右侧成交量明显萎缩（dry up），通常低于 50 日均量
4. **突破点 (Pivot)**: 最后一次收缩的高点即为买入点

### Trend Template (7 项过滤器)

| # | 条件 | 理由 |
|---|------|------|
| 1 | 收盘价 > 150MA 且 > 200MA | 确认 Stage 2 |
| 2 | 150MA > 200MA | 中期趋势向上 |
| 3 | 200MA 至少上升 1 个月 | 长期趋势确认 |
| 4 | 50MA > 150MA 且 > 200MA | 短中长期均线多头排列 |
| 5 | 收盘价 > 50MA | 短期趋势健康 |
| 6 | 收盘价距 52 周低点 >30% | 已脱离底部 |
| 7 | 收盘价距 52 周高点 <25% | 接近新高，非深度回调 |

### 参数敏感性分析

| 参数 | 默认 | 松弛 | 严格 | 影响 |
|------|------|------|------|------|
| min-contractions | 2 | 1 | 4 | 松弛→更多候选但假信号多；严格→极少但高质量 |
| t1-depth-min | 8% | 5% | 15% | 低→包含浅修正(科技股常见)；高→只看深度修正 |
| breakout-volume-ratio | 1.5x | 1.0x | 3.0x | 低→更多信号；高→只要放量确认的突破 |
| trend-min-score | 85 | 70 | 100 | 低→包含早期 Stage 2；高→只要完美趋势 |
| contraction-ratio | 0.75 | 0.85 | 0.50 | 高→允许较宽松收缩；低→要求明显收紧 |

### 常见问题

- **结果为零**: 大盘处于下跌趋势时，满足 Stage 2 的股票很少，这是正常的
- **FMP API 限额**: 免费层 250 calls/day，全 S&P 500 需 ~200 calls，仅限每日一次
- **VCP vs Cup-and-Handle**: VCP 是多次收缩，杯柄是一次大修正+一次小回调，两者可重叠

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
