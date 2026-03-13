---
name: edge-pipeline-orchestrator
description: Orchestrate the full edge research pipeline from candidate detection through strategy design, review, revision, and export. Use when coordinating multi-stage edge research workflows end-to-end. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Edge Pipeline Orchestrator

Coordinate all edge research stages into a single automated pipeline run.

## When to Use

- Run the full edge pipeline from tickets (or OHLCV) to exported strategies
- Resume a partially completed pipeline from the drafts stage
- Review and revise existing strategy drafts with feedback loop
- Dry-run the pipeline to preview results without exporting

## Workflow

1. Load pipeline configuration from CLI arguments
2. Run auto_detect stage if --from-ohlcv is provided (generates tickets from raw OHLCV data)
3. Run hints stage to extract edge hints from market summary and anomalies
4. Run concepts stage to synthesize abstract edge concepts from tickets and hints
5. Run drafts stage to design strategy drafts from concepts
6. Run review-revision feedback loop:
   - Review all drafts (max 2 iterations)
   - PASS verdicts accumulated; REJECT verdicts accumulated
   - REVISE verdicts trigger apply_revisions and re-review
   - Remaining REVISE after max iterations downgraded to research_probe
7. Export eligible drafts (PASS + export_ready_v1 + exportable entry_family)
8. Write pipeline_run_manifest.json with full execution trace

## CLI Usage

```bash
# Full pipeline from tickets
python3 scripts/orchestrate_edge_pipeline.py \
  --tickets-dir path/to/tickets/ \
  --output-dir reports/edge_pipeline/

# Full pipeline from OHLCV
python3 scripts/orchestrate_edge_pipeline.py \
  --from-ohlcv path/to/ohlcv.csv \
  --output-dir reports/edge_pipeline/

# Resume from drafts stage
python3 scripts/orchestrate_edge_pipeline.py \
  --resume-from drafts \
  --drafts-dir path/to/drafts/ \
  --output-dir reports/edge_pipeline/

# Review-only mode
python3 scripts/orchestrate_edge_pipeline.py \
  --review-only \
  --drafts-dir path/to/drafts/ \
  --output-dir reports/edge_pipeline/

# Dry run (no export)
python3 scripts/orchestrate_edge_pipeline.py \
  --tickets-dir path/to/tickets/ \
  --output-dir reports/edge_pipeline/ \
  --dry-run
```

## Output

All artifacts are written to `--output-dir`:

```
output-dir/
├── pipeline_run_manifest.json
├── tickets/          (from auto_detect)
├── hints/hints.yaml  (from hints)
├── concepts/edge_concepts.yaml
├── drafts/*.yaml
├── exportable_tickets/*.yaml
├── reviews_iter_0/*.yaml
├── reviews_iter_1/*.yaml  (if needed)
└── strategies/<candidate_id>/
    ├── strategy.yaml
    └── metadata.json
```

## Claude Code LLM-Augmented Workflow

Run the LLM-augmented pipeline entirely within Claude Code:

1. Run auto_detect to produce `market_summary.json` + `anomalies.json`
2. Claude Code analyzes data and generates edge hints
3. Save hints to a YAML file:

```yaml
- title: Sector rotation into industrials
  observation: Tech underperforming while industrials show relative strength
  symbols: [CAT, DE, GE]
  regime_bias: Neutral
  mechanism_tag: flow
  preferred_entry_family: pivot_breakout
  hypothesis_type: sector_x_stock
```

4. Run orchestrator with `--llm-ideas-file` and `--promote-hints`:

```bash
python3 scripts/orchestrate_edge_pipeline.py \
  --tickets-dir path/to/tickets/ \
  --llm-ideas-file llm_hints.yaml \
  --promote-hints \
  --as-of 2026-02-28 \
  --max-synthetic-ratio 1.5 \
  --strict-export \
  --output-dir reports/edge_pipeline/
```

### Optional Flags

- `--as-of YYYY-MM-DD` — forwarded to hints stage for date filtering
- `--strict-export` — export-eligible drafts with any warn finding get REVISE instead of PASS
- `--max-synthetic-ratio N` — cap synthetic tickets to N × real ticket count (floor: 3)
- `--overlap-threshold F` — condition overlap threshold for concept deduplication (default: 0.75)
- `--no-dedup` — disable concept deduplication

Note: `--llm-ideas-file` and `--promote-hints` are effective only during full pipeline runs.
`--resume-from drafts` and `--review-only` skip hints/concepts stages, so these flags are ignored.

## Resources

- `references/pipeline_flow.md` — Pipeline stages, data contracts, and architecture
- `references/revision_loop_rules.md` — Review-revision feedback loop rules and heuristics


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
