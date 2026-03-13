---
name: geopolitical-risk-monitor
description: "Quantifies geopolitical risk using 5-component weighted scoring system (0-100, 100=highest risk). Combines news sentiment, safe haven flows, oil disruption signals, volatility/credit stress, and cross-asset confirmation. Use when user asks about geopolitical risk, war impact on markets, sanctions effects, or global political tensions. 当用户用中文询问地缘政治风险、战争对市场影响、制裁影响、全球政治紧张局势时触发。"
---

# Geopolitical Risk Monitor Skill

## Purpose

Quantify geopolitical risk using a data-driven 5-component weighted scoring system (0-100). Combines news semantics, safe haven asset flows, oil disruption signals, volatility/credit stress, and cross-asset confirmation.

**Score direction:** 100 = Maximum risk (crisis), 0 = Calm (risk-on).

**API keys:** Finnhub (news), FRED (yields/credit). Also uses yfinance (no key).

## When to Use This Skill

- User asks about geopolitical risk, war impact, sanctions effects
- User wants safe haven flow analysis or oil disruption risk
- 「地缘政治风险有多高？」「战争对市场影响？」「避险资产走势？」

## Prerequisites

- **Python 3.8+** with `requests`, `yfinance`
- **Finnhub API key** — set via `--finnhub-key` or `FINNHUB_API_KEY`
- **FRED API key** — set via `--fred-key` or `FRED_API_KEY`

---

## Execution Workflow

### Phase 1: Execute Python Script

```bash
python3 skills/geopolitical-risk-monitor/scripts/geopolitical_risk_monitor.py \
  --finnhub-key "$FINNHUB_API_KEY" --fred-key "$FRED_API_KEY" --lang zh
```

Optional: `--output-dir`, `--lookback-days 7`

### Phase 2: Present Results

Present composite risk score, zone, component details, and top geopolitical articles.

---

## 5-Component Scoring System

| # | Component | Weight | Data Source | Key Signal |
|---|-----------|--------|-------------|------------|
| 1 | News Signal | **30%** | Finnhub + keyword classifier | Geo article volume & severity |
| 2 | Safe Haven Flows | **25%** | yfinance (GLD/FXY/FXF) + FRED (GS10) | Gold/Yen/Franc rally + yield drop |
| 3 | Oil Disruption | **15%** | yfinance (CL=F/BZ=F) | Oil price spike |
| 4 | Volatility & Credit | **15%** | yfinance (^VIX) + FRED (BAMLH0A0HYM2) | VIX spike + HY spread widening |
| 5 | Cross-Asset | **15%** | yfinance (SPY/EFA/EEM) | EM vs DM divergence |

## Risk Zone Mapping (100 = Highest Risk)

| Score | Zone | Guidance |
|-------|------|----------|
| 80-100 | 危机 (Crisis) | 最大防御配置 |
| 60-79 | 高度紧张 (Elevated) | 对冲 + 减仓 |
| 40-59 | 紧张 (Heightened) | 密切监控 + 开始对冲 |
| 20-39 | 关注 (Watch) | 正常但保持警惕 |
| 0-19 | 平静 (Calm) | 风险偏好环境 |

~3 Finnhub + 2 FRED + 7 yfinance calls per run. Optional: Twelve Data fallback.

---

## 数据补全（Web Search Fallback）

当脚本输出包含 `---SEARCH_NEEDED---` 标记时，表示部分数据源全部失败：

1. 解析标记块中的 `component` 和 `search` 字段
2. 对每个缺失指标执行 **WebSearch**，提取最新数值
3. 用搜索到的数据重新计算该组件评分（参考上方评分规则）
4. 在报告中标注 **[搜索补全]** 以区分数据来源

示例标记：
```
---SEARCH_NEEDED---
component: 避险资金流
search: GLD gold ETF price today, FXY yen ETF price, FXF franc ETF price
---
```

---

## 语言与输出规则

### 中文输出
- 所有分析报告、摘要、建议使用**中文**输出
- 保留英文的情况：ticker 代码（GLD, CL=F）、专有名词首次出现时附英文（高收益债 HY OAS）、数据源名称
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
