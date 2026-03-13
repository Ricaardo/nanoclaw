---
name: fear-greed-index
description: "Multi-market Fear & Greed Index with weighted composite scoring (0-100, 0=Extreme Fear, 100=Extreme Greed). Covers US, A-share, HK, and Crypto markets. Use when user asks about market sentiment, fear and greed, 贪恐指数, investor sentiment, or whether the market is overheated/oversold. 当用户用中文询问市场情绪、贪恐指数、恐慌贪婪指数、市场温度时触发。支持美股/A股/港股/加密货币多市场分析。"
---

# Fear & Greed Index — 多市场贪恐指数

## Purpose

量化多市场投资者情绪，生成 0-100 贪恐指数。综合波动率、动量、资金流、市场广度、避险需求等多维数据，诊断市场处于恐惧还是贪婪状态。

**评分方向:** 0 = 极度恐惧 (Extreme Fear), 100 = 极度贪婪 (Extreme Greed)
**注意:** 与 CNN Fear & Greed Index 方向一致（高分 = 贪婪）

**API keys:** FRED (可选), yfinance + AKShare + Binance (无需 key)

## When to Use This Skill

- User asks "What's the current fear and greed level?"
- User asks about market sentiment or whether it's time to buy/sell
- User wants to know if market is overheated or oversold
- 「当前市场情绪如何？」「贪恐指数是多少？」「市场是否过热？」「恐慌了吗？」
- User specifies a market: `--market us` / `a_share` / `hk` / `crypto` / `all`

## Prerequisites

- **Python 3.8+** with `requests`, `yfinance`
- **可选:** `akshare` (A股/港股), FRED API key (美股增强)
- **Internet access** for yfinance, AKShare, Binance/OKX public API

---

## Execution Workflow

### Phase 1: Execute Python Script

```bash
# 全市场（默认）
python3 skills/fear-greed-index/scripts/fear_greed_index.py --lang zh

# 指定市场
python3 skills/fear-greed-index/scripts/fear_greed_index.py --market us --lang zh
python3 skills/fear-greed-index/scripts/fear_greed_index.py --market a_share --lang zh
python3 skills/fear-greed-index/scripts/fear_greed_index.py --market hk --lang zh
python3 skills/fear-greed-index/scripts/fear_greed_index.py --market crypto --lang zh

# 可选参数
--api-key "$FRED_API_KEY"   # FRED 增强（美股 Put/Call ratio）
--output-dir reports/       # 保存报告
--verbose                   # 调试日志
```

### Phase 2: Present Results

呈现各市场贪恐指数、组件评分、信号和投资指引。

### Phase 3: Web Search Fallback

当脚本输出 `---SEARCH_NEEDED---` 时，执行 WebSearch 补全缺失数据。

---

## 评分体系

### 美股 (US Market) — 7 组件

| # | Component | Weight | Data Source | Scoring Logic |
|---|-----------|--------|-------------|---------------|
| 1 | VIX 波动率 | **20%** | yfinance: ^VIX | VIX<12→95, 12-15→75, 15-20→55, 20-25→35, 25-30→20, >30→5 |
| 2 | Put/Call Ratio | **15%** | FRED: PCERATIO / WebSearch | P/C<0.60→90, 0.60-0.70→75, 0.70-0.85→50, 0.85-1.0→30, >1.0→10 |
| 3 | 市场广度 | **15%** | yfinance: RSP/SPY 比率 | RSP 跑赢 SPY→贪婪, 跑输→恐惧 |
| 4 | 价格动量 | **15%** | yfinance: SPY 125MA | SPY >125MA 越多→越贪婪 |
| 5 | 避险需求 | **10%** | yfinance: TLT/SPY 20d变化 | TLT 跑赢 SPY→恐惧, 跑输→贪婪 |
| 6 | 垃圾债需求 | **10%** | yfinance: HYG/LQD 比率 | HYG 跑赢 LQD→贪婪(风险偏好) |
| 7 | VIX 期限结构 | **15%** | yfinance: ^VIX/^VIX3M | Contango→贪婪, Backwardation→恐惧 |

### A 股 (A-Share Market) — 5 组件

| # | Component | Weight | Data Source | Scoring Logic |
|---|-----------|--------|-------------|---------------|
| 1 | 融资余额变化 | **25%** | AKShare: 融资融券 | 余额增长→贪婪, 下降→恐惧 |
| 2 | 换手率 | **20%** | AKShare: 市场换手 | 高换手→贪婪, 低换手→恐惧 |
| 3 | 涨跌比 | **20%** | AKShare: 涨跌家数 | 涨多跌少→贪婪, 跌多涨少→恐惧 |
| 4 | 北向资金 | **20%** | AKShare: 沪深港通 | 净流入→贪婪, 净流出→恐惧 |
| 5 | 市场波动 | **15%** | AKShare / WebSearch | 近期波动大→恐惧, 稳定→贪婪 |

