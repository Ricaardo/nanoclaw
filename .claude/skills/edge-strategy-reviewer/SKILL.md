---
name: edge-strategy-reviewer
description: >
  Critically review strategy drafts from edge-strategy-designer for edge
  plausibility, overfitting risk, sample size adequacy, and execution realism.
  Use when strategy_drafts/*.yaml exists and needs quality gate before pipeline
  export. Outputs PASS/REVISE/REJECT verdicts with confidence scores.

  当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。---

# Edge Strategy Reviewer

Deterministic quality gate for strategy drafts produced by `edge-strategy-designer`.

## When to Use

- After `edge-strategy-designer` generates `strategy_drafts/*.yaml`
- Before exporting drafts to `edge-candidate-agent` via the pipeline
- When manually validating a draft strategy for edge plausibility

## Prerequisites

- Strategy draft YAML files (output of `edge-strategy-designer`)
- Python 3.10+ with PyYAML

## Workflow

1. Load draft YAML files from `--drafts-dir` or a single `--draft` file
2. Evaluate each draft against 8 criteria (C1-C8) with weighted scoring
3. Compute confidence score (weighted average of all criteria)
4. Determine verdict: PASS / REVISE / REJECT
5. Assess export eligibility (PASS + export_ready_v1 + exportable family)
6. Write review output (YAML or JSON) and optional markdown summary

## Review Criteria

| # | Criterion | Weight | Key Checks |
|---|-----------|--------|------------|
| C1 | Edge Plausibility | 20 | Thesis quality, domain terms, mechanism keywords (continuous 50-95) |
| C2 | Overfitting Risk | 20 | 5-tier filter count scoring (90/80/60/40/10), precise threshold penalty |
| C3 | Sample Adequacy | 15 | Continuous scoring from estimated annual opportunities (10-95) |
| C4 | Regime Dependency | 10 | Cross-regime validation |
| C5 | Exit Calibration | 10 | Stop-loss, reward-to-risk |
| C6 | Risk Concentration | 10 | Position sizing limits |
| C7 | Execution Realism | 10 | Volume filter, export consistency |
| C8 | Invalidation Quality | 5 | Signal count and specificity |

## Verdict Logic

- C1 or C2 severity=fail → immediate REJECT
- confidence >= 70, no fail findings → PASS
- confidence < 35 → REJECT
- Otherwise → REVISE (with revision instructions)

## Running the Script

```bash
# Review all drafts in a directory
python3 skills/edge-strategy-reviewer/scripts/review_strategy_drafts.py \
  --drafts-dir reports/edge_strategy_drafts/ \
  --output-dir reports/

# Single draft review
python3 skills/edge-strategy-reviewer/scripts/review_strategy_drafts.py \
  --draft reports/edge_strategy_drafts/draft_xxx.yaml \
  --output-dir reports/

# JSON output with markdown summary
python3 skills/edge-strategy-reviewer/scripts/review_strategy_drafts.py \
  --drafts-dir reports/edge_strategy_drafts/ \
  --output-dir reports/ \
  --format json \
  --markdown-summary

# Strict export mode: export-eligible drafts with any warn → REVISE
python3 skills/edge-strategy-reviewer/scripts/review_strategy_drafts.py \
  --drafts-dir reports/edge_strategy_drafts/ \
  --output-dir reports/ \
  --strict-export
```

## Output Format

Primary output: `review.yaml` (or `review.json`)

```yaml
generated_at_utc: "2026-02-28T12:00:00+00:00"
source:
  drafts_dir: "/path/to/strategy_drafts"
  draft_count: 4
summary:
  total: 4
  PASS: 1
  REVISE: 2
  REJECT: 1
  export_eligible: 1
reviews:
  - draft_id: "draft_xxx_core"
    verdict: "PASS"
    confidence_score: 80
    export_eligible: true
    findings: [...]
    revision_instructions: []
```

## Resources

- `references/review_criteria.md` — Detailed scoring rubric for C1-C8
- `references/overfitting_checklist.md` — Overfitting detection heuristics


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
