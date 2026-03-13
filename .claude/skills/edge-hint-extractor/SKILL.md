---
name: edge-hint-extractor
description: Extract edge hints from daily market observations and news reactions, with optional LLM ideation, and output canonical hints.yaml for downstream concept synthesis and auto detection. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Edge Hint Extractor

## Overview

Convert raw observation signals (`market_summary`, `anomalies`, `news reactions`) into structured edge hints.
This skill is the first stage in the split workflow: `observe -> abstract -> design -> pipeline`.

## When to Use

- You want to turn daily market observations into reusable hint objects.
- You want LLM-generated ideas constrained by current anomalies/news context.
- You need a clean `hints.yaml` input for concept synthesis or auto detection.

## Prerequisites

- Python 3.9+
- `PyYAML`
- Optional inputs from detector run:
  - `market_summary.json`
  - `anomalies.json`
  - `news_reactions.csv` or `news_reactions.json`

## Output

- `hints.yaml` containing:
  - `hints` list
  - generation metadata
  - rule/LLM hint counts

## Workflow

1. Gather observation files (`market_summary`, `anomalies`, optional news reactions).
2. Run `scripts/build_hints.py` to generate deterministic hints.
3. Optionally augment hints with LLM ideas via one of two methods:
   - a. `--llm-ideas-cmd` — pipe data to an external LLM CLI (subprocess).
   - b. `--llm-ideas-file PATH` — load pre-written hints from a YAML file (for Claude Code workflows where Claude generates hints itself).
4. Pass `hints.yaml` into concept synthesis or auto detection.

Note: `--llm-ideas-cmd` and `--llm-ideas-file` are mutually exclusive.

## Quick Commands

Rule-based only (default output to `reports/edge_hint_extractor/hints.yaml`):

```bash
python3 skills/edge-hint-extractor/scripts/build_hints.py \
  --market-summary /tmp/edge-auto/market_summary.json \
  --anomalies /tmp/edge-auto/anomalies.json \
  --news-reactions /tmp/news_reactions.csv \
  --as-of 2026-02-20 \
  --output-dir reports/
```

Rule + LLM augmentation (external CLI):

```bash
python3 skills/edge-hint-extractor/scripts/build_hints.py \
  --market-summary /tmp/edge-auto/market_summary.json \
  --anomalies /tmp/edge-auto/anomalies.json \
  --llm-ideas-cmd "python3 /path/to/llm_ideas_cli.py" \
  --output-dir reports/
```

Rule + LLM augmentation (pre-written file, for Claude Code):

```bash
python3 skills/edge-hint-extractor/scripts/build_hints.py \
  --market-summary /tmp/edge-auto/market_summary.json \
  --anomalies /tmp/edge-auto/anomalies.json \
  --llm-ideas-file /tmp/llm_hints.yaml \
  --output-dir reports/
```

## Resources

- `skills/edge-hint-extractor/scripts/build_hints.py`
- `references/hints_schema.md`


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
