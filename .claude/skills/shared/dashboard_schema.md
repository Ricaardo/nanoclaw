# Recharts Dashboard JSON Schema

## 概述
所有 Skill 在用户请求 dashboard 格式时，输出符合以下 schema 的 JSON 文件，可直接被前端 Recharts 组件消费。

## Schema 定义

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["title", "generated_at", "charts", "summary"],
  "properties": {
    "title": {
      "type": "string",
      "description": "Dashboard 标题"
    },
    "generated_at": {
      "type": "string",
      "format": "date-time",
      "description": "生成时间 ISO8601"
    },
    "charts": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "type", "title", "data"],
        "properties": {
          "id": { "type": "string" },
          "type": {
            "type": "string",
            "enum": ["line", "bar", "area", "pie", "heatmap", "scatter", "composed"]
          },
          "title": { "type": "string" },
          "data": {
            "type": "array",
            "items": { "type": "object" }
          },
          "xKey": { "type": "string", "description": "X 轴字段名" },
          "yKeys": {
            "type": "array",
            "items": { "type": "string" },
            "description": "Y 轴字段名列表"
          },
          "colors": {
            "type": "array",
            "items": { "type": "string" },
            "description": "可选颜色列表（hex）"
          }
        }
      }
    },
    "metrics": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["label", "value"],
        "properties": {
          "label": { "type": "string", "description": "指标名称" },
          "value": { "type": ["string", "number"], "description": "指标值" },
          "change": { "type": "string", "description": "变化幅度 如 +5.2%" },
          "trend": {
            "type": "string",
            "enum": ["up", "down", "flat"],
            "description": "趋势方向"
          }
        }
      }
    },
    "tables": {
      "type": "array",
      "items": {
        "type": "object",
        "required": ["id", "title", "columns", "rows"],
        "properties": {
          "id": { "type": "string" },
          "title": { "type": "string" },
          "columns": {
            "type": "array",
            "items": {
              "type": "object",
              "properties": {
                "key": { "type": "string" },
                "label": { "type": "string" },
                "type": { "type": "string", "enum": ["text", "number", "percent", "currency"] }
              }
            }
          },
          "rows": {
            "type": "array",
            "items": { "type": "object" }
          }
        }
      }
    },
    "summary": {
      "type": "string",
      "description": "一句话核心结论"
    }
  }
}
```

## 图表类型使用指南

| 类型 | 适用场景 | 示例 |
|------|----------|------|
| `line` | 时间序列、价格走势 | 股价走势、指标变化 |
| `bar` | 分类对比、排名 | 行业涨幅对比、评分排名 |
| `area` | 累积值、区间展示 | 成交量、资金流向 |
| `pie` | 占比分布 | 持仓分布、行业权重 |
| `heatmap` | 矩阵关系、相关性 | 行业相关性、信号强度 |
| `scatter` | 双变量关系 | 风险收益散点 |
| `composed` | 多指标叠加 | 价格+成交量组合 |

## 输出路径
`reports/<skill_name>_dashboard_YYYYMMDD.json`
