---
name: scanner-bullish
description: Scan stocks for bullish trends using technical indicators (SMA, RSI, MACD, ADX). Use when user asks to scan for bullish stocks, find trending stocks, or rank symbols by momentum. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
dependencies: ["trading-skills"]
---

# Bullish Scanner — 看涨技术形态扫描

## Purpose（目的）

Bullish Scanner 是一个多指标复合评分的看涨趋势扫描工具。它将 SMA 均线系统、RSI 动量、MACD 趋势、ADX 方向性四类经典技术指标整合为一个 0-8 分的综合评分体系，用于从一组候选标的中快速筛选出处于上升趋势的股票。

**核心价值：**
- **效率**：一次扫描数十只标的，按综合评分排序，快速缩小关注范围
- **客观**：基于量化指标打分，避免主观偏见
- **多维度**：结合趋势（SMA）、动量（RSI/MACD）、方向强度（ADX）四类信号，减少单一指标的误导

**典型使用场景：**
- 每日/每周例行扫描自选股列表，发现新的趋势启动
- 板块轮动分析中，对比同板块个股的趋势强度
- 与基本面筛选（如 CANSLIM、value-dividend-screener）配合使用，对基本面合格标的做技术面二次过滤

---

## When to Use（何时使用）

**显式触发：**
- "扫描这些股票的看涨趋势"
- "帮我找出上涨趋势最强的标的"
- "对这些 ticker 做技术面排名"
- "Scan these symbols for bullish trends"
- "Rank these stocks by momentum"
- "Which of these stocks are trending up?"

**隐式触发：**
- 用户提供一组 ticker 并要求"筛选"或"排序"
- 用户询问"哪些股票值得关注"（技术面角度）
- 用户要求"找出动量最强的标的"

**不适用场景：**
- 仅需单只标的的详细技术分析 → 使用 `technical-analyst`
- 需要基本面数据（PE、营收等）→ 使用 `fundamentals` 或 `us-stock-analysis`
- 需要期权策略 → 使用 `options-strategy-advisor`

---

## Prerequisites（前置条件）

| 依赖 | 版本 | 用途 |
|------|------|------|
| Python | 3.8+ | 运行环境 |
| pandas | ≥1.3 | 数据处理 |
| pandas-ta | ≥0.3 | 技术指标计算（SMA/RSI/MACD/ADX） |
| yfinance | ≥0.2 | 历史行情数据获取 |

**安装：**
```bash
pip install pandas pandas-ta yfinance
# 或使用 uv
uv add pandas pandas-ta yfinance
```

---

## Instructions（使用方法）

> **Note:** If `uv` is not installed or `pyproject.toml` is not found, replace `uv run python` with `python` in all commands below.

```bash
uv run python scripts/scan.py SYMBOLS [--top N] [--period PERIOD]
```

### Arguments

- `SYMBOLS` — Comma-separated ticker symbols (e.g., `AAPL,MSFT,GOOGL,NVDA`)
- `--top` — Number of top results to return (default: 30)
- `--period` — Historical period for analysis: `1mo`, `3mo`, `6mo` (default: `3mo`)

### Examples

```bash
# 基础扫描：5 只美股
uv run python scripts/scan.py AAPL,MSFT,GOOGL,NVDA,TSLA

# 扩大扫描并取 Top 10
uv run python scripts/scan.py AAPL,MSFT,GOOGL,NVDA,TSLA,AMD,AMZN,META --top 10

# 使用 6 个月回看期（适合中线趋势判断）
uv run python scripts/scan.py AAPL,MSFT,GOOGL --period 6mo

# A 股扫描
uv run python scripts/scan.py 600519.SH,000858.SZ,601318.SH

# 港股扫描
uv run python scripts/scan.py 00700.HK,09988.HK,01810.HK
```

---

## Scoring System（评分体系，满分约 8 分）

### 指标详解

