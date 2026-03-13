---
name: strategy-pivot-designer
description: Detect backtest iteration stagnation and generate structurally different strategy pivot proposals when parameter tuning reaches a local optimum. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Strategy Pivot Designer

## Overview

Detect when a strategy's backtest iteration loop has stalled and propose structurally different strategy architectures. This skill acts as the feedback loop for the Edge pipeline (hint-extractor -> concept-synthesizer -> strategy-designer -> candidate-agent), breaking out of local optima by redesigning the strategy's skeleton rather than tweaking parameters.

## When to Use

- Backtest scores have plateaued despite multiple refinement iterations.
- A strategy shows signs of overfitting (high in-sample, low robustness).
- Transaction costs defeat the strategy's thin edge.
- Tail risk or drawdown exceeds acceptable thresholds.
- You want to explore fundamentally different strategy architectures for the same market hypothesis.

## Prerequisites

- Python 3.9+
- `PyYAML`
- Iteration history JSON (accumulated backtest-expert evaluations)
- Source strategy draft YAML (from edge-strategy-designer)

## Output

- `pivot_drafts/research_only/*.yaml` — strategy_draft compatible YAML proposals
- `pivot_drafts/exportable/*.yaml` — export-ready drafts + ticket YAML for candidate-agent
- `pivot_report_*.md` — human-readable pivot analysis
- `pivot_manifest_*.json` — metadata for all generated files
- `pivot_diagnosis_*.json` — stagnation detection results

## Workflow

1. Accumulate backtest evaluation results into an iteration history file using `--append-eval`.
2. Run stagnation detection on the history to identify triggers (plateau, overfitting, cost defeat, tail risk).
3. If stagnation detected, generate pivot proposals using three techniques: assumption inversion, archetype switch, objective reframe.
4. Review ranked proposals (scored by quality potential + novelty).
5. For exportable proposals, ticket YAML is ready for edge-candidate-agent pipeline.
6. For research_only proposals, manual strategy design needed before pipeline integration.
7. Feed the selected pivot draft back into backtest-expert for the next iteration cycle.

## Quick Commands

Append a backtest evaluation to history (creates history if new):

```bash
python3 skills/strategy-pivot-designer/scripts/detect_stagnation.py \
  --append-eval reports/backtest_eval_2026-02-10_120000.json \
  --history reports/iteration_history.json \
  --strategy-id draft_edge_concept_breakout_behavior_riskon_core \
  --changes "Widened stop_loss from 5% to 7%"
```

Detect stagnation:

```bash
python3 skills/strategy-pivot-designer/scripts/detect_stagnation.py \
  --history reports/iteration_history.json \
  --output-dir reports/
```

Generate pivot proposals:

```bash
python3 skills/strategy-pivot-designer/scripts/generate_pivots.py \
  --diagnosis reports/pivot_diagnosis_*.json \
  --strategy reports/edge_strategy_drafts/draft_*.yaml \
  --max-pivots 3 \
  --output-dir reports/
```

## Resources

- `skills/strategy-pivot-designer/scripts/detect_stagnation.py`
- `skills/strategy-pivot-designer/scripts/generate_pivots.py`
- `references/stagnation_triggers.md`
- `references/strategy_archetypes.md`
- `references/pivot_techniques.md`
- `references/pivot_proposal_schema.md`
- `skills/backtest-expert/scripts/evaluate_backtest.py`
- `skills/edge-strategy-designer/scripts/design_strategy_drafts.py`

## 停滞检测逻辑

### 四种停滞触发器

| 触发器 | 检测条件 | 建议转型方向 |
|--------|---------|------------|
| **Plateau** | 连续 3+ 轮迭代，综合评分变化 <2% | 假设反转、目标重构 |
| **Overfitting** | 样本内评分 >80，样本外评分 <40 | 架构切换（规则→统计→ML） |
| **Cost Defeat** | 扣除交易成本后收益 <0 | 降频交易、增大仓位、换品种 |
| **Tail Risk** | 最大回撤 >设定阈值，或尾部损失超预期 | 增加对冲腿、切换到非对称策略 |

### 状态转换图

```
[初始策略] → backtest-expert 评估
     ↓
[迭代历史] → detect_stagnation.py
     ↓
  ┌─ 未停滞 → 继续参数优化
  └─ 停滞 → generate_pivots.py
              ↓
         [转型提案] → 三种技术:
              ├─ 假设反转 (Assumption Inversion)
              ├─ 架构切换 (Archetype Switch)
              └─ 目标重构 (Objective Reframe)
              ↓
         [排名评分] → quality_potential × novelty
              ↓
         [导出] → research_only/ 或 exportable/
```

### 输入 JSON Schema

```json
{
  "strategy_id": "draft_xxx",
  "iterations": [
    {
      "iteration": 1,
      "date": "2026-03-01",
      "changes": "Initial parameters",
      "scores": {
        "in_sample_sharpe": 1.8,
        "out_sample_sharpe": 0.9,
        "max_drawdown_pct": -15.2,
        "win_rate": 0.55,
        "profit_factor": 1.4,
        "net_after_costs": 0.02
      }
    }
  ]
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
