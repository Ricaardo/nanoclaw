# Thesis Tracker

description: Maintain and update investment theses for portfolio positions and watchlist names. Track key data points, catalysts, and thesis milestones over time. Use when updating a thesis with new information, reviewing position rationale, or checking if a thesis is still intact. Triggers on "update thesis for [company]", "is my thesis still intact", "thesis check", "add data point to [company]", or "review my positions". 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。

## Workflow

### Step 1: Define or Load Thesis

If creating a new thesis:
- **Company**: Name and ticker
- **Position**: Long or Short
- **Thesis statement**: 1-2 sentence core thesis (e.g., "Long ACME — margin expansion from pricing power + operating leverage as mix shifts to software")
- **Key pillars**: 3-5 supporting arguments
- **Key risks**: 3-5 risks that would invalidate the thesis
- **Catalysts**: Upcoming events that could prove/disprove the thesis (earnings, product launches, regulatory decisions)
- **Target price / valuation**: What's it worth if the thesis plays out
- **Stop-loss trigger**: What would make you exit

If updating an existing thesis, ask the user for the new data point or development.

### Step 2: Update Log

For each new data point or development:

- **Date**: When this happened
- **Data point**: What changed (earnings beat, management departure, competitor move, etc.)
- **Thesis impact**: Does this strengthen, weaken, or neutralize a specific pillar?
- **Action**: No change / Increase position / Trim / Exit
- **Updated conviction**: High / Medium / Low

### Step 3: Thesis Scorecard

Maintain a running scorecard:

| Pillar | Original Expectation | Current Status | Trend |
|--------|---------------------|----------------|-------|
| Revenue growth >20% | On track | Q3 was 22% | Stable |
| Margin expansion | Behind | Margins flat YoY | Concerning |
| New product launch | Pending | Delayed to Q2 | Watch |

### Step 4: Catalyst Calendar

Track upcoming catalysts:

| Date | Event | Expected Impact | Notes |
|------|-------|-----------------|-------|
| | | | |

### Step 5: Output

Thesis summary suitable for:
- Morning meeting discussion
- Portfolio review
- Risk committee presentation

Format: Concise markdown or Word doc with the scorecard, recent updates, and current conviction level.

## Important Notes

- A thesis should be falsifiable — if nothing could disprove it, it's not a thesis
- Track disconfirming evidence as rigorously as confirming evidence
- Review theses at least quarterly, even when nothing dramatic has happened
- If the user manages multiple positions, offer to do a full portfolio thesis review
- Store thesis data in a structured format so it can be referenced across sessions

## 数据持久化

### Thesis YAML Schema

论点存储在 `reports/theses/` 目录下，每个标的一个 YAML 文件：

```yaml
# reports/theses/AAPL.yaml
ticker: AAPL
name: Apple Inc.
position: long
created: "2026-01-15"
last_updated: "2026-03-12"
conviction: high  # high/medium/low
thesis_statement: "Long AAPL — 服务收入高速增长 + AI 功能驱动换机周期"

pillars:
  - id: P1
    description: "服务收入占比提升，毛利率扩张"
    status: on_track  # on_track/behind/ahead/invalidated
    evidence:
      - date: "2026-01-30"
        event: "Q1 服务收入 $26.3B (+14% YoY)"
        impact: strengthens
  - id: P2
    description: "Apple Intelligence 驱动 iPhone 升级"
    status: watch
    evidence: []

risks:
  - id: R1
    description: "中国市场需求持续疲软"
    severity: medium
    status: active

catalysts:
  - date: "2026-04-24"
    event: "Q2 FY2026 Earnings"
    expected_impact: high

target_price: 245
stop_loss: 185
entry_price: 198
current_conviction_score: 78  # 0-100
```

### 操作指令

```bash
# 创建新论点
echo "创建 AAPL 论点" && mkdir -p reports/theses

# 更新论点（手动编辑 YAML 或通过对话更新）
# Claude 会自动读取/更新 reports/theses/TICKER.yaml
```

### 评分卡计算

| 维度 | 权重 | 评分规则 |
|------|------|---------|
| 支撑论据达成率 | 40% | on_track=100, ahead=100, watch=50, behind=25, invalidated=0 |
| 风险可控度 | 25% | 无 active 高风险=100, 有=根据严重性折扣 |
| 催化剂进展 | 20% | 已验证催化剂占比 |
| 价格位置 | 15% | 相对入场价和目标价的位置 |

综合评分 = 加权平均，<50 建议减仓/退出，50-70 维持，>70 可加仓

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