| 指标 | 条件 | 得分 | 原理说明 |
|------|------|------|----------|
| **SMA20** | Price > SMA20 | +1.0 | 价格站上 20 日均线，短期趋势向上。SMA20 是最常用的短期趋势参考线，代表近一个月的平均持仓成本 |
| **SMA50** | Price > SMA50 | +1.0 | 价格站上 50 日均线，中期趋势向上。SMA50 代表约两个半月的持仓成本，是机构常用的中期趋势判断依据 |
| **RSI** | 50-70（看涨区间） | +1.0 | RSI 处于健康的上升动量区间。50 以上表示多头占优，70 以下说明尚未过热 |
| | 30-50（中性区间） | +0.5 | 动量偏中性，可能正在筑底或盘整 |
| | <30（超卖区间） | +0.25 | 严重超卖，虽然可能反弹，但当前趋势仍偏弱，仅给少量分数 |
| **MACD** | MACD > Signal Line | +1.0 | MACD 线在信号线之上，表示短期动量强于中期动量，趋势偏多 |
| | Histogram 上升 | +0.5 | MACD 柱状图递增，表示多头动能正在加速 |
| **ADX** | >25 且 +DI > -DI | +1.5 | ADX>25 表示趋势明显，+DI>-DI 表示方向为上涨。这是最高分指标，因为它同时确认了趋势强度和方向 |
| | 仅 +DI > -DI | +0.5 | 方向向上但趋势不够强（ADX<25），可能是趋势初期或震荡市 |
| **Momentum** | 3 个月收益率 / 20 | -1 ~ +2 | 将实际价格涨幅转化为连续分数。20% 涨幅得 +1 分，40% 得 +2 分（封顶），-20% 得 -1 分（最低）。反映价格层面的实际表现 |

### 组合信号解读

| 信号组合 | 含义 | 操作建议 |
|----------|------|----------|
| SMA20 > SMA50 且均线都在价格下方 | **金叉 + 多头排列**：短期趋势强于中期，且价格站上两条均线 | 趋势确认信号，可作为入场参考 |
| MACD 金叉 + RSI 50-70 | **动量共振**：两个独立的动量指标同时给出看涨信号 | 高置信度的动量确认 |
| ADX>25 + 所有均线/动量指标看涨 | **强趋势全面确认**：方向明确且趋势强劲 | 评分通常 >6，是最佳的趋势追踪时机 |
| 价格 > SMA20 但 < SMA50 | **短期反弹但中期趋势未恢复** | 谨慎对待，可能是下跌中的反弹 |
| RSI > 70 | **超买**（扫描器不给额外分数） | 短期回调风险增加，注意仓位管理 |

---

## Output（输出格式）

返回 JSON，包含以下字段：

- `scan_date` — 扫描时间戳
- `symbols_scanned` — 扫描的标的总数
- `results` — 按评分从高到低排序的结果数组：
  - `symbol`, `score`, `price`
  - `next_earnings`, `earnings_timing` (BMO/AMC)
  - `period_return_pct`, `pct_from_sma20`, `pct_from_sma50`
  - `rsi`, `macd`, `adx`, `dmp`, `dmn`
  - `signals` — 触发的条件列表

### Output Example（输出示例）

```json
{
  "scan_date": "2026-03-13T10:30:00",
  "symbols_scanned": 5,
  "results": [
    {
      "symbol": "NVDA",
      "score": 7.2,
      "price": 142.50,
      "next_earnings": "2026-05-28",
      "earnings_timing": "AMC",
      "period_return_pct": 18.5,
      "pct_from_sma20": 3.2,
      "pct_from_sma50": 8.7,
      "rsi": 62.4,
      "macd": 2.15,
      "adx": 32.1,
      "dmp": 28.5,
      "dmn": 14.2,
      "signals": ["Above SMA20", "Above SMA50", "RSI bullish (50-70)", "MACD above signal", "Histogram rising", "ADX strong trend (+DI > -DI)"]
    },
    {
      "symbol": "AAPL",
      "score": 4.8,
      "price": 198.30,
      "next_earnings": "2026-04-24",
      "earnings_timing": "AMC",
      "period_return_pct": 6.2,
      "pct_from_sma20": 1.1,
      "pct_from_sma50": -0.8,
      "rsi": 55.1,
      "macd": 0.43,
      "adx": 18.7,
      "dmp": 22.3,
      "dmn": 19.1,
      "signals": ["Above SMA20", "RSI bullish (50-70)", "MACD above signal", "+DI > -DI"]
    },
    {
      "symbol": "TSLA",
      "score": 1.5,
      "price": 175.20,
      "period_return_pct": -12.3,
      "pct_from_sma20": -4.5,
      "pct_from_sma50": -11.2,
      "rsi": 38.2,
      "macd": -3.72,
      "adx": 29.4,
      "dmp": 12.8,
      "dmn": 31.5,
      "signals": ["RSI neutral (30-50)"]
    }
  ]
}
```

