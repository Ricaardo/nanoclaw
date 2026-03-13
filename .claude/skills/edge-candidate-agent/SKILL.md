---
name: edge-candidate-agent
description: Generate and prioritize US equity long-side edge research tickets from EOD observations, then export pipeline-ready candidate specs for trade-strategy-pipeline Phase I. Use when users ask to turn hypotheses/anomalies into reproducible research tickets, convert validated ideas into `strategy.yaml` + `metadata.json`, or preflight-check interface compatibility (`edge-finder-candidate/v1`) before running pipeline backtests. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Edge Candidate Agent

## Overview

Convert daily market observations into reproducible research tickets and Phase I-compatible candidate specs.
Prioritize signal quality and interface compatibility over aggressive strategy proliferation.
This skill can run end-to-end standalone, but in the split workflow it primarily serves the final export/validation stage.

## When to Use

- Convert market observations, anomalies, or hypotheses into structured research tickets.
- Run daily auto-detection to discover new edge candidates from EOD OHLCV and optional hints.
- Export validated tickets as `strategy.yaml` + `metadata.json` for `trade-strategy-pipeline` Phase I.
- Run preflight compatibility checks for `edge-finder-candidate/v1` before pipeline execution.

## Prerequisites

- Python 3.9+ with `PyYAML` installed.
- Access to the target `trade-strategy-pipeline` repository for schema/stage validation.
- `uv` available when running pipeline-managed validation via `--pipeline-root`.

## Output

- `strategies/<candidate_id>/strategy.yaml`: Phase I-compatible strategy spec.
- `strategies/<candidate_id>/metadata.json`: provenance metadata including interface version and ticket context.
- Validation status from `scripts/validate_candidate.py` (pass/fail + reasons).
- Daily detection artifacts:
  - `daily_report.md`
  - `market_summary.json`
  - `anomalies.json`
  - `watchlist.csv`
  - `tickets/exportable/*.yaml`
  - `tickets/research_only/*.yaml`

## Position in Split Workflow

Recommended split workflow:

1. `skills/edge-hint-extractor`: observations/news -> `hints.yaml`
2. `skills/edge-concept-synthesizer`: tickets/hints -> `edge_concepts.yaml`
3. `skills/edge-strategy-designer`: concepts -> `strategy_drafts` + exportable ticket YAML
4. `skills/edge-candidate-agent` (this skill): export + validate for pipeline handoff

## Workflow

1. Run auto-detection from EOD OHLCV:
   - `skills/edge-candidate-agent/scripts/auto_detect_candidates.py`
   - Optional: `--hints` for human ideation input
   - Optional: `--llm-ideas-cmd` for external LLM ideation loop
2. Load the contract and mapping references:
   - `references/pipeline_if_v1.md`
   - `references/signal_mapping.md`
   - `references/research_ticket_schema.md`
   - `references/ideation_loop.md`
3. Build or update a research ticket using `references/research_ticket_schema.md`.
4. Export candidate artifacts with `skills/edge-candidate-agent/scripts/export_candidate.py`.
5. Validate interface and Phase I constraints with `skills/edge-candidate-agent/scripts/validate_candidate.py`.
6. Hand off candidate directory to `trade-strategy-pipeline` and run dry-run first.

## Quick Commands

Daily auto-detection (with optional export/validation):

```bash
python3 skills/edge-candidate-agent/scripts/auto_detect_candidates.py \
  --ohlcv /path/to/ohlcv.parquet \
  --output-dir reports/edge_candidate_auto \
  --top-n 10 \
  --hints path/to/hints.yaml \
  --export-strategies-dir /path/to/trade-strategy-pipeline/strategies \
  --pipeline-root /path/to/trade-strategy-pipeline
```

Create a candidate directory from a ticket:

```bash
python3 skills/edge-candidate-agent/scripts/export_candidate.py \
  --ticket path/to/ticket.yaml \
  --strategies-dir /path/to/trade-strategy-pipeline/strategies
```

Validate interface contract only:

```bash
python3 skills/edge-candidate-agent/scripts/validate_candidate.py \
  --strategy /path/to/trade-strategy-pipeline/strategies/my_candidate_v1/strategy.yaml
```

Validate both interface contract and pipeline schema/stage rules:

```bash
python3 skills/edge-candidate-agent/scripts/validate_candidate.py \
  --strategy /path/to/trade-strategy-pipeline/strategies/my_candidate_v1/strategy.yaml \
  --pipeline-root /path/to/trade-strategy-pipeline \
  --stage phase1
```

## Export Rules

- Keep `validation.method: full_sample`.
- Keep `validation.oos_ratio` omitted or `null`.
- Export only supported entry families for v1:
  - `pivot_breakout` with `vcp_detection`
  - `gap_up_continuation` with `gap_up_detection`
- Mark unsupported hypothesis families as research-only in ticket notes, not as export candidates.

## Guardrails

- Reject candidates that violate schema bounds (risk, exits, empty conditions).
- Reject candidate when folder name and `id` mismatch.
- Require deterministic metadata with `interface_version: edge-finder-candidate/v1`.
- Use `--dry-run` in pipeline before full execution.

## Resources

### `skills/edge-candidate-agent/scripts/export_candidate.py`
Generate `strategies/<candidate_id>/strategy.yaml` and `metadata.json` from a research ticket YAML.

### `skills/edge-candidate-agent/scripts/validate_candidate.py`
Run interface checks and optional `StrategySpec`/`validate_spec` checks against `trade-strategy-pipeline`.

### `skills/edge-candidate-agent/scripts/auto_detect_candidates.py`
Auto-detect edge ideas from EOD OHLCV, generate exportable/research tickets, and optionally export/validate automatically.

### `references/pipeline_if_v1.md`
Condensed integration contract for `edge-finder-candidate/v1`.

### `references/signal_mapping.md`
Map hypothesis families to currently exportable signal families.

### `references/research_ticket_schema.md`
Ticket schema used by `export_candidate.py`.

### `references/ideation_loop.md`
Hint schema and external LLM ideation command contract.


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
