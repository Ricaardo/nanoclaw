---
name: skill-idea-miner
description: Mine Claude Code session logs for skill idea candidates. Use when running the weekly skill generation pipeline to extract, score, and backlog new skill ideas from recent coding sessions. 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。
---

# Skill Idea Miner

Automatically extract skill idea candidates from Claude Code session logs,
score them for novelty, feasibility, and trading value, and maintain a
prioritized backlog for downstream skill generation.

## When to Use

- Weekly automated pipeline run (Saturday 06:00 via launchd)
- Manual backlog refresh: `python3 scripts/run_skill_generation_pipeline.py --mode weekly`
- Dry-run to preview candidates without LLM scoring

## Workflow

### Stage 1: Session Log Mining

1. Enumerate session logs from allowlist projects in `~/.claude/projects/`
2. Filter to past 7 days by file mtime, confirm with `timestamp` field
3. Extract user messages (`type: "user"`, `userType: "external"`)
4. Extract tool usage patterns from assistant messages
5. Run deterministic signal detection:
   - Skill usage frequency (`skills/*/` path references)
   - Error patterns (non-zero exit codes, `is_error` flags, exception keywords)
   - Repetitive tool sequences (3+ tools repeated 3+ times)
   - Automation request keywords (English and Japanese)
   - Unresolved requests (5+ minute gap after user message)
6. Invoke Claude CLI headless for idea abstraction
7. Output `raw_candidates.yaml`

### Stage 2: Scoring and Deduplication

1. Load existing skills from `skills/*/SKILL.md` frontmatter
2. Deduplicate via Jaccard similarity (threshold > 0.5) against:
   - Existing skill names and descriptions
   - Existing backlog ideas
3. Score non-duplicate candidates with Claude CLI:
   - Novelty (0-100): differentiation from existing skills
   - Feasibility (0-100): technical implementability
   - Trading Value (0-100): practical value for investors/traders
   - Composite = 0.3 * Novelty + 0.3 * Feasibility + 0.4 * Trading Value
4. Merge scored candidates into `logs/.skill_generation_backlog.yaml`

## Output Format

### raw_candidates.yaml

```yaml
generated_at_utc: "2026-03-08T06:00:00Z"
period: {from: "2026-03-01", to: "2026-03-07"}
projects_scanned: ["claude-trading-skills"]
sessions_scanned: 12
candidates:
  - id: "raw_2026w10_001"
    title: "Earnings Whispers Image Parser"
    source_project: "claude-trading-skills"
    evidence:
      user_requests: ["Extract earnings dates from screenshot"]
      pain_points: ["Manual image reading"]
      frequency: 3
    raw_description: "Parse Earnings Whispers screenshots to extract dates."
    category: "data-extraction"
```

### Backlog (logs/.skill_generation_backlog.yaml)

```yaml
updated_at_utc: "2026-03-08T06:15:00Z"
ideas:
  - id: "idea_2026w10_001"
    title: "Earnings Whispers Image Parser"
    description: "Skill that parses Earnings Whispers screenshots..."
    category: "data-extraction"
    scores: {novelty: 75, feasibility: 60, trading_value: 80, composite: 73}
    status: "pending"
```

## Resources

- `references/idea_extraction_rubric.md` — Signal detection criteria and scoring rubric
- `scripts/mine_session_logs.py` — Session log parser
- `scripts/score_ideas.py` — Scorer and deduplicator

## 算法说明

### Jaccard 去重 (阈值 0.5)

将 skill 名称/描述 tokenize 后计算集合相似度：
```
Jaccard(A, B) = |A ∩ B| / |A ∪ B|
```
- 阈值 0.5 = 两个 idea 有超过一半的关键词重叠时视为重复
- 该阈值经验证对 3-10 词的 skill 标题有良好效果
- 可通过 `--jaccard-threshold` 参数调整

### 评分权重说明

| 维度 | 权重 | 理由 |
|------|------|------|
| Novelty | 30% | 避免与现有 83 个 skill 重复 |
| Feasibility | 30% | 确保可在 Claude Skill 框架内实现 |
| Trading Value | 40% | 最终目标：为交易/投资提供实际价值 |

Trading Value 权重最高，因为工具的价值在于帮助用户做出更好的投资决策。

### 调试模式

```bash
# Dry-run: 只挖掘不评分
python3 skills/skill-idea-miner/scripts/mine_session_logs.py \
  --dry-run --output-dir reports/

# Verbose: 显示去重计算过程
python3 skills/skill-idea-miner/scripts/mine_session_logs.py \
  --verbose --output-dir reports/
```

### 常见问题

- **无候选 idea**: 过去 7 天无新 session log，或所有 idea 与已有 skill 重复
- **评分偏低**: 可能 idea 太泛化，尝试更具体的 session（如调试特定策略时的 session）
- **backlog 文件冲突**: `logs/.skill_generation_backlog.yaml` 格式错误时手动修复

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
