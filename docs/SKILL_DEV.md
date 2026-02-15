# NanoClaw Skill 开发指南

本文档介绍如何为 NanoClaw 创建新的 Skill。

## 什么是 Skill

Skill 是预定义的任务模板，可以被 API 调用来执行特定任务，如：
- 生成测试用例
- 调试问题
- 添加新功能
- 代码审查

## Skill 目录结构

```
.claude/skills/
└── <skill-name>/
    └── SKILL.md
```

## SKILL.md 格式

```yaml
---
name: <skill-name>
description: <简短描述>
triggers: <触发关键词>(可选)
---

# Skill 标题

详细的 Skill 说明和使用方法...
```

### 字段说明

| 字段 | 必填 | 说明 |
|------|------|------|
| name | 是 | Skill 名称 (英文) |
| description | 是 | 简短描述，会在 API 中返回 |
| triggers | 否 | 触发关键词，多个用逗号或 `|` 分隔 |

## 示例 1: 生成测试用例

### 目录结构
```
.claude/skills/generate-test/
└── SKILL.md
```

### SKILL.md 内容

```markdown
---
name: generate-test
description: Generate unit tests for uploaded code files. Supports JavaScript, TypeScript, Python, Go, and other languages. Uses Vitest for JS/TS, pytest for Python.
triggers: test, generate test, unit test, 写测试
---

# Test Generator

You are a test generation assistant. Your task is to analyze the uploaded code and generate comprehensive unit tests.

## Workflow

1. **Read the uploaded files** - Understand the code structure
2. **Identify testable functions** - Find functions that can be unit tested
3. **Generate test file** - Create appropriate test file based on language

## Supported Languages

| Language | Test Framework | Pattern |
|----------|----------------|---------|
| JavaScript/TypeScript | Vitest | *.test.ts |
| Python | pytest | test_*.py |
| Go | built-in | *_test.go |

## Guidelines

- Cover edge cases and error conditions
- Use descriptive test names
- Follow best practices for the test framework
```

### API 调用

```bash
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=generate-test" \
  -F "message=generate unit tests" \
  -F "files=@source.ts"
```

---

## 示例 2: 代码审查

### SKILL.md

```markdown
---
name: code-review
description: Review code for bugs, security issues, performance problems, and best practices.
triggers: review, code review, 审查, review code
---

# Code Review Assistant

You are a code review assistant. Your task is to analyze the uploaded code and provide constructive feedback.

## Review Criteria

1. **Bugs** - Logic errors, edge cases
2. **Security** - Vulnerabilities, injection risks
3. **Performance** - Inefficient algorithms, memory issues
4. **Best Practices** - Code style, naming, documentation
5. **Testing** - Test coverage, test quality

## Output Format

Provide your review in the following format:

### Issues Found
- **[Severity]** File:Line - Description

### Recommendations
1. ...
2. ...

### Summary
Overall assessment...
```

### API 调用

```bash
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=code-review" \
  -F "message=review this code for security issues" \
  -F "files=@app.py"
```

---

## 示例 3: 文档生成

### SKILL.md

```markdown
---
name: generate-doc
description: Generate documentation for code. Supports JSDoc, docstrings, OpenAPI specs.
triggers: doc, documentation, generate doc, 文档
---

# Documentation Generator

You are a documentation assistant. Your task is to analyze the uploaded code and generate comprehensive documentation.

## Supported Formats

| Language | Format |
|----------|--------|
| JavaScript/TypeScript | JSDoc |
| Python | docstring (Google/NumPy style) |
| Go | GoDoc |

## Workflow

1. Read and understand the code
2. Identify public APIs, classes, functions
3. Generate documentation for each
4. Output in appropriate format

## Output

Write the documentation as comments in the code or as a separate markdown file.
```

### API 调用

```bash
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=generate-doc" \
  -F "message=generate documentation" \
  -F "files=@utils.ts"
```

---

## 示例 4: 代码转换

### SKILL.md

```markdown
---
name: code-convert
description: Convert code from one language to another. Supports JS to TS, Python to JS, etc.
triggers: convert, translate, 转换, 翻译
---

# Code Converter

You are a code conversion assistant. Your task is to convert code from one programming language to another.

## Supported Conversions

| From | To |
|------|-----|
| JavaScript | TypeScript |
| Python | JavaScript |
| Java | Python |

## Workflow

1. Read source code
2. Understand functionality
3. Convert to target language
4. Maintain equivalent behavior
5. Output converted code
```

### API 调用

```bash
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=code-convert" \
  -F "message=convert to TypeScript" \
  -F "files=@app.js"
```

---

## 示例 5: 安全扫描

### SKILL.md

```markdown
---
name: security-scan
description: Scan code for security vulnerabilities, secrets, and compliance issues.
triggers: security, scan, vulnerability, 安全, 扫描
---

# Security Scanner

You are a security scanning assistant. Your task is to identify security issues in the uploaded code.

## Scan Categories

1. **Secrets** - API keys, passwords, tokens
2. **Injection** - SQL, XSS, command injection
3. **Authentication** - Weak crypto, improper auth
4. **Data Exposure** - Sensitive data handling
5. **Dependencies** - Known vulnerabilities

## Output Format

```json
{
  "issues": [
    {
      "severity": "high|medium|low",
      "category": "...",
      "file": "...",
      "line": "...",
      "description": "...",
      "recommendation": "..."
    }
  ]
}
```

---

## 创建新 Skill 步骤

### 1. 创建目录

```bash
mkdir -p .claude/skills/<your-skill-name>
```

### 2. 创建 SKILL.md

按照上述格式编写 Skill 定义文件。

### 3. 测试 Skill

```bash
# 重启 API 服务
npm run api

# 查看 Skill 列表
curl http://localhost:3456/api/skills

# 运行 Skill
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=<your-skill-name>" \
  -F "message=your task" \
  -F "files=@file.txt"
```

### 4. 提交代码

```bash
git add .claude/skills/<your-skill-name>/
git commit -m "feat: add <skill-name> skill"
git push
```

---

## Skill 最佳实践

### 1. 名称规范
- 使用英文小写字母
- 使用连字符分隔单词
- 如: `generate-test`, `code-review`, `security-scan`

### 2. 描述规范
- 一句话说明功能
- 包含主要用途
- 如: "Generate unit tests for uploaded code files"

### 3. 触发词 (可选)
- 使用英文逗号或竖线分隔
- 包含常见变体
- 如: `test, generate test, unit test, 写测试`

### 4. 说明文档
- 清晰的工作流程
- 支持的格式/语言
- 输出格式示例

### 5. 错误处理
- 明确输入要求
- 提供使用示例
- 说明限制条件

---

## 常见问题

### Q: Skill 可以在 API 调用时传递参数吗?
可以，通过 `message` 字段传递具体指令。

### Q: Skill 可以生成文件吗?
可以，Skill 可以使用 Write 工具生成文件，文件会保存在工作目录中。

### Q: 如何让 Skill 支持更多语言?
在 SKILL.md 中添加对应的语言和框架支持说明。

### Q: Skill 有大小限制吗?
Skill 本身没有限制，但上传文件有 50MB 限制。
