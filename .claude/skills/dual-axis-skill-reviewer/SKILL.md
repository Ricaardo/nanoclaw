---
name: dual-axis-skill-reviewer
description: "Review skills in any project using a dual-axis method: (1) deterministic code-based checks (structure, scripts, tests, execution safety) and (2) LLM deep review findings. Use when you need reproducible quality scoring for `skills/*/SKILL.md`, want to gate merges with a score threshold (for example 90+), or need concrete improvement items for low-scoring skills. Works across projects via --project-root." 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Dual Axis Skill Reviewer

Run the dual-axis reviewer script and save reports to `reports/`.

The script supports:
- Random or fixed skill selection
- Auto-axis scoring with optional test execution
- LLM prompt generation
- LLM JSON review merge with weighted final score
- Cross-project review via `--project-root`

## When to Use

- Need reproducible scoring for one skill in `skills/*/SKILL.md`.
- Need improvement items when final score is below 90.
- Need both deterministic checks and qualitative LLM code/content review.
- Need to review skills in a **different project** from the command line.

## Prerequisites

- Python 3.9+
- `uv` (recommended — auto-resolves `pyyaml` dependency via inline metadata)
- For tests: `uv sync --extra dev` or equivalent in the target project
- For LLM-axis merge: JSON file that follows the LLM review schema (see Resources)

## Workflow

Determine the correct script path based on your context:

- **Same project**: `skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py`
- **Global install**: `~/.claude/skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py`

The examples below use `REVIEWER` as a placeholder. Set it once:

```bash
# If reviewing from the same project:
REVIEWER=skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py

# If reviewing another project (global install):
REVIEWER=~/.claude/skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py
```

### Step 1: Run Auto Axis + Generate LLM Prompt

```bash
uv run "$REVIEWER" \
  --project-root . \
  --emit-llm-prompt \
  --output-dir reports/
```

When reviewing a different project, point `--project-root` to it:

```bash
uv run "$REVIEWER" \
  --project-root /path/to/other/project \
  --emit-llm-prompt \
  --output-dir reports/
```

### Step 2: Run LLM Review
- Use the generated prompt file in `reports/skill_review_prompt_<skill>_<timestamp>.md`.
- Ask the LLM to return strict JSON output.
- When running inside Claude Code, let Claude act as orchestrator: read the generated prompt, produce the LLM review JSON, and save it for the merge step.

### Step 3: Merge Auto + LLM Axes

```bash
uv run "$REVIEWER" \
  --project-root . \
  --skill <skill-name> \
  --llm-review-json <path-to-llm-review.json> \
  --auto-weight 0.5 \
  --llm-weight 0.5 \
  --output-dir reports/
```

### Step 4: Optional Controls

- Fix selection for reproducibility: `--skill <name>` or `--seed <int>`
- Review all skills at once: `--all`
- Skip tests for quick triage: `--skip-tests`
- Change report location: `--output-dir <dir>`
- Increase `--auto-weight` for stricter deterministic gating.
- Increase `--llm-weight` when qualitative/code-review depth is prioritized.

## Output

- `reports/skill_review_<skill>_<timestamp>.json`
- `reports/skill_review_<skill>_<timestamp>.md`
- `reports/skill_review_prompt_<skill>_<timestamp>.md` (when `--emit-llm-prompt` is enabled)

## Installation (Global)

To use this skill from any project, symlink it into `~/.claude/skills/`:

```bash
ln -sfn /path/to/claude-trading-skills/skills/dual-axis-skill-reviewer \
  ~/.claude/skills/dual-axis-skill-reviewer
```

After this, Claude Code will discover the skill in all projects, and the script is accessible at `~/.claude/skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py`.

## Resources

- Auto axis scores metadata, workflow coverage, execution safety, artifact presence, and test health.
- Auto axis detects `knowledge_only` skills and adjusts script/test expectations to avoid unfair penalties.
- LLM axis scores deep content quality (correctness, risk, missing logic, maintainability).
- Final score is weighted average.
- If final score is below 90, improvement items are required and listed in the markdown report.
- Script: `skills/dual-axis-skill-reviewer/scripts/run_dual_axis_review.py`
- LLM schema: `references/llm_review_schema.md`
- Rubric detail: `references/scoring_rubric.md`


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
