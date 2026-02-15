# NanoClaw API 服务完整文档

## 目录

1. [概述](#概述)
2. [快速开始](#快速开始)
3. [环境配置](#环境配置)
4. [API 端点参考](#api-端点参考)
5. [认证与安全](#认证与安全)
6. [运行模式](#运行模式)
7. [请求与响应示例](#请求与响应示例)
8. [多语言调用示例](#多语言调用示例)
9. [部署指南](#部署指南)
10. [错误处理](#错误处理)
11. [常见问题](#常见问题)
12. [Skill 开发指南](./SKILL_DEV.md)

---

## 概述

NanoClaw API 是一个轻量级的 HTTP 接口服务，提供对 Claude Agent 的编程访问能力。

### 核心功能

- **消息处理**: 发送文本消息获取 AI 回复
- **文件上传**: 支持多种文件格式上传分析
- **模型选择**: 可选择不同的 Claude 模型
- **工具控制**: 细粒度控制 Agent 可使用的工具
- **流式响应**: Server-Sent Events (SSE) 实时返回结果

### 两种运行模式

| 模式 | 说明 | 依赖 |
|------|------|------|
| `local` (默认) | 使用本机安装的 Claude Code CLI | Claude Code 已登录 |
| `container` | 使用 Docker/Apple Container 容器 | Apple Container 或 Docker |

---

## 快速开始

### 1. 安装

```bash
# 克隆项目
git clone https://github.com/your-repo/nanoclaw.git
cd nanoclaw

# 安装依赖
npm install
```

### 2. 启动服务

```bash
# 默认模式 (使用本机 Claude CLI)
npm run dev

# 仅启动 API 服务
npm run api
```

### 3. 验证

```bash
curl http://localhost:3456/api/health
# {"status":"ok","timestamp":"2026-02-15T12:00:00.000Z"}
```

---

## 环境配置

### 环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `API_PORT` | 3456 | HTTP 服务端口 |
| `API_HOST` | 0.0.0.0 | 绑定地址 (支持局域网访问) |
| `NANOCLAW_API_KEY` | - | API 认证密钥 |
| `API_ENABLED` | true | 是否启用 API 服务 |
| `API_ONLY` | false | 仅启动 API，跳过容器检查 |
| `API_MAX_FILE_SIZE` | 52428800 | 最大文件上传字节 (50MB) |
| `API_RUNNER_MODE` | local | 运行模式: `local` 或 `container` |
| `CLAUDE_CLI_PATH` | claude | 本机 Claude CLI 路径 |
| `API_WORK_DIR` | groups/main | API 工作目录 |

### 启动示例

```bash
# 默认模式 (本机 CLI)
npm run dev

# 使用容器模式
API_RUNNER_MODE=container npm run dev

# 仅 API 服务
npm run api

# 自定义端口
API_PORT=8080 npm run dev

# 启用认证
NANOCLAW_API_KEY=your-secret-key npm run dev

# 禁用 API (原有模式)
API_ENABLED=false npm run dev

# 组合使用
API_ONLY=true NANOCLAW_API_KEY=secret PORT=8080 npm run dev
```

---

## API 端点参考

### 1. 健康检查

```http
GET /api/health
```

**响应:**
```json
{
  "status": "ok",
  "timestamp": "2026-02-15T12:00:00.000Z"
}
```

---

### 2. 获取可用组

```http
GET /api/groups
```

**响应:**
```json
{
  "groups": [
    {
      "jid": "imessage:chat123",
      "name": "Family Chat",
      "folder": "family",
      "trigger": "@Andy"
    }
  ]
}
```

---

### 3. 获取支持的模型

```http
GET /api/models
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

### 4. 获取支持的工具

```http
GET /api/tools
```

**响应:**
```json
{
  "tools": [
    { "id": "Bash", "description": "执行 shell 命令" },
    { "id": "Read", "description": "读取文件内容" },
    { "id": "Edit", "description": "编辑/修改文件" },
    { "id": "Write", "description": "创建/写入文件" },
    { "id": "Glob", "description": "按模式搜索文件" },
    { "id": "Grep", "description": "搜索文件内容" },
    { "id": "WebFetch", "description": "抓取网页内容" },
    { "id": "WebSearch", "description": "网络搜索" },
    { "id": "TodoWrite", "description": "任务管理" },
    { "id": "Task", "description": "调用子任务" }
  ]
}
```

---

### 5. 获取 Skills 列表

获取 NanoClaw 中可用的 Skills 列表。

```http
GET /api/skills
```

**响应:**
```json
{
  "skills": [
    { "name": "debug", "description": "Debug container agent issues" },
    { "name": "generate-test", "description": "Generate unit tests for code files" },
    { "name": "setup", "description": "Run initial NanoClaw setup" },
    { "name": "customize", "description": "Add new capabilities or modify behavior" }
  ]
}
```

---

### 6. 运行 Skill (生成测试用例等)

专门用于运行 Skills 的接口，适合自动化任务，如生成测试用例。

```http
POST /api/skills/run
Content-Type: multipart/form-data
```

**请求参数:**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `skill` | string | 是 | Skill 名称 |
| `message` | string | 是 | 任务描述 |
| `model` | string | 否 | 模型 ID |
| `tools` | string | 否 | 逗号分隔的工具列表 |
| `files` | file[] | 否 | 上传的文件 |

**支持的文件类型:**
- 代码文件: `.js`, `.ts`, `.jsx`, `.tsx`, `.py`, `.go`, `.java`, `.c`, `.cpp`, `.rs`, `.rb`, `.php`
- 文档: `.txt`, `.md`, `.json`, `.pdf`
- 表格: `.csv`, `.xlsx`
- 图片: `.png`, `.jpg`, `.jpeg`, `.gif`
- 压缩: `.zip`

**示例 - 生成测试用例:**

```bash
# 为 TypeScript 文件生成测试
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=generate-test" \
  -F "message=generate unit tests for this file" \
  -F "files=@utils.ts"

# 为 Python 文件生成测试
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=generate-test" \
  -F "message=generate unit tests using pytest" \
  -F "files=@app.py"
```

**示例 - 调试:**

```bash
curl -X POST http://localhost:3456/api/skills/run \
  -F "skill=debug" \
  -F "message=check recent container logs"
```

---

### 7. 发送聊天消息 (核心接口)

```http
POST /api/chat
Content-Type: multipart/form-data
```

**请求参数:**

| 参数 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `message` | string | 是 | - | 消息内容 |
| `group` | string | 否 | main | 组文件夹名称 |
| `model` | string | 否 | claude-sonnet-4-20250514 | 模型 ID |
| `tools` | string | 否 | 全部 | 逗号分隔的工具列表 |
| `skill` | string | 否 | - | 要调用的 Skill 名称 |
| `files` | file[] | 否 | - | 上传的文件 |

**支持的文件类型:**
- 代码文件: `.js`, `.ts`, `.jsx`, `.tsx`, `.py`, `.go`, `.java`, `.c`, `.cpp`, `.rs`, `.rb`, `.php`
- 文档: `.txt`, `.md`, `.json`, `.pdf`
- 表格: `.csv`, `.xlsx`
- 图片: `.png`, `.jpg`, `.jpeg`, `.gif`
- 压缩: `.zip`

**响应格式:** Server-Sent Events (SSE)

**示例:**

```bash
# 基础消息
curl -X POST http://localhost:3456/api/chat \
  -F "message=你好"

# 指定模型
curl -X POST http://localhost:3456/api/chat \
  -F "message=解释量子计算" \
  -F "model=claude-opus-4-20250514"

# 限制工具
curl -X POST http://localhost:3456/api/chat \
  -F "message=搜索代码中的 TODO" \
  -F "tools=Grep,Glob"

# 上传文件
curl -X POST http://localhost:3456/api/chat \
  -F "message=分析这个数据" \
  -F "files=@data.csv"

# 调用 Skill (如 debug)
curl -X POST http://localhost:3456/api/chat \
  -F "message=show me recent container logs" \
  -F "skill=debug"

# 调用 Skill 并上传文件
curl -X POST http://localhost:3456/api/chat \
  -F "message=analyze this code for security issues" \
  -F "skill=customize" \
  -F "files=@src/index.ts"

# 完整参数
curl -X POST http://localhost:3456/api/chat \
  -F "message=审查代码" \
  -F "group=main" \
  -F "model=claude-opus-4-20250514" \
  -F "tools=Read,Grep,Bash" \
  -F "files=@src/index.ts"
```

---

### 6. 下载文件

```http
GET /api/download/:fileId
```

**示例:**
```bash
curl -O http://localhost:3456/api/download/abc123
curl -o result.pdf http://localhost:3456/api/download/abc123
```

---

### 7. 删除文件

```http
DELETE /api/download/:fileId
```

**示例:**
```bash
curl -X DELETE http://localhost:3456/api/download/abc123
```

---

## 认证与安全

### 启用 API 密钥

```bash
NANOCLAW_API_KEY=your-secret-key npm run dev
```

### 请求时携带认证

```bash
curl -H "Authorization: Bearer your-secret-key" \
  http://localhost:3456/api/chat -F "message=你好"
```

### 安全建议

1. **本地部署**: 默认绑定 `0.0.0.0`，局域网可访问
2. **使用认证**: 生产环境务必设置 `NANOCLAW_API_KEY`
3. **防火墙**: 只开放必要端口

---

## 运行模式

### Local 模式 (默认)

使用本机安装的 Claude Code CLI：

```bash
# 默认就是 local 模式
npm run dev

# 或显式指定
API_RUNNER_MODE=local npm run dev
```

**要求:**
- Claude Code 已安装
- Claude Code 已登录 (运行过 `claude` 并完成认证)

### Container 模式

使用 Docker/Apple Container：

```bash
API_RUNNER_MODE=container npm run dev
```

**要求:**
- Apple Container (macOS) 或 Docker (macOS/Linux)

### 切换模式

| 场景 | 模式 | 命令 |
|------|------|------|
| 本机已安装 Claude Code | local | `npm run dev` |
| 需要隔离环境 | container | `API_RUNNER_MODE=container npm run dev` |
| 无 Claude Code，仅有 Docker | container | `API_RUNNER_MODE=container npm run dev` |

---

## 请求与响应示例

### SSE 响应格式

```
data: {"type":"start","requestId":"..."}
data: {"type":"content","text":"你好"}
data: {"type":"content","text="，我是 AI"}
data: {"type":"file","filename":"result.csv","fileId":"abc123"}
data: {"type":"done"}
```

### 事件类型

| 类型 | 字段 | 说明 |
|------|------|------|
| start | requestId | 请求开始 |
| content | text | 文本内容 |
| file | filename, fileId | 生成的文件 |
| error | error | 错误信息 |
| done | - | 完成 |

### 响应示例

```bash
curl -X POST http://localhost:3456/api/chat -F "message=你好"
```

**响应:**
```
data: {"type":"start","requestId":"f47ac10b-58cc-4372-a567-0e02b2c3d479"}
data: {"type":"content","text":"你好！有什么可以帮助你的？"}
data: {"type":"done"}
```

---

## 多语言调用示例

### Python

```python
import requests

def chat(message, model=None, tools=None, files=None):
    url = 'http://localhost:3456/api/chat'
    data = {'message': message}
    if model: data['model'] = model
    if tools: data['tools'] = ','.join(tools)
    
    files_list = [('files', (f, open(f, 'rb'))) for f in files] if files else None
    
    with requests.post(url, data=data, files=files_list, stream=True) as r:
        for line in r.iter_content():
            if line:
                for l in line.decode().split('\n'):
                    if l.startswith('data: '):
                        print(l[6:])

chat("你好", model="claude-opus-4-20250514", tools=["Read", "Bash"])
```

### Python (完整客户端)

```python
import requests
import json
from typing import Optional, List
from dataclasses import dataclass
from enum import Enum

class EventType(Enum):
    START = "start"
    CONTENT = "content"
    FILE = "file"
    ERROR = "error"
    DONE = "done"

@dataclass
class ChatEvent:
    type: EventType
    text: str = None
    file_id: str = None
    filename: str = None
    error: str = None

class NanoClawClient:
    def __init__(self, base_url="http://localhost:3456", api_key: str = None):
        self.base_url = base_url
        self.session = requests.Session()
        if api_key:
            self.session.headers['Authorization'] = f'Bearer {api_key}'
    
    def chat(self, message: str, model: str = None, 
              tools: List[str] = None, files: List[str] = None) -> List[ChatEvent]:
        url = f'{self.base_url}/api/chat'
        data = {'message': message}
        if model: data['model'] = model
        if tools: data['tools'] = ','.join(tools)
        
        files_data = [('files', (f, open(f, 'rb'))) for f in files] if files else None
        
        events = []
        resp = self.session.post(url, data=data, files=files_data, stream=True)
        
        buffer = ''
        for chunk in resp.iter_content():
            buffer += chunk.decode()
            for line in buffer.split('\n'):
                if line.startswith('data: '):
                    d = json.loads(line[6:])
                    events.append(ChatEvent(
                        type=EventType(d['type']),
                        text=d.get('text'),
                        file_id=d.get('fileId'),
                        filename=d.get('filename'),
                        error=d.get('error')
                    ))
                    if d.get('text'): print(d['text'], end='')
            buffer = ''
        return events

# 使用
client = NanoClawClient(api_key="your-key")
client.chat("分析这个文件", model="claude-opus-4-20250514", files=["data.csv"])

    def run_skill(self, skill: str, message: str, model: str = None,
                  tools: List[str] = None, files: List[str] = None) -> List[ChatEvent]:
        """运行指定的 Skill"""
        url = f'{self.base_url}/api/skills/run'
        data = {'skill': skill, 'message': message}
        if model: data['model'] = model
        if tools: data['tools'] = ','.join(tools)
        
        files_data = [('files', (f, open(f, 'rb'))) for f in files] if files else None
        
        events = []
        resp = self.session.post(url, data=data, files=files_data, stream=True)
        
        buffer = ''
        for chunk in resp.iter_content():
            buffer += chunk.decode()
            for line in buffer.split('\n'):
                if line.startswith('data: '):
                    d = json.loads(line[6:])
                    events.append(ChatEvent(
                        type=EventType(d['type']),
                        text=d.get('text'),
                        file_id=d.get('fileId'),
                        filename=d.get('filename'),
                        error=d.get('error')
                    ))
                    if d.get('text'): print(d['text'], end='')
            buffer = ''
        return events

# 使用 Skill 生成测试用例
client = NanoClawClient()
result = client.run_skill(
    skill="generate-test",
    message="generate unit tests for this file",
    files=["utils.ts"]
)
```

### Go

```go
package main

import (
	"bytes"
	"fmt"
	"io"
	"mime/multipart"
	"net/http"
	"os"
	"strings"
)

func chat(message, model, tools string) error {
	url := "http://localhost:3456/api/chat"
	
	var buf bytes.Buffer
	w := multipart.NewWriter(&buf)
	w.WriteField("message", message)
	if model != "" { w.WriteField("model", model) }
	if tools != "" { w.WriteField("tools", tools) }
	w.Close()
	
	req, _ := http.NewRequest("POST", url, &buf)
	req.Header.Set("Content-Type", w.FormDataContentType())
	
	resp, _ := http.DefaultClient.Do(req)
	defer resp.Body.Close()
	
	io.Copy(os.Stdout, resp.Body)
	return nil
}

func main() {
	chat("你好", "claude-opus-4-20250514", "Read,Bash")
}
```

### JavaScript

```javascript
async function chat(message, options = {}) {
  const formData = new FormData();
  formData.append('message', message);
  if (options.model) formData.append('model', options.model);
  if (options.tools) formData.append('tools', options.tools.join(','));
  
  const response = await fetch('http://localhost:3456/api/chat', {
    method: 'POST',
    body: formData
  });
  
  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  
  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    
    for (const line of decoder.decode(value).split('\n')) {
      if (line.startsWith('data: ')) {
        console.log(JSON.parse(line.slice(6)));
      }
    }
  }
}

chat('你好', { model: 'claude-opus-4-20250514', tools: ['Read', 'Bash'] });
```

### cURL

```bash
# 基础
curl -X POST http://localhost:3456/api/chat -F "message=你好"

# 带认证
curl -H "Authorization: Bearer your-key" \
  -X POST http://localhost:3456/api/chat \
  -F "message=分析数据" \
  -F "files=@data.csv"
```

---

## 部署指南

### 一、本地部署

```bash
# 克隆项目
git clone https://github.com/your-repo/nanoclaw.git
cd nanoclaw

# 安装
npm install

# 启动
npm run dev

# 或带认证
NANOCLAW_API_KEY=your-secret-key npm run dev
```

### 二、一键部署脚本

```bash
# 完整部署
sudo ./deploy.sh --deploy

# 自定义端口和密钥
sudo ./deploy.sh --deploy -p 8080 -k your-secret-key

# 其他命令
./deploy.sh --start    # 启动
./deploy.sh --stop     # 停止
./deploy.sh --restart   # 重启
./deploy.sh --status    # 状态
./deploy.sh --uninstall # 卸载
```

### 三、Docker 部署

```bash
# 使用 docker-compose
docker-compose up -d

# 或手动
docker build -f Dockerfile.api -t nanoclaw-api .
docker run -d -p 3456:3456 -e NANOCLAW_API_KEY=your-key nanoclaw-api
```

### 四、局域网访问

服务默认绑定 `0.0.0.0`，局域网设备可通过 `http://<IP>:3456` 访问。

获取本机 IP:
```bash
# macOS
ipconfig getifaddr en0

# Linux
hostname -I | awk '{print $1}'
```

---

## 错误处理

### HTTP 状态码

| 状态码 | 说明 |
|--------|------|
| 200 | 成功 |
| 400 | 请求错误 |
| 401 | 未授权 |
| 404 | 资源不存在 |
| 500 | 服务器错误 |

### 错误响应

```json
{
  "error": "错误信息"
}
```

### 常见错误

| 错误 | 解决方案 |
|------|----------|
| Message or file required | 提供 message 参数 |
| Group not found | 检查 group 参数 |
| File type not allowed | 使用支持的文件类型 |
| Unauthorized | 检查 API 密钥 |

---

## 常见问题

### Q: 如何修改端口?
```bash
API_PORT=8080 npm run dev
```

### Q: 如何只让本机访问?
```bash
API_HOST=127.0.0.1 npm run dev
```

### Q: 上传文件大小限制?
默认 50MB，可通过 `API_MAX_FILE_SIZE` 修改。

### Q: local 模式和 container 模式区别?
- local: 使用本机 Claude Code，无需额外依赖
- container: 使用隔离容器，更安全但需要 Docker

### Q: 如何禁用 API?
```bash
API_ENABLED=false npm run dev
```

### Q: 原来 NanoClaw 功能会受影响吗?
不会。API 是独立功能，默认启用，可通过 `API_ENABLED=false` 禁用。

---

## 附录

### 目录结构

```
nanoclaw/
├── src/
│   ├── api/
│   │   ├── server.ts    # API 服务
│   │   └── index.ts    # API 入口
│   ├── index.ts        # 主程序入口
│   └── config.ts       # 配置
├── groups/             # 组目录
├── data/              # 数据目录
├── docs/
│   ├── API.md         # API 文档
│   └── API_TEST.md    # 测试报告
├── deploy.sh          # 一键部署脚本
├── deploy-docker.sh   # Docker 部署脚本
├── docker-compose.yml # Docker Compose 配置
└── Dockerfile.api     # API Docker 镜像
```

### 相关链接

- [Claude Code 官方文档](https://docs.anthropic.com/en/docs/claude-code)
- [Apple Container](https://github.com/apple/container)
- [NanoClaw 项目](https://github.com/gavrielc/nanoclaw)
