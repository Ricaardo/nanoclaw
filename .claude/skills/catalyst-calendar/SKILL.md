# Catalyst Calendar

description: Build and maintain a calendar of upcoming catalysts across a coverage universe — earnings dates, conferences, product launches, regulatory decisions, and macro events. Helps prioritize attention and position ahead of events. Triggers on "catalyst calendar", "upcoming events", "what's coming up", "earnings calendar", "event calendar", or "catalyst tracker". 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。

## Workflow

### Step 1: Define Coverage Universe

- List of companies to track (tickers or names)
- Sector / industry focus
- Include macro events? (Fed meetings, economic data, regulatory deadlines)
- Time horizon (next 2 weeks, month, quarter)

### Step 2: Gather Catalysts

For each company, identify upcoming events:

**Earnings & Financial Events**
- Quarterly earnings date and time (pre/post market)
- Annual shareholder meeting
- Investor day / analyst day
- Capital markets day
- Debt maturity / refinancing dates

**Corporate Events**
- Product launches or announcements
- FDA approvals / regulatory decisions
- Contract renewals or expirations
- M&A milestones (close dates, regulatory approvals)
- Management transitions
- Insider trading windows (lockup expirations)

**Industry Events**
- Major conferences (dates, which companies presenting)
- Trade shows and expos
- Regulatory comment periods or rulings
- Industry data releases (monthly sales, traffic, etc.)

**Macro Events**
- Fed meetings (FOMC dates)
- Jobs report, CPI, GDP releases
- Central bank decisions (ECB, BOJ, etc.)
- Geopolitical events with market impact

### Step 3: Calendar View

| Date | Event | Company/Sector | Type | Impact (H/M/L) | Our Positioning | Notes |
|------|-------|---------------|------|-----------------|----------------|-------|
| | | | Earnings/Corp/Industry/Macro | | Long/Short/Neutral | |

### Step 4: Weekly Preview

Each week, generate a forward-looking summary:

**This Week's Key Events:**
1. [Day]: [Company] Q[X] earnings — consensus [$X EPS], our estimate [$X], key focus: [metric]
2. [Day]: [Event] — why it matters for [stocks]
3. [Day]: [Macro release] — expectations and positioning

**Next Week Preview:**
- Early heads-up on important events coming

**Position Implications:**
- Events that could move specific positions
- Any pre-positioning recommended
- Risk management ahead of binary events

### Step 5: Output

- Excel workbook with calendar view and sortable columns
- Weekly preview email/note (markdown)
- Optional: integration with Google Calendar

## Important Notes

- Earnings dates shift — verify against company IR pages and Bloomberg/FactSet closer to the date
- Pre-announce risk: track companies with a history of pre-announcing (positive or negative)
- Conference attendance lists are valuable — which companies are presenting and which are conspicuously absent?
- Some catalysts are recurring (monthly industry data) — build a template and auto-populate
- Color-code by impact level: Red = high impact, Yellow = moderate, Green = routine
- Archive past catalysts with the actual outcome — builds pattern recognition over time

## 自动化数据聚合

### 使用现有 Skills 构建日历

```bash
# Step 1: 获取财报日历（使用 earnings-calendar skill）
python3 skills/earnings-calendar/scripts/get_earnings_calendar.py --weeks 4

# Step 2: 获取经济日历（使用 economic-calendar-fetcher skill）
python3 skills/economic-calendar-fetcher/scripts/fetch_economic_calendar.py --weeks 4

# Step 3: 合并为统一日历（手动或 Claude 辅助）
```

### 事件分类标准

| 类型 | 图标 | 影响评级标准 |
|------|------|------------|
| 财报 | 📊 | 持仓标的=H，观察名单=M，其他=L |
| FOMC | 🏛️ | 利率决议=H，纪要=M |
| 经济数据 | 📈 | CPI/NFP/GDP=H，PMI=M，其他=L |
| 公司事件 | 🏢 | IPO/并购=H，分析师日=M，常规=L |
| 期权到期 | ⚡ | 四巫日=H，月度到期=M，周度=L |

### 输出格式示例

```json
{
  "title": "催化剂日历",
  "generated_at": "2026-03-13T08:00:00",
  "period": {"from": "2026-03-13", "to": "2026-03-27"},
  "events": [
    {
      "date": "2026-03-18",
      "time": "14:00 ET",
      "event": "FOMC 利率决议",
      "type": "macro",
      "impact": "H",
      "tickers_affected": ["SPY", "QQQ", "TLT"],
      "notes": "市场定价维持不变概率 85%"
    }
  ],
  "weekly_preview": "本周关注 FOMC 决议和四巫日期权到期...",
  "position_implications": ["FOMC 前降低仓位至 80%", "期权到期前关注 max pain 水平"]
}
```

### 与其他 Skills 联动

| 事件类型 | 联动 Skill | 用途 |
|---------|-----------|------|
| 财报 | earnings-preview | 生成财报前预览 |
| 财报后 | earnings-trade-analyzer | 分析财报反应 |
| FOMC | fed-data-tracker | 获取 Fed 数据背景 |
| 期权到期 | option-chain | 查看 max pain 和 OI 分布 |

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