### 港股 (HK Market) — 4 组件

| # | Component | Weight | Data Source | Scoring Logic |
|---|-----------|--------|-------------|---------------|
| 1 | VHSI 恒指波动率 | **30%** | yfinance / WebSearch | 类似 VIX 逻辑 |
| 2 | 南向资金 | **25%** | AKShare: 港股通 | 净流入→贪婪, 净流出→恐惧 |
| 3 | 成交额变化 | **25%** | AKShare / WebSearch | 放量→贪婪, 缩量→恐惧 |
| 4 | AH 溢价指数 | **20%** | AKShare / WebSearch | 溢价扩大→A股贪婪/港股恐惧 |

### 加密货币 (Crypto) — 4 组件

| # | Component | Weight | Data Source | Scoring Logic |
|---|-----------|--------|-------------|---------------|
| 1 | Alternative.me 指数 | **30%** | WebSearch / API | 直接引用 0-100 指数 |
| 2 | 资金费率 | **25%** | Binance/OKX API | 正费率高→贪婪, 负费率→恐惧 |
| 3 | BTC 主导率变化 | **25%** | Binance / WebSearch | 主导率上升→恐惧(避险), 下降→贪婪 |
| 4 | 价格动量 | **20%** | Binance: BTC 30d/90d | BTC 上涨→贪婪, 下跌→恐惧 |

---

## Score Zones (0 = Extreme Fear, 100 = Extreme Greed)

| Score | Zone | 中文 | Guidance |
|-------|------|------|----------|
| 80-100 | Extreme Greed | 极度贪婪 | 警惕回调，考虑减仓或对冲 |
| 60-79 | Greed | 贪婪 | 保持仓位，设好止损 |
| 40-59 | Neutral | 中性 | 信号混合，可择机建仓 |
| 20-39 | Fear | 恐惧 | 关注优质标的，分批建仓 |
| 0-19 | Extreme Fear | 极度恐惧 | 逆向布局，长期机会 |

> **巴菲特法则:** "别人恐惧时贪婪，别人贪婪时恐惧" — 极端值往往是反向信号

---

## 全市场综合指数

当 `--market all` (默认) 时，各市场按权重合成全球贪恐指数：

| Market | Weight | Rationale |
|--------|--------|-----------|
| US | 45% | 全球最大资本市场 |
| A-Share | 25% | 全球第二大股票市场 |
| HK | 15% | 亚洲国际金融中心 |
| Crypto | 15% | 风险偏好风向标 |

---

## 数据补全（Web Search Fallback）

当脚本输出包含 `---SEARCH_NEEDED---` 标记时：

1. 解析标记块中的 `component` 和 `search` 字段
2. 对每个缺失指标执行 **WebSearch**，提取最新数值
3. 用搜索到的数据重新计算该组件评分（参考上方评分规则）
4. 在报告中标注 **[搜索补全]** 以区分数据来源

示例标记：
```
---SEARCH_NEEDED---
component: CBOE Put/Call Ratio
search: CBOE equity put call ratio today
---
```

---

## 语言与输出规则

### 中文输出
- 所有分析报告、摘要、建议使用**中文**输出
- 保留英文的情况：ticker 代码（^VIX, SPY）、专有名词首次出现时附英文（贪恐指数 Fear & Greed Index）、数据源名称
- 数字格式：使用国际通用格式（1,234.56）

### Dashboard JSON 输出（可选）
当用户请求 dashboard 格式时，在报告末尾额外输出 Recharts 兼容 JSON：
```json
{
  "title": "多市场贪恐指数",
  "generated_at": "ISO8601时间戳",
  "charts": [
    {"id": "gauge", "type": "bar", "title": "各市场贪恐指数", "data": [...], "xKey": "market", "yKeys": ["score"]},
    {"id": "components", "type": "bar", "title": "组件评分", "data": [...], "xKey": "component", "yKeys": ["score"]}
  ],
  "metrics": [
    {"label": "全球贪恐指数", "value": 65, "trend": "up"},
    {"label": "美股", "value": 72, "trend": "up"},
    {"label": "A股", "value": 45, "trend": "flat"}
  ],
  "summary": "一句话结论"
}
```
保存为 `reports/fear_greed_dashboard_YYYYMMDD.json`
