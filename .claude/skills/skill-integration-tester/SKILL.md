---
name: skill-integration-tester
description: Validate multi-skill workflows defined in CLAUDE.md by checking skill existence, inter-skill data contracts (JSON schema compatibility), file naming conventions, and handoff integrity. Use when adding new workflows, modifying skill outputs, or verifying pipeline health before release. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Skill Integration Tester

## Overview

Validate multi-skill workflows defined in CLAUDE.md (Daily Market Monitoring,
Weekly Strategy Review, Earnings Momentum Trading, etc.) by executing each step
in sequence. Check inter-skill data contracts for JSON schema compatibility
between output of step N and input of step N+1, verify file naming conventions,
and report broken handoffs. Supports dry-run mode with synthetic fixtures.

## When to Use

- After adding or modifying a multi-skill workflow in CLAUDE.md
- After changing a skill's output format (JSON schema, file naming)
- Before releasing new skills to verify pipeline compatibility
- When debugging broken handoffs between consecutive workflow steps
- As a CI pre-check for pull requests touching skill scripts

## Prerequisites

- Python 3.9+
- No API keys required
- No third-party Python packages required (uses only standard library)

## Workflow

### Step 1: Run Integration Validation

Execute the validation script against the project's CLAUDE.md:

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --output-dir reports/
```

This parses all `**Workflow Name:**` blocks from the Multi-Skill Workflows
section, resolves each step's display name to a skill directory, and validates
existence, contracts, and naming.

### Step 2: Validate a Specific Workflow

Target a single workflow by name substring:

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --workflow "Earnings Momentum" \
  --output-dir reports/
```

### Step 3: Dry-Run with Synthetic Fixtures

Create synthetic fixture JSON files for each skill's expected output and
validate contract compatibility without real data:

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --dry-run \
  --output-dir reports/
```

Fixture files are written to `reports/fixtures/` with `_fixture` flag set.

### Step 4: Review Results

Open the generated Markdown report for a human-readable summary, or parse
the JSON report for programmatic consumption. Each workflow shows:
- Step-by-step skill existence checks
- Handoff contract validation (PASS / FAIL / N/A)
- File naming convention violations
- Overall workflow status (valid / broken / warning)

### Step 5: Fix Broken Handoffs

For each `FAIL` handoff, verify that:
1. The producer skill's output contains all required fields
2. The consumer skill's input parameter accepts the producer's output format
3. File naming patterns are consistent between producer output and consumer input

## Output Format

### JSON Report

```json
{
  "schema_version": "1.0",
  "generated_at": "2026-03-01T12:00:00+00:00",
  "dry_run": false,
  "summary": {
    "total_workflows": 8,
    "valid": 6,
    "broken": 1,
    "warnings": 1
  },
  "workflows": [
    {
      "workflow": "Daily Market Monitoring",
      "step_count": 4,
      "status": "valid",
      "steps": [...],
      "handoffs": [...],
      "naming_violations": []
    }
  ]
}
```

### Markdown Report

Structured report with per-workflow sections showing step validation,
handoff status, and naming violations.

Reports are saved to `reports/` with filenames
`integration_test_YYYY-MM-DD_HHMMSS.{json,md}`.

## Resources

- `scripts/validate_workflows.py` -- Main validation script
- `references/workflow_contracts.md` -- Contract definitions and handoff patterns

## Key Principles

1. No API keys required -- all validation is local and offline
2. Non-destructive -- reads SKILL.md and CLAUDE.md only, never modifies skills
3. Deterministic -- same inputs always produce same validation results

## 扩展验证能力

### SKILL.md Frontmatter 校验

除工作流验证外，还可校验每个 skill 的 SKILL.md 格式：

```bash
python3 skills/skill-integration-tester/scripts/validate_workflows.py \
  --validate-frontmatter \
  --output-dir reports/
```

检查项：
- `name` 字段存在且与目录名一致
- `description` 字段存在且非空
- YAML frontmatter 格式正确（`---` 分隔符）

### 输出 Schema 回归测试

当 skill 更新输出格式时，验证下游消费者是否兼容：

| 检查项 | 验证方法 | 失败处理 |
|--------|---------|---------|
| JSON 字段存在性 | 检查必需字段 | FAIL + 列出缺失字段 |
| 文件命名格式 | 正则匹配 `*_YYYY-MM-DD_HHMMSS.json` | WARNING |
| schema_version 兼容 | 语义版本比较 | FAIL if major version mismatch |

### 常见问题

- **Workflow 未找到**: 确认 CLAUDE.md 中工作流名称格式为 `**Workflow Name:**`
- **Skill 目录不存在**: 检查 skill 名称映射（display name → directory name）
- **Contract FAIL**: 查看生产者 skill 的输出 JSON 是否包含消费者期望的字段

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