---

## Interpretation Guide（结果解读）

| 评分区间 | 趋势判断 | 操作建议 |
|----------|----------|----------|
| **> 6** | **强看涨** — 所有指标共振向上 | 多个技术指标同时确认上升趋势。可作为入场候选。建议结合成交量确认（放量上涨更可靠），并检查是否接近阻力位 |
| **4 - 6** | **中等看涨** — 部分指标看涨，存在分歧 | 趋势正在形成但尚未完全确认。建议等待更多确认信号（如 MACD 金叉、突破均线），或使用较小仓位试探 |
| **2 - 4** | **中性/弱势** — 无明确趋势 | 标的处于盘整或方向不明状态。不建议追涨，可加入观察列表等待信号清晰 |
| **< 2** | **偏空** — 多数指标看跌 | 下跌趋势中或动量严重不足。应回避做多，或在反转交易体系中寻找超卖反弹机会 |

**补充说明：**
- 评分应结合**成交量分析**：高分标的如果伴随缩量，可能是假突破
- 评分应结合**市场大环境**（market regime）：大盘下跌时，个股高分可能不可持续。建议配合 `market-breadth-analyzer` 或 `macro-regime-detector` 判断大环境
- 不同市场的分数分布可能不同：A 股涨跌停制度下，动量分布与美股有差异
- 连续多次扫描观察分数变化趋势，比单次绝对分数更有参考价值

---

## Limitations（局限性）

1. **仅技术面指标**：不考虑基本面（营收/利润/估值）、资金面（机构持仓/资金流）或消息面。一只基本面恶化的股票可能因技术反弹获得高分
2. **滞后性**：SMA、MACD 等指标本质上是滞后指标，反映的是已发生的价格行为。在趋势拐点处可能给出延迟信号
3. **筛选工具而非交易信号**：高分标的是值得进一步研究的候选，而不是直接的买入信号。应结合 `technical-analyst`（图表分析）、`fundamentals`（基本面）、`risk-assessment`（风险评估）等做完整分析
4. **市场状态敏感**：在系统性下跌（熊市）中，几乎所有标的评分都会偏低，这是正常现象而非工具故障
5. **数据依赖 yfinance**：部分 A 股/港股 ticker 可能需要正确的后缀格式（.SH / .SZ / .HK），且非交易时段数据可能延迟

---

## Troubleshooting（常见问题）

| 问题 | 可能原因 | 解决方案 |
|------|----------|----------|
| 扫描结果为空 | 市场休市或 ticker 格式错误 | 确认当前是否为交易时段；检查 ticker 是否正确（美股大写字母，A 股需 `.SH`/`.SZ` 后缀，港股需 `.HK` 后缀） |
| 所有标的评分都很低 | 市场处于整体下跌趋势 | 这是正常现象。在熊市中大部分股票的技术指标都偏空。可配合 `market-breadth-analyzer` 确认市场状态 |
| yfinance 报错 / 超时 | 网络问题或 API 限流 | 检查网络连接；减少单次扫描的 ticker 数量；增加重试间隔 |
| 某只标的数据缺失 | ticker 不存在或已退市 | 在 Yahoo Finance 网站上手动搜索确认 ticker 有效性 |
| 评分与直觉不符 | 指标基于 3 个月数据，可能与短期走势不同 | 尝试调整 `--period` 参数（`1mo` 更敏感，`6mo` 更平滑）来匹配你的分析时间框架 |

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
