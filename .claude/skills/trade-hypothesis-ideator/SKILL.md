---
name: trade-hypothesis-ideator
description: >
  Generate falsifiable trade strategy hypotheses from market data, trade logs,
  and journal snippets. Use when you have a structured input bundle and want
  ranked hypothesis cards with experiment designs, kill criteria, and optional
  strategy.yaml export compatible with edge-finder-candidate/v1.

  当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。---

# Trade Hypothesis Ideator

Generate 1-5 structured hypothesis cards from a normalized input bundle, critique and rank them, then optionally export `pursue` cards into `strategy.yaml` + `metadata.json` artifacts.

## Workflow

1. Receive input JSON bundle.
2. Run pass 1 normalization + evidence extraction.
3. Generate hypotheses with prompts:
   - `prompts/system_prompt.md`
   - `prompts/developer_prompt_template.md` (inject `{{evidence_summary}}`)
4. Critique hypotheses with `prompts/critique_prompt_template.md`.
5. Run pass 2 ranking + output formatting + guardrails.
6. Optionally export `pursue` hypotheses via Step H strategy exporter.

## Scripts

- Pass 1 (evidence summary):

```bash
python3 skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py \
  --input skills/trade-hypothesis-ideator/examples/example_input.json \
  --output-dir reports/
```

- Pass 2 (rank + output + optional export):

```bash
python3 skills/trade-hypothesis-ideator/scripts/run_hypothesis_ideator.py \
  --input skills/trade-hypothesis-ideator/examples/example_input.json \
  --hypotheses reports/raw_hypotheses.json \
  --output-dir reports/ \
  --export-strategies
```

## References

- `references/hypothesis_types.md`
- `references/evidence_quality_guide.md`

## 证据质量评估框架

### 输入 JSON Bundle 结构

```json
{
  "context": {
    "market": "US",
    "date": "2026-03-13",
    "regime": "bull"
  },
  "evidence": [
    {
      "type": "price_action",
      "description": "NVDA 突破前高，成交量放大 2.5x",
      "quality": "high",
      "source": "market_data"
    },
    {
      "type": "flow_data",
      "description": "13F 显示 Tiger Global 加仓 NVDA 35%",
      "quality": "medium",
      "source": "sec_filing"
    }
  ],
  "trade_logs": [],
  "journal_snippets": []
}
```

### 证据质量分级

| 等级 | 定义 | 权重 |
|------|------|------|
| **High** | 可量化、可验证的硬数据（价格、成交量、财报） | ×1.0 |
| **Medium** | 延迟数据或二手来源（13F、分析师报告） | ×0.7 |
| **Low** | 定性观察、传闻、社交媒体情绪 | ×0.3 |

### 假设排名公式

每个假设按 5 维度评分 (0-100)：

| 维度 | 权重 | 说明 |
|------|------|------|
| 可证伪性 | 25% | 是否有明确的 kill criteria |
| 证据支撑 | 25% | 加权证据质量得分 |
| 风险回报比 | 20% | 预期收益/最大损失 |
| 执行可行性 | 15% | 流动性、成本、时效性 |
| 新颖度 | 15% | 与已知策略的差异度 |

Composite = Σ(维度分 × 权重)

### 输出示例

```json
{
  "hypotheses": [
    {
      "id": "H1",
      "title": "NVDA AI 订单加速驱动突破",
      "direction": "long",
      "confidence": 78,
      "verdict": "pursue",
      "kill_criteria": ["NVDA 跌破 50MA", "Q2 数据中心收入增速 <40%"],
      "experiment": {
        "entry": "突破 $950 买入",
        "stop": "$890 (-6.3%)",
        "target": "$1050 (+10.5%)",
        "timeframe": "4-6 weeks"
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
