---
name: trade-journal
description: Trade journal for logging entries/exits, per-trade review scoring (entry quality, execution, management, result), and statistical analysis (win rate, profit factor, by-strategy, monthly). YAML persistence to reports/trades/. Use when user asks to log a trade, review past trades, or analyze trading performance. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Trade Journal

## Overview

交易日志系统，支持记录、复盘和统计分析三大功能。所有交易记录以 YAML 格式持久化到 `reports/trades/` 目录。

**三种操作模式**:
- **log**: 记录新交易（开仓/平仓）
- **review**: 逐笔复盘评分（进场质量/执行/管理/结果，各 1-5 分）
- **stats**: 统计分析（胜率/盈亏比/按策略/按月度）

## When to Use

- 用户开仓时记录交易计划和论点
- 平仓后记录结果
- 定期复盘评估交易质量
- 查看交易统计（胜率、盈亏比、哪个策略最赚钱）
- 与 thesis-tracker 配合：thesis-tracker 跟踪投资论点，trade-journal 记录具体交易

## Prerequisites

- No API keys required
- Python 3.9+ (标准库即可运行，有 PyYAML 更好)
- `pip install pyyaml`（可选，无 PyYAML 时使用内置简易解析器）

## Workflow

### Step 1: Log Trade (开仓记录)

```bash
# 记录新开仓
python3 skills/trade-journal/scripts/trade_journal.py log \
  --ticker AAPL --entry-price 175 --size 100 \
  --strategy "breakout" --thesis "VCP breakout on earnings beat" \
  --tags "tech,momentum"

# 做空记录
python3 skills/trade-journal/scripts/trade_journal.py log \
  --ticker TSLA --entry-price 250 --size 50 --direction short \
  --strategy "breakdown" --thesis "Head & shoulders breakdown"

# 开仓同时记录平仓（已完成交易）
python3 skills/trade-journal/scripts/trade_journal.py log \
  --ticker MSFT --entry-price 400 --size 80 --entry-date 2026-03-01 \
  --exit-price 420 --exit-date 2026-03-10 --strategy "swing"
```

交易保存到 `reports/trades/{TICKER}_{ENTRY_DATE}.yaml`

### Step 2: Close Trade (平仓)

```bash
python3 skills/trade-journal/scripts/trade_journal.py close \
  --ticker AAPL --entry-date 2026-03-01 \
  --exit-price 190 --exit-date 2026-03-15
```

自动计算盈亏金额和百分比。

### Step 3: Review Trade (复盘)

```bash
python3 skills/trade-journal/scripts/trade_journal.py review \
  --ticker AAPL --entry-date 2026-03-01 \
  --entry-quality 4 --execution 3 --management 4 --result-score 5 \
  --review-notes "Entry timing good, could have sized up"
```

**评分维度 (1-5)**:
| 维度 | 1 分 | 3 分 | 5 分 |
|------|------|------|------|
| 进场质量 | 追高/无计划 | 有计划但时机一般 | 完美时机+明确计划 |
| 执行 | 偏离计划 | 基本按计划 | 严格执行 |
| 管理 | 无止损/过早平仓 | 基本风控 | 完善的止损/加仓/减仓 |
| 结果 | 大幅亏损 | 小赚小亏 | 显著盈利 |

### Step 4: Statistics (统计)

```bash
# 生成完整统计报告
python3 skills/trade-journal/scripts/trade_journal.py stats

# 仅 JSON 输出
python3 skills/trade-journal/scripts/trade_journal.py stats --format json

# 保存报告
python3 skills/trade-journal/scripts/trade_journal.py stats --output reports/stats.json
```

**统计内容**:
- 总体：胜率、盈亏比、利润因子、总盈亏
- 按策略：每种策略的胜率和盈亏
- 按月度：月度表现趋势
- 最近交易：最近 10 笔交易明细
- 复盘均值：各评分维度的平均分

## YAML Schema

```yaml
ticker: AAPL
direction: long
entry_date: "2026-03-01"
entry_price: 175.0
exit_date: "2026-03-15"
exit_price: 190.0
size: 100
strategy: breakout
thesis: "VCP breakout on earnings beat"
status: closed
pnl: 1500.0
pnl_pct: 8.57
tags: [tech, momentum]
lessons: "Should have added on first pullback"
review:
  entry_quality: 4
  execution: 3
  management: 4
  result_score: 5
  avg_score: 4.0
  notes: "Entry timing good, could have sized up"
  reviewed_at: "2026-03-16T10:30:00"
```

## Combining with Other Skills

**完整交易闭环**:
1. `idea-generator` / `canslim-screener` → 发现候选标的
2. `fundamentals` + `technical-analysis` → 分析确认
3. `position-sizer` → 计算仓位
4. `stop-loss-manager` → 设置止损/止盈
5. **`trade-journal log`** → 记录交易计划
6. **`trade-journal close`** → 平仓记录
7. **`trade-journal review`** → 复盘评分
8. **`trade-journal stats`** → 定期统计分析
9. `trade-hypothesis-ideator` → 基于交易日志生成新假设

**与 thesis-tracker 的区别**:
- `thesis-tracker`: 跟踪投资论点的有效性（长期持仓管理）
- `trade-journal`: 记录具体交易的进出场和执行质量（交易复盘）

## Resources

### scripts/trade_journal.py

主脚本：
- 4 种操作：log, close, review, stats
- YAML 持久化（支持 PyYAML / 内置简易解析器）
- 盈亏自动计算（支持多/空方向）
- 统计分析（胜率/盈亏比/利润因子/按策略/按月度）
- JSON + Markdown 双格式输出
- 无外部依赖（仅标准库，PyYAML 可选）

---

**提示**: 建议每笔交易平仓后 24 小时内完成复盘，避免记忆偏差。定期（每周/每月）运行 stats 检查交易系统是否持续有效。

---

## 语言与输出规则

### 中文输出
- 所有分析报告、摘要、建议使用**中文**输出
- 保留英文的情况：ticker 代码（AAPL, 600519.SH）、专有名词首次出现时附英文（胜率 Win Rate）、数据源名称
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
