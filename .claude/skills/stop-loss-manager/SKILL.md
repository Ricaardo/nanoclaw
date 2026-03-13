---
name: stop-loss-manager
description: Calculate stop-loss levels (fixed %, ATR, support, volatility percentile), take-profit targets (R:R ratio, Fibonacci extensions), and trailing stop parameters for active trades. Use when user asks about stop-loss placement, take-profit targets, trailing stops, or risk management for open positions. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Stop-Loss Manager

## Overview

计算和管理交易的止损/止盈水平。支持 4 种止损策略和多种止盈方法，输出完整的风险管理参数。

**4 种止损策略**:
- **固定百分比 (fixed)**: 入场价下方固定百分比（默认 5%）
- **ATR 倍数 (atr)**: 入场价 - ATR × 倍数（默认 2x），基于波动率自适应
- **技术支撑位 (support)**: 关键支撑位下方设置缓冲（默认 0.5%）
- **波动百分位 (volatility)**: 基于历史日波动率的统计止损（默认 95 百分位）

**止盈方法**:
- 风险回报比目标（1:2, 1:3）
- 斐波那契扩展（1.618, 2.618）
- 阶梯追踪止损

## When to Use

- 用户询问止损价位设置
- 需要计算止盈目标价
- 设置追踪止损参数
- 评估单笔交易风险金额占账户比例
- 与 position-sizer 配合使用：先算仓位大小，再设止损/止盈

## Prerequisites

- No API keys required
- Python 3.9+ with standard library only

## Workflow

### Step 1: Gather Parameters

从用户收集：
- **必需**: 入场价格 (entry)、持仓数量 (size)、账户总值 (account)
- **策略选择**: fixed / atr / support / volatility
- **策略参数**:
  - fixed: `--stop-pct` 止损百分比（默认 5%）
  - atr: `--atr` ATR 值, `--atr-multiplier` 倍数（默认 2.0）
  - support: `--support` 支撑位价格, `--support-buffer` 缓冲百分比（默认 0.5%）
  - volatility: `--daily-std` 日标准差(%), `--vol-percentile` 百分位（默认 95）

如果用户提供 ticker 但未给价格，先用 stock-quote 获取当前价，用 technical-analysis 获取 ATR 和支撑位。

### Step 2: Execute Script

```bash
# 固定百分比止损（最常用）
python3 skills/stop-loss-manager/scripts/stop_loss_manager.py \
  --strategy fixed --entry 150 --size 100 --account 50000 --stop-pct 5

# ATR 止损（波动率自适应）
python3 skills/stop-loss-manager/scripts/stop_loss_manager.py \
  --strategy atr --entry 150 --size 100 --account 50000 --atr 3.5

# 支撑位止损
python3 skills/stop-loss-manager/scripts/stop_loss_manager.py \
  --strategy support --entry 150 --size 100 --account 50000 --support 142

# 波动百分位止损
python3 skills/stop-loss-manager/scripts/stop_loss_manager.py \
  --strategy volatility --entry 150 --size 100 --account 50000 --daily-std 1.8

# 自定义风险回报比
python3 skills/stop-loss-manager/scripts/stop_loss_manager.py \
  --strategy fixed --entry 150 --size 100 --account 50000 --rr-ratios 1.5 2 3

# 仅输出 JSON
python3 skills/stop-loss-manager/scripts/stop_loss_manager.py \
  --strategy atr --entry 150 --size 100 --account 50000 --atr 3.5 --format json
```

### Step 3: Interpret Results

脚本输出 JSON + Markdown 报告，包含：

**止损信息**:
- stop_price: 止损价格
- stop_distance_pct: 止损距离百分比
- risk_per_share: 每股风险
- risk_amount: 总风险金额
- risk_of_account_pct: 占账户总值百分比

**止盈目标**:
- R:R 1:2 和 1:3 目标价
- Fibonacci 1.618 和 2.618 扩展目标
- 每个目标的预期收益百分比

**追踪止损**:
- 初始止损 → 盈亏平衡 → 锁利的阶梯计划
- ATR 追踪参数（如适用）

### Step 4: Risk Check

检查风险是否合理：
- `risk_of_account_pct` 应 ≤2%（保守）或 ≤5%（积极）
- 如果风险过高，建议用户减少仓位（联动 position-sizer）
- 如果止损距离 >10%，提醒可能需要更紧的止损或更小仓位

## Strategy Selection Guide

| 场景 | 推荐策略 | 理由 |
|------|---------|------|
| 日常交易（默认） | fixed 5% | 简单可靠 |
| 波动性股票 | atr 2x | 自适应波动率 |
| 突破交易 | support | 基于关键价位 |
| 统计驱动 | volatility 95% | 基于历史分布 |
| 财报前持仓 | fixed 8-10% | 预留跳空空间 |

## Combining with Other Skills

**完整交易工作流**:
1. `position-sizer` → 计算仓位大小
2. `stop-loss-manager` → 设置止损/止盈
3. `risk-assessment` → 验证组合风险
4. `trade-journal` → 记录交易计划

**获取输入参数**:
- `technical-analysis` → ATR 值、支撑/阻力位
- `stock-quote` → 当前价格
- `greeks` → 期权交易的 Delta 调整止损

## Resources

### scripts/stop_loss_manager.py

主计算脚本：
- 4 种止损策略实现
- R:R 和 Fibonacci 止盈目标计算
- 阶梯追踪止损生成
- JSON + Markdown 双格式输出
- 无外部依赖（仅标准库）

---

**风险提示**: 止损不保证成交价格。缺口、流动性不足或极端行情可能导致实际止损价格偏离设定值。本工具仅供参考，不构成投资建议。

---

## 语言与输出规则

### 中文输出
- 所有分析报告、摘要、建议使用**中文**输出
- 保留英文的情况：ticker 代码（AAPL, 600519.SH）、专有名词首次出现时附英文（平均真实范围 ATR）、数据源名称
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
