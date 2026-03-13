---
name: edge-strategy-designer
description: Convert abstract edge concepts into strategy draft variants and optional exportable ticket YAMLs for edge-candidate-agent export/validation. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Edge Strategy Designer

## Overview

Translate concept-level hypotheses into concrete strategy draft specs.
This skill sits after concept synthesis and before pipeline export validation.

## When to Use

- You have `edge_concepts.yaml` and need strategy candidates.
- You want multiple variants (core/conservative/research-probe) per concept.
- You want optional exportable ticket files for interface v1 families.

## Prerequisites

- Python 3.9+
- `PyYAML`
- `edge_concepts.yaml` produced by concept synthesis

## Output

- `strategy_drafts/*.yaml`
- `strategy_drafts/run_manifest.json`
- Optional `exportable_tickets/*.yaml` for downstream `export_candidate.py`

## Workflow

1. Load `edge_concepts.yaml`.
2. Choose risk profile (`conservative`, `balanced`, `aggressive`).
3. Generate per-concept variants with hypothesis-type exit calibration.
4. Apply `HYPOTHESIS_EXIT_OVERRIDES` to adjust stop-loss, reward-to-risk, time-stop, and trailing-stop per hypothesis type (breakout, earnings_drift, panic_reversal, etc.).
5. Clamp reward-to-risk at `RR_FLOOR=1.5` to prevent C5 review failures.
6. Export v1-ready ticket YAML when applicable.
7. Hand off exportable tickets to `skills/edge-candidate-agent/scripts/export_candidate.py`.

## Quick Commands

Generate drafts only:

```bash
python3 skills/edge-strategy-designer/scripts/design_strategy_drafts.py \
  --concepts /tmp/edge-concepts/edge_concepts.yaml \
  --output-dir /tmp/strategy-drafts \
  --risk-profile balanced
```

Generate drafts + exportable tickets:

```bash
python3 skills/edge-strategy-designer/scripts/design_strategy_drafts.py \
  --concepts /tmp/edge-concepts/edge_concepts.yaml \
  --output-dir /tmp/strategy-drafts \
  --exportable-tickets-dir /tmp/exportable-tickets \
  --risk-profile conservative
```

## Resources

- `skills/edge-strategy-designer/scripts/design_strategy_drafts.py`
- `references/strategy_draft_schema.md`
- `skills/edge-candidate-agent/scripts/export_candidate.py`


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
