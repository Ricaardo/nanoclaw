---
name: dividend-screener
description: 股息股筛选器（双模式）。Growth 模式：12%+ 股息 CAGR + RSI 超卖回调入场；Value 模式：P/E<20 + P/B<2 + 3%+ 股息率价值筛选。两种模式均支持 FINVIZ 两阶段预筛选以节省 FMP API 配额。当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Dividend Screener（股息股筛选器）

## Overview

双模式股息股筛选工具，合并原 `dividend-growth-pullback-screener` 和 `value-dividend-screener`：

| 模式 | 核心逻辑 | 适用场景 | 脚本 |
|------|---------|---------|------|
| **Growth** | 12%+ 股息 CAGR + RSI ≤40 超卖 | 低起始收益率、高增长复利，择时入场 | `screen_dividend_growth_rsi.py` |
| **Value** | P/E<20 + P/B<2 + 3%+ 股息率 | 当前高收益 + 合理估值 + 稳定增长 | `screen_dividend_stocks.py` |

两种模式均支持 **FINVIZ Elite + FMP 两阶段筛选**（推荐），可将 FMP API 调用量降低 60-94%。

## When to Use

**Growth 模式**（运行 `screen_dividend_growth_rsi.py`）：
- 寻找股息 CAGR 12%+ 的高增长复利股
- 市场回调 / 板块轮动时抄底优质股息成长股
- 愿意接受 1.5-3% 低起始收益率，看重 5-10 年总回报
- 关键词：「股息增长回调」「RSI 超卖股息股」「dividend growth pullback」

**Value 模式**（运行 `screen_dividend_stocks.py`）：
- 寻找当前高收益（3%+）+ 合理估值的收入型股票
- 构建稳定现金流的股息组合
- 需要严格价值过滤（P/E、P/B）
- 关键词：「高股息价值股」「dividend income」「价值股息筛选」

**Do NOT use when：**
- Growth 模式不适合需要即时高收益（>3%）的场景 → 用 Value 模式
- Value 模式不适合寻找低收益高增长的场景 → 用 Growth 模式
- 短期交易（<6 个月）→ 用 `scanner-bullish` 或 `technical-analyst`

## Workflow

### Step 1: Set API Keys

```bash
# 推荐：FINVIZ + FMP 两阶段
export FMP_API_KEY=your_fmp_key_here
export FINVIZ_API_KEY=your_finviz_key_here

# 最低要求：仅 FMP（配额受限，建议 --max-candidates 40）
export FMP_API_KEY=your_fmp_key_here
```

### Step 2: Execute Screening

#### Growth 模式（股息增长 + RSI 回调）

```bash
cd /path/to/dividend-screener/scripts

# 两阶段（推荐）
python3 screen_dividend_growth_rsi.py --use-finviz

# FMP-only
python3 screen_dividend_growth_rsi.py --max-candidates 40

# 自定义参数
python3 screen_dividend_growth_rsi.py --use-finviz --min-yield 2.0 --min-div-growth 15.0 --rsi-max 35
```

**筛选逻辑：**
1. 股息率 ≥ 1.5%，市值 ≥ $2B，NYSE/NASDAQ
2. 3 年股息 CAGR ≥ 12%，无削减历史，派息率 < 100%
3. 正向营收/EPS 增长，D/E < 2.0，流动比率 > 1.0
4. 14 日 RSI ≤ 40（超卖/回调入场信号）
5. 综合评分：股息增长 40% + 财务质量 30% + 技术面 20% + 估值 10%

**输出：**
- `dividend_growth_pullback_results_YYYY-MM-DD.json`
- `dividend_growth_pullback_screening_YYYY-MM-DD.md`

#### Value 模式（价值 + 高股息）

```bash
cd /path/to/dividend-screener/scripts

# 两阶段（推荐）
python3 screen_dividend_stocks.py --use-finviz

# FMP-only
python3 screen_dividend_stocks.py

# 自定义
python3 screen_dividend_stocks.py --use-finviz --top 50
```

**筛选逻辑：**
1. 股息率 ≥ 3%，P/E ≤ 20，P/B ≤ 2，中盘以上
2. 3 年股息 CAGR ≥ 5%，营收/EPS 正增长
3. 派息可持续性（FCF 覆盖率）、财务健康度（D/E、流动比率）
4. 质量评分（ROE、净利率）
5. 综合评分排名

**输出：**
- `dividend_screener_results.json`

