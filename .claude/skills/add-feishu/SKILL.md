---
name: add-feishu
description: 添加飞书 (Feishu) 渠道到 NanoClaw。支持文本、图片、文件消息收发。触发条件: "add feishu", "添加飞书", "setup feishu", "configure feishu"
---

# 添加飞书渠道

本 skill 将帮助你在 NanoClaw 中添加飞书 (Feishu/Lark) 消息渠道。

## 前提条件

1. 有一个飞书企业账号
2. 能够在飞书开放平台创建应用

## 步骤

### Step 1: 在飞书开放平台创建应用

1. 访问 [飞书开放平台](https://open.feishu.cn/)
2. 点击「创建应用」
3. 输入应用名称（如 NanoClaw）
4. 点击「确定创建」

### Step 2: 配置应用权限

1. 在应用详情页，点击「权限管理」
2. 添加以下权限：
   - `im:message` - 发送消息
   - `im:message:receive_v1` - 接收消息
   - `im:resource` - 图片/文件资源
   - `contact:user.base` - 获取用户基本信息

### Step 3: 创建机器人

1. 在应用详情页，点击「添加应用能力」
2. 选择「机器人」
3. 点击「确定」

### Step 4: 发布应用

1. 点击「版本管理与发布」
2. 创建新版本
3. 填写版本信息
4. 点击「申请发布」
5. 企业管理员审批后即可使用

### Step 5: 配置 NanoClaw

获取应用的 App ID 和 App Secret：
1. 在应用详情页，点击「凭证与基础信息」
2. 复制 App ID 和 App Secret

设置环境变量或配置文件：

```bash
# 方式 1: 环境变量
export FEISHU_ENABLED=true
export FEISHU_APP_ID=cli_xxxxx
export FEISHU_APP_SECRET=xxxxx
```

或者修改启动脚本。

### Step 6: 重启 NanoClaw

```bash
# 停止服务
launchctl unload ~/Library/LaunchAgents/com.nanoclaw.plist

# 启动服务
launchctl load ~/Library/LaunchAgents/com.nanoclaw.plist
```

## 功能

添加飞书渠道后，你可以：

- ✅ 发送和接收文本消息
- ✅ 发送和接收图片
- ✅ 发送和接收文件
- ✅ 群聊和私聊支持
- ✅ @mention 触发 Agent

## 触发方式

在飞书中：
- 私聊：直接发送消息
- 群聊：@机器人名称 触发

## 故障排除

**问题：无法连接**
- 检查 App ID 和 App Secret 是否正确
- 检查应用是否已发布
- 检查权限是否配置正确

**问题：收不到消息**
- 检查是否在应用详情页启用了「机器人」
- 检查事件订阅是否正确配置
- 检查网络连接

## 相关文档

- [飞书开放平台文档](https://open.feishu.cn/document/)
- [NanoClaw 文档](../README.md)
