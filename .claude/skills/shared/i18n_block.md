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

### 市场特定注意事项

**A 股特色分析要素**：
- 政策风险评估（行业监管、产业政策）
- 北向资金流向（沪股通/深股通）
- 大宗交易与龙虎榜数据
- 申万行业分类（替代 GICS）
- 涨跌停制度影响

**港股特色分析要素**：
- 南向资金流向
- AH 溢价分析
- 港股通标的覆盖

**加密货币特色分析要素**：
- 链上数据指标
- 交易所资金流向
- 市值排名与主导率

### Dashboard JSON 输出（可选）
当用户请求 dashboard 格式时，在报告末尾额外输出 Recharts 兼容 JSON：
```json
{
  "title": "分析标题",
  "generated_at": "ISO8601时间戳",
  "charts": [
    {
      "id": "chart_1",
      "type": "line|bar|area|pie|heatmap",
      "title": "图表标题",
      "data": [],
      "xKey": "date",
      "yKeys": ["value"]
    }
  ],
  "metrics": [
    {
      "label": "指标名",
      "value": "数值",
      "change": "+5.2%",
      "trend": "up|down|flat"
    }
  ],
  "summary": "一句话结论"
}
```
保存为 `reports/<skill_name>_dashboard_YYYYMMDD.json`
