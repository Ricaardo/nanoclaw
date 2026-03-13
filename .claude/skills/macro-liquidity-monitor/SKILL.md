---
name: macro-liquidity-monitor
description: "Monitors macro liquidity conditions using 8-component weighted scoring system (0-100, 100=most accommodative). Covers Fed balance sheet, net liquidity, yield curve, credit spreads, dollar, overnight rates, commodities, and crypto risk appetite. Use when user asks about liquidity conditions, financial conditions, or whether liquidity supports risk assets. 当用户用中文询问流动性状况、金融条件、资金面、流动性是否支持风险资产时触发。"
---

# Macro Liquidity Monitor Skill

## Purpose

Quantify financial system liquidity using a data-driven 8-component weighted scoring system (0-100). Synthesizes Fed balance sheet dynamics, net liquidity flows, yield curve, credit conditions, dollar strength, overnight rates, commodity signals, and crypto risk appetite.

**Score direction:** 100 = Maximum liquidity (flood), 0 = Liquidity drought.

**API keys:** FRED (required), yfinance + Binance (no key needed).

## When to Use This Skill

- User asks "How are liquidity conditions?" or "Is liquidity supporting risk assets?"
- User wants Fed balance sheet impact on markets
- User asks about net liquidity, credit spreads, or financial conditions
- 「流动性状况如何？」「资金面是否支持风险资产？」「信用利差走势？」

## Prerequisites

- **Python 3.8+** with `requests`, `yfinance`
- **FRED API key** — set via `--api-key` or `FRED_API_KEY` env var
- **Internet access** for yfinance and Binance public API

---

## Execution Workflow

### Phase 1: Execute Python Script

```bash
python3 skills/macro-liquidity-monitor/scripts/macro_liquidity_monitor.py --api-key "$FRED_API_KEY" --lang zh
```

Optional: `--output-dir`, `--lookback-days 365`

### Phase 2: Present Results

Present composite score, zone, and each component's contribution.

---

## 8-Component Scoring System

| # | Component | Weight | Data Source | Key Signal |
|---|-----------|--------|-------------|------------|
| 1 | Fed Balance Sheet | **15%** | FRED: WALCL | 4w/13w momentum |
| 2 | Net Liquidity | **20%** | FRED: WALCL-TGA-RRP+SRF+SWPT | 有效流动性趋势 + TGA 季节性 |
| 3 | Yield Curve | **15%** | FRED: GS2, GS10 | 2s10s spread + direction |
| 4 | Credit Spreads | **15%** | FRED: BAMLH0A0HYM2 | HY OAS level + direction |
| 5 | Dollar Strength | **10%** | yfinance: UUP | 30d trend (inverse) |
| 6 | Overnight Rate | **5%** | FRED: SOFR, DFF | vs target rate deviation |
| 7 | Commodity/Oil Shock | **10%** | yfinance: CL=F, GC=F | 油价冲击 + 滞胀信号 |
| 8 | Crypto Risk Appetite | **10%** | Binance: BTC | 30d/90d momentum |

### Key Enhancements (v2.2.1)
- **TGA 季节性前瞻**: 4/15 税期、季度估税、季末窗口粉饰自动扣分
- **油价冲击检测**: 油价 >15% 暴涨 = 供给冲击，滞胀信号（金油齐涨）
- **增强净流动性公式**: +SRF (Standing Repo) +SWPT (央行互换)
- **保守缺失处理**: 缺失组件用 45 分（非排除），覆盖率低时额外收缩
- **置信度等级**: high/medium/low 基于数据覆盖率

## Score Zones (100 = Most Accommodative)

| Score | Zone | Guidance |
|-------|------|----------|
| 80-100 | 流动性泛滥 (Flood) | 全面风险偏好 |
| 60-79 | 流动性宽松 (Easing) | 条件有利 |
| 40-59 | 流动性中性 (Neutral) | 信号混合 |
| 20-39 | 流动性收紧 (Tightening) | 减少敞口 |
| 0-19 | 流动性枯竭 (Drought) | 资本保全 |

~12 FRED + 5 yfinance + 1 Binance calls per run. Optional: Twelve Data + OKX fallback.

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
component: 商品/油价冲击
search: gold price today XAU/USD, WTI crude oil price today
---
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
