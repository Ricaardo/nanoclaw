---
name: scenario-analyzer
description: |
  从新闻标题出发分析18个月投资场景的技能。Analyze 18-month scenarios from news headlines.
  调用 scenario-analyst 智能体执行主分析，
  调用 strategy-reviewer 智能体获取第二意见。
  生成包含一次/二次/三次影响、推荐标的、评审意见的中文综合报告。
  支持美股/A股/港股/加密货币/贵金属多市场分析。
  使用例: /scenario-analyzer "Fed raises rates by 50bp"
  触发词: 新闻分析、场景分析、18个月展望、中长期投资策略、scenario analysis
---

# 标题场景分析器

## 概述

本技能以新闻标题为起点，分析中长期（18个月）投资场景。
依次调用两个专业智能体（`scenario-analyst` 和 `strategy-reviewer`），
将多角度分析与批判性审查整合，生成综合报告。
支持美股/A股/港股/加密货币/贵金属多市场分析。

## 适用场景

以下情况请使用本技能：

- 从新闻标题分析中长期投资影响
- 构建18个月内的多种场景
- 按一次/二次/三次影响整理板块和标的
- 需要包含第二意见的综合分析
- 需要中文报告输出

**使用示例:**
```
/scenario-analyzer "Fed raises interest rates by 50bp, signals more hikes ahead"
/scenario-analyzer "中国对美半导体加征新关税"
/scenario-analyzer "OPEC+ agrees to cut oil production by 2 million barrels per day"
/scenario-analyzer "央行宣布降准50个基点"
```

## 架构

```
┌─────────────────────────────────────────────────────────────────────┐
│                    Skill（编排器）                                    │
│                                                                      │
│  Phase 1: 准备                                                       │
│  ├─ 标题解析                                                         │
│  ├─ 事件类型分类                                                     │
│  └─ 参考资料读取                                                     │
│                                                                      │
│  Phase 2: 智能体调用                                                 │
│  ├─ scenario-analyst（主分析）                                       │
│  └─ strategy-reviewer（第二意见）                                    │
│                                                                      │
│  Phase 3: 整合与报告生成                                             │
│  └─ reports/scenario_analysis_<topic>_YYYYMMDD.md                   │
└─────────────────────────────────────────────────────────────────────┘
```

## 工作流程

### Phase 1: 准备

#### Step 1.1: 标题解析

解析用户输入的新闻标题。

1. **标题确认**
   - 确认是否传入了标题参数
   - 若未传入，要求用户输入

2. **关键词提取**
   - 主要实体（企业名、国家名、机构名）
   - 数值数据（利率、价格、数量）
   - 行为动词（上调、下调、发布、达成协议等）

#### Step 1.2: 事件类型分类

将标题归入以下类别：

| 类别 | 示例 |
|------|------|
| 货币政策 | FOMC、ECB、央行、加息、降息、QE/QT、降准 |
| 地缘政治 | 战争、制裁、关税、贸易摩擦 |
| 监管政策 | 环境法规、金融监管、反垄断 |
| 科技变革 | AI、EV、可再生能源、半导体 |
| 大宗商品 | 原油、黄金、铜、农产品 |
| 企业/并购 | 收购、破产、财报、行业重组 |

#### Step 1.3: 参考资料读取

根据事件类型读取相关参考资料：

```
Read references/headline_event_patterns.md
Read references/sector_sensitivity_matrix.md
Read references/scenario_playbooks.md
```

**参考资料内容:**
- `headline_event_patterns.md`: 历史事件模式与市场反应
- `sector_sensitivity_matrix.md`: 事件×板块影响度矩阵
- `scenario_playbooks.md`: 场景构建模板与最佳实践

---

### Phase 2: 智能体调用

#### Step 2.1: 调用 scenario-analyst

使用 Task tool 调用主分析智能体。

```
Task tool:
- subagent_type: "scenario-analyst"
- prompt: |
    请对以下标题执行18个月场景分析。

    ## 目标标题
    [输入的标题]

    ## 事件类型
    [分类结果]

    ## 参考信息
    [读取的参考资料摘要]

    ## 分析要求
    1. 通过 WebSearch 收集近两周的相关新闻
    2. 构建 Base/Bull/Bear 三个场景（概率合计100%）
    3. 按板块分析一次/二次/三次影响
    4. 选定正面/负面影响标的各3-5个（覆盖美股/A股/港股，根据事件相关市场选择）
    5. 全部使用中文输出
```

**期望输出:**
- 相关新闻列表
- 三个场景（Base/Bull/Bear）详情
- 板块影响分析（一次/二次/三次）
- 标的推荐列表

