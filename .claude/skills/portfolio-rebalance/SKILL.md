# Portfolio Rebalance

description: Analyze portfolio allocation drift and generate rebalancing trade recommendations across accounts. Considers tax implications, transaction costs, and wash sale rules. Triggers on "rebalance", "portfolio drift", "allocation check", "rebalancing trades", or "my portfolio is out of balance". 当用户用中文询问时触发。支持美股/A股/港股/加密货币/贵金属多市场分析。

## Workflow

### Step 1: Current State

For each account, capture:
- Account type (taxable, IRA, Roth, 401k)
- Holdings with current market value
- Cost basis (for taxable accounts)
- Unrealized gains/losses per position

### Step 2: Drift Analysis

Compare current allocation to IPS targets:

| Asset Class | Target % | Current % | Drift | $ Over/Under |
|------------|----------|-----------|-------|-------------|
| US Large Cap Equity | | | | |
| US Small/Mid Cap | | | | |
| International Developed | | | | |
| Emerging Markets | | | | |
| Investment Grade Bonds | | | | |
| High Yield / Credit | | | | |
| TIPS / Inflation Protected | | | | |
| Alternatives | | | | |
| Cash | | | | |

Flag positions exceeding the rebalancing band (typically ±3-5%).

### Step 3: Trade Recommendations

Generate trades to bring allocation back to target:

**Tax-Aware Rebalancing Rules:**
- Prefer rebalancing in tax-advantaged accounts (IRA, Roth) first — no tax consequences
- In taxable accounts, avoid selling positions with large short-term gains
- Harvest losses where possible while rebalancing
- Watch for wash sale rules (30-day window) across all accounts
- Consider directing new contributions to underweight asset classes instead of trading

**Trade List:**

| Account | Action | Security | Shares/$ | Reason | Tax Impact |
|---------|--------|----------|----------|--------|-----------|
| | Buy/Sell | | | Rebalance / TLH | ST gain / LT gain / Loss |

### Step 4: Asset Location Review

Optimize which assets are held in which account types:
- **Tax-deferred (IRA/401k)**: Bonds, REITs, high-turnover funds (highest tax drag)
- **Roth**: Highest expected growth assets (tax-free growth)
- **Taxable**: Tax-efficient equity (index funds, ETFs, munis), tax-loss harvesting candidates

### Step 5: Implementation

- Total trades by account
- Estimated transaction costs
- Estimated tax impact (realized gains/losses)
- Net effect on allocation drift

### Step 6: Output

- Drift analysis table
- Recommended trade list (Excel)
- Tax impact summary
- Before/after allocation comparison

## Important Notes

- Don't rebalance for rebalancing's sake — small drift within bands is fine
- Tax costs can outweigh rebalancing benefits in taxable accounts — calculate the breakeven
- Consider pending cash flows (contributions, withdrawals, RMDs) before trading
- Check for any client-specific restrictions (ESG, concentrated stock, lockups)
- Document rationale for every trade for compliance records
- Wash sale rules apply across accounts — coordinate trades across the household


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
