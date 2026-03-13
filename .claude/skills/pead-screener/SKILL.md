---
name: pead-screener
description: Screen post-earnings gap-up stocks for PEAD (Post-Earnings Announcement Drift) patterns. Analyzes weekly candle formation to detect red candle pullbacks and breakout signals. Supports two input modes - FMP earnings calendar (Mode A) or earnings-trade-analyzer JSON output (Mode B). Use when user asks about PEAD screening, post-earnings drift, earnings gap follow-through, red candle breakout patterns, or weekly earnings momentum setups. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# PEAD Screener - Post-Earnings Announcement Drift

Screen post-earnings gap-up stocks for PEAD (Post-Earnings Announcement Drift) patterns using weekly candle analysis to detect red candle pullbacks and breakout signals.

## When to Use

- User asks for PEAD screening or post-earnings drift analysis
- User wants to find earnings gap-up stocks with follow-through potential
- User requests red candle breakout patterns after earnings
- User asks for weekly earnings momentum setups
- User provides earnings-trade-analyzer JSON output for further screening

## Prerequisites

- FMP API key (set `FMP_API_KEY` environment variable or pass `--api-key`)
- Free tier (250 calls/day) is sufficient for default screening
- For Mode B: earnings-trade-analyzer JSON output file with schema_version "1.0"

## Workflow

### Step 1: Prepare and Execute Screening

Run the PEAD screener script in one of two modes:

**Mode A (FMP earnings calendar):**
```bash
# Default: last 14 days of earnings, 5-week monitoring window
python3 skills/pead-screener/scripts/screen_pead.py --output-dir reports/

# Custom parameters
python3 skills/pead-screener/scripts/screen_pead.py \
  --lookback-days 21 \
  --watch-weeks 6 \
  --min-gap 5.0 \
  --min-market-cap 1000000000 \
  --output-dir reports/
```

**Mode B (earnings-trade-analyzer JSON input):**
```bash
# From earnings-trade-analyzer output
python3 skills/pead-screener/scripts/screen_pead.py \
  --candidates-json reports/earnings_trade_analyzer_YYYY-MM-DD_HHMMSS.json \
  --min-grade B \
  --output-dir reports/
```

### Step 2: Review Results

1. Read the generated JSON and Markdown reports
2. Load `references/pead_strategy.md` for PEAD theory and pattern context
3. Load `references/entry_exit_rules.md` for trade management rules

### Step 3: Present Analysis

For each candidate, present:
- Stage classification (MONITORING, SIGNAL_READY, BREAKOUT, EXPIRED)
- Weekly candle pattern details (red candle location, breakout status)
- Composite score and rating
- Trade setup: entry, stop-loss, target, risk/reward ratio
- Liquidity metrics (ADV20, average volume)

### Step 4: Provide Actionable Guidance

Based on stages and ratings:
- **BREAKOUT + Strong Setup (85+):** High-conviction PEAD trade, full position size
- **BREAKOUT + Good Setup (70-84):** Solid PEAD setup, standard position size
- **SIGNAL_READY:** Red candle formed, set alert for breakout above red candle high
- **MONITORING:** Post-earnings, no red candle yet, add to watchlist
- **EXPIRED:** Beyond monitoring window, remove from watchlist

## Output

- `pead_screener_YYYY-MM-DD_HHMMSS.json` - Structured results with stage classification
- `pead_screener_YYYY-MM-DD_HHMMSS.md` - Human-readable report grouped by stage

## Resources

- `references/pead_strategy.md` - PEAD theory and weekly candle approach
- `references/entry_exit_rules.md` - Entry, exit, and position sizing rules

## PEAD 方法论详解

### 什么是 PEAD (Post-Earnings Announcement Drift)?

学术研究表明，财报后股价倾向于沿着财报当日方向继续漂移 60-90 天。PEAD 策略利用这一统计偏差：

1. **筛选条件**: 财报日跳空上涨 >5%（表明超预期）
2. **等待红蜡烛**: 周线图上出现红色蜡烛（收盘 < 开盘）= 短期回调
3. **突破进场**: 红蜡烛高点被突破 = PEAD 漂移恢复

### 阶段分类详解

```
MONITORING → SIGNAL_READY → BREAKOUT → EXPIRED
   ↓              ↓             ↓           ↓
 财报后跳空     出现红蜡烛    突破红蜡烛高   超出窗口期
 等待回调       设置警报      执行买入       移出观察
```

| 阶段 | 定义 | 交易动作 |
|------|------|---------|
| MONITORING | 财报跳空上涨后，尚未出现周线红蜡烛 | 加入观察名单 |
| SIGNAL_READY | 出现至少一根周线红蜡烛（收盘<开盘） | 设置突破警报：价格 > 红蜡烛高点 |
| BREAKOUT | 价格突破红蜡烛高点，成交量放大 | 买入，止损设在红蜡烛低点下方 |
| EXPIRED | 超出 watch-weeks 窗口（默认 5 周） | 移出观察名单 |

### 红蜡烛量化定义

- **周线级别**: 使用周线（非日线）蜡烛
- **红色条件**: 周收盘价 < 周开盘价
- **有效性**: 蜡烛实体不能太小（收盘-开盘 > 0.5% 最小幅度）
- **位置**: 必须在财报跳空后的首个基底形成期内

### 进出场规则示例

```
进场: AAPL 财报跳空 +8%，第 3 周出现红蜡烛 (H=198, L=192, C=194)
  → 买入价: $198.50 (红蜡烛高点 +0.25%)
  → 止损: $191.50 (红蜡烛低点 -0.25%)
  → 风险: ($198.50 - $191.50) / $198.50 = 3.5%
  → 目标: $212 (风险的 2:1 = $14 上方)
```

### 常见问题

- **Mode A vs Mode B**: Mode A 从 FMP 日历自动获取财报股，Mode B 接受 earnings-trade-analyzer 输出进行二次筛选
- **min-gap 设置**: 默认 5%，科技股可放宽至 3%，防御性板块可收紧至 8%
- **watch-weeks 窗口**: 默认 5 周，研究表明 PEAD 漂移主要在 60 天内，超出后概率下降

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