#### Step 2.2: 调用 strategy-reviewer

基于 scenario-analyst 的分析结果，调用审查智能体。

```
Task tool:
- subagent_type: "strategy-reviewer"
- prompt: |
    请审查以下场景分析。

    ## 目标标题
    [输入的标题]

    ## 分析结果
    [scenario-analyst 的完整输出]

    ## 审查要求
    从以下角度进行审查：
    1. 被遗漏的板块/标的
    2. 场景概率分配的合理性
    3. 影响分析的逻辑一致性
    4. 乐观/悲观偏见检测
    5. 替代场景建议
    6. 时间线的现实性

    请用中文输出建设性且具体的反馈。
```

**期望输出:**
- 遗漏指出
- 场景概率意见
- 偏见指出
- 替代场景建议
- 最终建议

---

### Phase 3: 整合与报告生成

#### Step 3.1: 结果整合

将两个智能体的输出整合，形成最终投资判断。

**整合要点:**
1. 补充审查中指出的遗漏
2. 调整概率分配（如有必要）
3. 考虑偏见后的最终判断
4. 制定具体行动方案

#### Step 3.2: 报告生成

按以下格式生成最终报告并保存。

**保存路径:** `reports/scenario_analysis_<topic>_YYYYMMDD.md`

```markdown
# 标题场景分析报告

**分析时间**: YYYY-MM-DD HH:MM
**目标标题**: [输入的标题]
**事件类型**: [分类类别]

---

## 1. 相关新闻
[scenario-analyst 收集的新闻列表]

## 2. 场景概要（未来18个月）

### Base Case（XX%概率）
[场景详情]

### Bull Case（XX%概率）
[场景详情]

### Bear Case（XX%概率）
[场景详情]

## 3. 板块/行业影响

### 一次影响（直接影响）
[影响表格]

### 二次影响（产业链/关联产业）
[影响表格]

### 三次影响（宏观/监管/技术）
[影响表格]

## 4. 正面影响标的（3-5个）
[标的表格]

## 5. 负面影响标的（3-5个）
[标的表格]

## 6. 第二意见与审查
[strategy-reviewer 的输出]

## 7. 最终投资判断与建议

### 推荐行动
[结合审查的具体行动]

### 风险因素
[主要风险列举]

### 监控要点
[需跟踪的指标与事件]

---
**生成**: scenario-analyzer skill
**智能体**: scenario-analyst, strategy-reviewer
```

#### Step 3.3: 报告保存

1. 若 `reports/` 目录不存在则创建
2. 保存为 `scenario_analysis_<topic>_YYYYMMDD.md`（例: `scenario_analysis_fed_rate_hike_20260104.md`）
3. 通知用户保存完成
4. **不得直接保存到项目根目录**

---

## 资源

### 参考文档
- `references/headline_event_patterns.md` - 事件模式与市场反应
- `references/sector_sensitivity_matrix.md` - 板块敏感度矩阵
- `references/scenario_playbooks.md` - 场景构建模板

### 智能体
- `scenario-analyst` - 主场景分析
- `strategy-reviewer` - 第二意见审查

---

## 重要说明

### 语言
- 所有分析和输出使用**中文**
- 标的 ticker 保留英文标记（AAPL, 600519.SH, 00700.HK）

### 目标市场
- 标的选择覆盖**美股、A股、港股**（根据事件相关市场）
- 加密货币和贵金属在相关事件时纳入分析
- 含 ADR

### 时间轴
- 场景覆盖**18个月**
- 按 0-6个月/6-12个月/12-18个月 三阶段描述

### 概率分配
- Base + Bull + Bear = **100%**
- 各场景概率须附带依据

### 第二意见
- **必须**执行（始终调用 strategy-reviewer）
- 审查结果须反映在最终判断中

### 输出路径（重要）
- **必须**保存到 `reports/` 目录下
- 路径: `reports/scenario_analysis_<topic>_YYYYMMDD.md`
- 例: `reports/scenario_analysis_fed_rate_hike_20260104.md`
- 若 `reports/` 目录不存在则创建
- **不得直接保存到项目根目录**

---

## 质量检查清单

报告完成前确认以下事项：

- [ ] 标题是否正确解析
- [ ] 事件类型分类是否恰当
- [ ] 三个场景概率合计是否为100%
- [ ] 一次/二次/三次影响的逻辑关联是否清晰
- [ ] 标的选定是否有具体依据
- [ ] 是否包含 strategy-reviewer 的审查
- [ ] 是否有结合审查的最终判断
- [ ] 报告是否保存到正确路径


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
