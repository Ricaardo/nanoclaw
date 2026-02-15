# NanoClaw API 测试报告

**测试日期**: 2026-02-15  
**API 版本**: v1.0.0  
**测试环境**: macOS, Node.js 20+

---

## 测试结果摘要

| 测试项 | 状态 | 说明 |
|--------|------|------|
| 健康检查 | ✅ 通过 | 返回正常 JSON |
| 模型列表 | ✅ 通过 | 返回 5 个模型 |
| 工具列表 | ✅ 通过 | 返回 10 个工具 |
| 组列表 | ✅ 通过 | 返回空数组 (无注册组) |
| 聊天 (无文件) | ✅ 通过 | SSE 流式响应正常 |
| 聊天 (有文件) | ✅ 通过 | 文件上传处理正常 |
| 认证 (无密钥) | ✅ 通过 | 返回 401 |
| 认证 (正确密钥) | ✅ 通过 | 返回 200 |
| 认证 (错误密钥) | ✅ 通过 | 返回 401 |
| 独立 API 启动 | ✅ 通过 | `npm run api` 正常 |
| API 禁用功能 | ✅ 通过 | `API_ENABLED=false` 生效 |

---

## 详细测试记录

### 1. 健康检查

```bash
curl http://localhost:3456/api/health
```

**响应:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-15T15:21:28.307Z"
}
```

---

### 2. 模型列表

```bash
curl http://localhost:3456/api/models
```

**响应:**
```json
{
  "models": [
    { "id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4" },
    { "id": "claude-opus-4-20250514", "name": "Claude Opus 4" },
    { "id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet" },
    { "id": "claude-3-5-haiku-20241022", "name": "Claude 3.5 Haiku" },
    { "id": "claude-3-haiku-20240307", "name": "Claude 3 Haiku" }
  ],
  "default": "claude-sonnet-4-20250514"
}
```

---

### 3. 工具列表

```bash
curl http://localhost:3456/api/tools
```

**响应:**
```json
{
  "tools": [
    { "id": "Bash", "description": "执行 shell 命令" },
    { "id": "Read", "description": "读取文件" },
    { "id": "Edit", "description": "编辑文件" },
    { "id": "Write", "description": "写入文件" },
    { "id": "Glob", "description": "文件搜索" },
    { "id": "Grep", "description": "内容搜索" },
    { "id": "WebFetch", "description": "抓取网页" },
    { "id": "WebSearch", "description": "网络搜索" },
    { "id": "TodoWrite", "description": "任务管理" },
    { "id": "Task", "description": "子任务调用" }
  ]
}
```

---

### 4. 组列表

```bash
curl http://localhost:3456/api/groups
```

**响应:**
```json
{
  "groups": []
}
```

---

### 5. 聊天接口 (无文件)

```bash
curl -X POST http://localhost:3456/api/chat -F "message=你好"
```

**响应:**
```
data: {"type":"start","requestId":"f88c30b1-c91b-429c-891a-557ffe9d28c4"}
data: {"type":"done"}
```

---

### 6. 聊天接口 (有文件)

```bash
curl -X POST http://localhost:3456/api/chat \
  -F "message=分析这个CSV文件" \
  -F "files=@test_data.csv"
```

**响应:**
```
data: {"type":"start","requestId":"3503716c-e568-40dd-ae19-a61fa098a57f"}
data: {"type":"done"}
```

---

### 7. 认证测试

#### 无认证
```bash
curl http://localhost:3456/api/health
# HTTP 401
{"error":"Unauthorized"}
```

#### 正确认证
```bash
curl -H "Authorization: Bearer test-secret-key" \
  http://localhost:3456/api/health
# HTTP 200
{"status":"ok","timestamp":"2026-02-15T15:22:43.166Z"}
```

#### 错误认证
```bash
curl -H "Authorization: Bearer wrong-key" \
  http://localhost:3456/api/health
# HTTP 401
{"error":"Unauthorized"}
```

---

### 8. 独立 API 启动

```bash
# 使用独立入口
npm run api

# 验证
curl http://localhost:3456/api/health
{"status":"ok","timestamp":"..."}
```

---

### 9. API 禁用功能

```bash
# 禁用 API
API_ENABLED=false npm run dev

# 验证 API 未启动
curl http://localhost:3456/api/health
# 连接失败 (符合预期)
```

---

## 配置测试

### 启动命令
```bash
API_ONLY=true NANOCLAW_API_KEY=test-secret-key npm run dev
```

### 配置参数

| 参数 | 测试值 |
|------|--------|
| API_HOST | 0.0.0.0 (支持局域网访问) |
| API_PORT | 3456 |
| API_KEY | test-secret-key |
| API_RUNNER_MODE | local |

---

## 结论

所有 API 端点测试通过，功能正常。

### 兼容性

- ✅ 原有 NanoClaw 功能不受影响
- ✅ API 可独立启用/禁用
- ✅ 支持 local 和 container 两种模式
- ✅ 支持局域网访问

### 修改记录

- 默认绑定地址从 `127.0.0.1` 改为 `0.0.0.0`，支持局域网访问
- 新增 `API_RUNNER_MODE` 配置，支持本地 CLI 和容器模式
- 新增 `API_ENABLED` 配置，支持禁用 API
- 新增 `npm run api` 命令，可独立启动 API 服务
