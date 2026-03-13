---
name: market-environment-analysis
description: Comprehensive market environment analysis and reporting tool. Analyzes global markets including US, European, Asian markets, forex, commodities, and economic indicators. Provides risk-on/risk-off assessment, sector analysis, and technical indicator interpretation. Triggers on keywords like market analysis, market environment, global markets, trading environment, market conditions, investment climate, market sentiment, forex analysis, stock market analysis, 相場環境, 市場分析, マーケット状況, 投資環境. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Market Environment Analysis

Comprehensive analysis tool for understanding market conditions and creating professional market reports anytime.

## Core Workflow

### 1. Initial Data Collection
Collect latest market data using web_search tool:
1. Major stock indices (S&P 500, NASDAQ, Dow, Nikkei 225, Shanghai Composite, Hang Seng)
2. Forex rates (USD/JPY, EUR/USD, major currency pairs)
3. Commodity prices (WTI crude, Gold, Silver)
4. US Treasury yields (2-year, 10-year, 30-year)
5. VIX index (Fear gauge)
6. Market trading status (open/close/current values)

### 2. Market Environment Assessment
Evaluate the following from collected data:
- **Trend Direction**: Uptrend/Downtrend/Range-bound
- **Risk Sentiment**: Risk-on/Risk-off
- **Volatility Status**: Market anxiety level from VIX
- **Sector Rotation**: Where capital is flowing

### 3. Report Structure

#### Standard Report Format:
```
1. Executive Summary (3-5 key points)
2. Global Market Overview
   - US Markets
   - Asian Markets
   - European Markets
3. Forex & Commodities Trends
4. Key Events & Economic Indicators
5. Risk Factor Analysis
6. Investment Strategy Implications
```

## Script Usage

### market_utils.py
Provides common functions for report creation:
```bash
# Generate report header
python scripts/market_utils.py

# Available functions:
- format_market_report_header(): Create header
- get_market_session_times(): Check trading hours
- categorize_volatility(vix): Interpret VIX levels
- format_percentage_change(value): Format price changes
```

## Reference Documentation

### Key Indicators Interpretation (references/indicators.md)
Reference when you need:
- Important levels for each index
- Technical analysis key points
- Sector-specific focus areas

### Analysis Patterns (references/analysis_patterns.md)
Reference when analyzing:
- Risk-on/Risk-off criteria
- Economic indicator interpretation
- Inter-market correlations
- Seasonality and market anomalies

## Output Examples

### Quick Summary Version
```
📊 Market Summary [2025/01/15 14:00]
━━━━━━━━━━━━━━━━━━━━━
【US】S&P 500: 5,123.45 (+0.45%)
【JP】Nikkei 225: 38,456.78 (-0.23%)
【FX】USD/JPY: 149.85 (↑0.15)
【VIX】16.2 (Normal range)

⚡ Key Events
- Japan GDP Flash
- US Employment Report

📈 Environment: Risk-On Continues
```

### Detailed Analysis Version
Start with executive summary, then analyze each section in detail.
Key clarifications:
1. Current market phase (Bullish/Bearish/Neutral)
2. Short-term direction (1-5 days outlook)
3. Risk events to monitor
4. Recommended position adjustments

## Important Considerations

### Timezone Awareness
- Consider all major market timezones
- US markets: Evening to early morning (Asian time)
- European markets: Afternoon to evening (Asian time)
- Asian markets: Morning to afternoon (Local time)

### Economic Calendar Priority
Categorize by importance:
- ⭐⭐⭐ Critical (FOMC, NFP, CPI, etc.)
- ⭐⭐ Important (GDP, Retail Sales, etc.)
- ⭐ Reference level

### Data Source Priority
1. Official releases (Central banks, Government statistics)
2. Major financial media (Bloomberg, Reuters)
3. Broker reports
4. Analyst consensus estimates

## Troubleshooting

### Data Collection Notes
- Check market holidays (holiday calendars)
- Be aware of daylight saving time changes
- Distinguish between flash and final data

### Market Volatility Response
1. First organize the facts
2. Reference historical similar events
3. Verify with multiple sources
4. Maintain objective analysis

## Customization Options

Adjust based on user's investment style:
- **Day Traders**: Intraday charts, order flow focus
- **Swing Traders**: Daily/weekly technicals emphasis
- **Long-term Investors**: Fundamentals, macro economics focus
- **Forex Traders**: Currency correlations, interest rate differentials
- **Options Traders**: Volatility analysis, Greeks monitoring

## 量化 Risk-On/Risk-Off 评分

### 评估框架 (0-100, 100=极度 Risk-On)

| # | 指标 | 权重 | Risk-On 信号 | Risk-Off 信号 | 数据源 |
|---|------|------|-------------|-------------|--------|
| 1 | VIX 水平 | 20% | <15 | >25 | yfinance: ^VIX |
| 2 | 收益率曲线 | 15% | 正斜率扩大 | 倒挂加深 | FRED: GS2, GS10 |
| 3 | 信用利差 | 15% | 收窄 | 扩大 | FRED: BAMLH0A0HYM2 |
| 4 | 美元强度 | 10% | 走弱 | 走强 | yfinance: UUP |
| 5 | 商品/黄金比 | 10% | 铜/金比上升 | 铜/金比下降 | yfinance: COPX/GLD |
| 6 | 全球权益动量 | 15% | ACWI >50MA | ACWI <50MA | yfinance: ACWI |
| 7 | 新兴市场相对 | 15% | EEM 跑赢 SPY | EEM 跑输 SPY | yfinance: EEM/SPY |

### 与其他 Skills 联动

| 分析维度 | 推荐 Skill | 数据输入 |
|---------|-----------|---------|
| 波动率分析 | fear-greed-index | VIX + 期限结构 |
| 流动性条件 | macro-liquidity-monitor | Fed + 信用 |
| 板块轮动 | sector-analyst | 板块资金流 |
| 市场广度 | market-breadth-analyzer | A/D 线 |
| 地缘风险 | geopolitical-risk-monitor | 风险事件 |

### 结构化 JSON 输出

```json
{
  "title": "市场环境分析",
  "generated_at": "ISO8601",
  "risk_appetite_score": 65,
  "regime": "Risk-On",
  "markets": {
    "us": {"index": "S&P 500", "level": 5823, "change_1d": "+0.45%", "trend": "uptrend"},
    "asia": {"index": "Nikkei 225", "level": 38456, "change_1d": "-0.23%", "trend": "range"},
    "europe": {"index": "STOXX 600", "level": 512, "change_1d": "+0.12%", "trend": "uptrend"},
    "china": {"index": "CSI 300", "level": 3845, "change_1d": "+1.2%", "trend": "recovery"}
  },
  "key_levels": {"vix": 16.2, "dxy": 103.5, "us10y": 4.25, "gold": 2185},
  "outlook": "短期 Risk-On 延续，关注本周 FOMC 决议"
}
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
