---
name: skill-designer
description: Design new Claude skills from structured idea specifications. Use when the skill auto-generation pipeline needs to produce a Claude CLI prompt that creates a complete skill directory (SKILL.md, references, scripts, tests) following repository conventions. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Skill Designer

## Overview

Generate a comprehensive Claude CLI prompt from a structured skill idea
specification. The prompt instructs Claude to create a complete skill directory
following repository conventions: SKILL.md with YAML frontmatter, reference
documents, helper scripts, and test scaffolding.

## When to Use

- The skill auto-generation pipeline selects an idea from the backlog and needs
  a design prompt for `claude -p`
- A developer wants to bootstrap a new skill from a JSON idea specification
- Quality review of generated skills requires awareness of the scoring rubric

## Prerequisites

- Python 3.9+
- No external API keys required
- Reference files must exist under `skills/skill-designer/references/`

## Workflow

### Step 1: Prepare Idea Specification

Accept a JSON file (`--idea-json`) containing:
- `title`: Human-readable idea name
- `description`: What the skill does
- `category`: Skill category (e.g., trading-analysis, developer-tooling)

Accept a normalized skill name (`--skill-name`) that will be used as the
directory name and YAML frontmatter `name:` field.

### Step 2: Build Design Prompt

Run the prompt builder:

```bash
python3 skills/skill-designer/scripts/build_design_prompt.py \
  --idea-json /tmp/idea.json \
  --skill-name "my-new-skill" \
  --project-root .
```

The script:
1. Loads the idea JSON
2. Reads all three reference files (structure guide, quality checklist, template)
3. Lists existing skills (up to 20) to prevent duplication
4. Outputs a complete prompt to stdout

### Step 3: Feed Prompt to Claude CLI

The calling pipeline pipes the prompt into `claude -p`:

```bash
python3 skills/skill-designer/scripts/build_design_prompt.py \
  --idea-json /tmp/idea.json \
  --skill-name "my-new-skill" \
  --project-root . \
| claude -p --allowedTools Read,Edit,Write,Glob,Grep
```

### Step 4: Validate Output

After Claude creates the skill, verify:
- `skills/<skill-name>/SKILL.md` exists with correct frontmatter
- Directory structure follows conventions
- Score with dual-axis-skill-reviewer meets threshold

## Output Format

The script outputs a plain-text prompt to stdout. Exit code 0 on success,
1 if required reference files are missing.

## Resources

- `references/skill-structure-guide.md` -- Directory structure, SKILL.md format, naming conventions
- `references/quality-checklist.md` -- Dual-axis reviewer 5-category checklist (100 points)
- `references/skill-template.md` -- SKILL.md template with YAML frontmatter and standard sections
- `scripts/build_design_prompt.py` -- Prompt builder script (CLI interface)

## 安全检查

### 引用文件验证

脚本在构建 prompt 前验证：
1. `references/skill-structure-guide.md` — 存在且非空
2. `references/quality-checklist.md` — 存在且非空
3. `references/skill-template.md` — 存在且非空

缺少任何文件 → exit code 1 + 明确错误信息

### Skill 名称唯一性

脚本列出现有 skills 目录（最多 20 个），在 prompt 中包含已有列表，指示 Claude 避免重复。

### 常见问题

| 问题 | 原因 | 解决 |
|------|------|------|
| "Reference file not found" | references/ 目录缺失文件 | 检查 `skills/skill-designer/references/` 下三个文件 |
| 生成的 skill 缺少 frontmatter | prompt 模板未正确注入 | 检查 `skill-template.md` 格式 |
| Skill 名称与已有重复 | 列表仅包含前 20 个 | 手动检查 `ls skills/` |
| Claude CLI 超时 | 生成内容过多 | 减少 `--max-tokens` 或拆分生成 |

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