### Step 3: Analyze Results

**Growth 模式关注指标：**
- 股息 CAGR（12%+ = 6 年翻倍）
- RSI 水平（<30 极度超卖，30-40 早期回调）
- 入场时机建议（分批建仓 vs 一次性入场）

**Value 模式关注指标：**
- 当前股息率（3%+ 即时收入）
- 估值水平（P/E、P/B 安全边际）
- 股息可持续性（派息率、FCF 覆盖率）

### Step 4: Generate Report

两种模式均生成包含以下内容的分析报告：
- 排名表（综合评分排序）
- 逐股详细分析（估值/增长/可持续性/财务健康）
- 投资建议与风险因素
- 组合构建指引（分散化、仓位管理）

### Step 5: Follow-up

常见后续问题处理：
- 「某股为何未入选？」→ 检查具体未通过的筛选条件
- 「能否按行业筛选？」→ 脚本支持行业过滤参数
- 「多久重新筛选？」→ 建议每季度（配合财报周期）
- 「该买多少只？」→ 股息组合建议 10-15 只，注意行业分散

## RSI 解读指南（Growth 模式专用）

| RSI 区间 | 含义 | 建议 |
|---------|------|------|
| 25-30 | 极度超卖，可能恐慌抛售 | 等 RSI 回升再入场，先建 50% 仓位 |
| 30-35 | 强势回调 | 可立即建仓，止损 5-8% |
| 35-40 | 轻度回调 | 保守入场，止损 3-5% |

## 股息增长复利示例

| CAGR | 起始收益率 | 第 6 年成本收益率 | 第 12 年成本收益率 |
|------|-----------|----------------|-----------------|
| 12% | 1.5% | 2.96% (2x) | 5.85% (4x) |
| 15% | 1.8% | 4.08% (2.3x) | 9.22% (5.1x) |
| 20% | 2.0% | 6.00% (3x) | 18.0% (9x) |

**核心观点：** 低起始收益率 + 高增长 > 高起始收益率 + 低增长（10 年以上）。

## Troubleshooting

### 通用问题
- **`requests` 库缺失** → `pip install requests`
- **FMP API Key 未设置** → `export FMP_API_KEY=your_key`
- **API 配额超限** → 使用 FINVIZ 两阶段，或等待次日 UTC 零点重置
- **无结果** → 放宽条件（降低收益率/增长率门槛，或提高 RSI 上限）

### Growth 模式特有
- **RSI 数据不足** → 上市不足 30 天的股票自动跳过
- **参数调节** → `--rsi-max 45`（放宽）、`--min-div-growth 10.0`（降低门槛）

### Value 模式特有
- **FINVIZ 认证失败** → 确认 Elite 订阅有效，检查 API Key
- **运行缓慢** → 正常行为（0.3s/请求限速），100 只约 8-10 分钟

## Combining with Other Skills

**筛选前：**
- `market-news-analyst` → 识别板块轮动/市场回调
- `market-breadth-analyzer` → 确认大盘超卖
- `economic-calendar-fetcher` → 检查即将发布的宏观事件

**筛选后：**
- `technical-analyst` → 对候选股进行图表分析
- `us-stock-analysis` → 个股深度研究
- `backtest-expert` → 回测策略历史表现
- `position-sizer` → 确定仓位大小

## Resources

### scripts/

- **screen_dividend_growth_rsi.py** — Growth 模式筛选脚本
  - FMP API 基本面数据 + 14 日 RSI 计算
  - 多阶段过滤 + 综合评分排名
  - 输出 JSON + Markdown 报告

- **screen_dividend_stocks.py** — Value 模式筛选脚本
  - FMP API 多阶段筛选（估值/增长/可持续性）
  - CAGR 计算、FCF 覆盖率分析
  - 综合评分排名，输出 JSON

### references/

- **rsi_oversold_strategy.md** — RSI 超卖策略详解（指标原理/误判管理/风险控制）
- **dividend_growth_compounding.md** — 股息增长复利数学（CAGR 示例/历史案例）
- **screening_methodology.md** — Value 模式筛选方法论（三阶段过滤/评分体系/投资哲学）
- **fmp_api_guide.md** — FMP API 使用指南（端点/限速/错误处理）

---

**Disclaimer:** 本筛选工具仅供信息参考。过去的股息增长不保证未来表现。投资决策前请进行充分的尽职调查。RSI 超卖不保证价格反转——股票可能在超卖区间持续较长时间。

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
