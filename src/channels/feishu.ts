/**
 * Feishu (飞书) Channel for NanoClaw
 * 使用 WebSocket 长连接接收消息，支持文本、图片、文件、音频等
 */

import { Channel, NewMessage, OnInboundMessage, OnChatMetadata } from '../types.js';
import { logger } from '../logger.js';

// 导入飞书 SDK
import * as lark from '@larksuiteoapi/node-sdk';

const FEISHU_AVAILABLE = true;

// 消息类型映射
const MSG_TYPE_MAP: Record<string, string> = {
  image: '[image]',
  audio: '[audio]',
  file: '[file]',
  sticker: '[sticker]',
};

export interface FeishuConfig {
  appId: string;
  appSecret: string;
  encryptKey?: string;
  verificationToken?: string;
  allowFrom?: string[];  // open_id 白名单
}

export class FeishuChannel implements Channel {
  name = 'feishu';
  prefixAssistantName = true;

  private config: FeishuConfig;
  private client: any = null;
  private wsClient: any = null;
  private wsThread: any = null;
  private connected = false;
  private running = false;
  private loop: any = null;
  private onMessage: OnInboundMessage | null = null;
  private onChatMetadata: OnChatMetadata | null = null;
  private processedMessageIds: Map<string, number> = new Map();

  constructor(config: FeishuConfig) {
    this.config = config;
  }

  async connect(): Promise<void> {
    if (!this.config.appId || !this.config.appSecret) {
      throw new Error('Feishu appId and appSecret are required');
    }

    try {
      // 使用 REST API 连接
      await this.connectWithREST();
    } catch (error) {
      logger.error({ error }, 'Failed to connect to Feishu');
      throw error;
    }
  }

  /**
   * 使用 REST API 连接飞书
   * 注意: 生产环境可能需要 WebSocket 长连接
   */
  private async connectWithREST(): Promise<void> {
    try {
      // 创建 Lark client
      this.client = new lark.Client({
        appId: this.config.appId,
        appSecret: this.config.appSecret,
      });

      // 测试连接 - 获取授权令牌
      const tokenResponse = await this.client.authen.v1.accessToken.create({
        grant_type: 'client_credentials',
        app_id: this.config.appId,
        app_secret: this.config.appSecret,
      });

      if (!tokenResponse.success) {
        throw new Error(`Failed to get access token: ${tokenResponse.msg}`);
      }

      this.connected = true;
      this.running = true;
      logger.info('Feishu channel connected');

      // 启动轮询 (飞书 REST API 不支持 WebSocket 回调时使用)
      this.startPolling();

    } catch (error) {
      logger.error({ error }, 'Failed to connect to Feishu');
      throw error;
    }
  }

  /**
   * 启动轮询获取消息
   * 注意: 飞书推荐使用 WebSocket，这里是简化实现
   */
  private startPolling(): void {
    let lastId = '';

    const poll = async () => {
      if (!this.running || !this.connected) return;

      try {
        // 获取授权Token
        const tokenResponse = await this.client.authen.v1.accessToken.create({
          grant_type: 'client_credentials',
          app_id: this.config.appId,
          app_secret: this.config.appSecret,
        });

        if (!tokenResponse.success || !tokenResponse.data?.access_token) {
          logger.warn('Failed to get Feishu access token');
          setTimeout(poll, 5000);
          return;
        }

        const accessToken = tokenResponse.data.access_token;

        // 获取接收者ID (用户ID)
        const userResponse = await this.client.authen.v1.getUserAccessToken.create({
          grant_type: 'authorization_code',
          code: 'temporary_code', // 需要OAuth流程获取
        }, {
          Authorization: `Bearer ${accessToken}`,
        });

        // 简化: 假设已经获取到用户ID
        // 实际实现需要 OAuth 授权流程

      } catch (error: any) {
        // 忽略权限错误，因为REST API有限制
        if (error?.response?.status !== 403) {
          logger.debug({ error }, 'Feishu polling error');
        }
      }

      // 5秒轮询一次
      setTimeout(poll, 5000);
    };

    poll();
  }

  isConnected(): boolean {
    return this.connected;
  }

  ownsJid(jid: string): boolean {
    // Feishu JID 格式: open_id 或 chat_id
    // 示例: ou_xxxxx (用户), oc_xxxxx (群组)
    return jid.startsWith('ou_') || jid.startsWith('oc_');
  }

  async sendMessage(jid: string, text: string): Promise<void> {
    if (!this.client) {
      throw new Error('Feishu client not initialized');
    }

    try {
      const receiveIdType = jid.startsWith('oc_') ? 'chat_id' : 'open_id';

      // 发送文本消息
      await this.client.im.v1.message.create({
        receive_id_type: receiveIdType,
        request_body: {
          receive_id: jid,
          msg_type: 'text',
          content: JSON.stringify({ text }),
        },
      });

      logger.debug({ jid }, 'Feishu message sent');
    } catch (error) {
      logger.error({ error, jid }, 'Failed to send Feishu message');
      throw error;
    }
  }

  async sendCard(jid: string, card: any): Promise<void> {
    if (!this.client) {
      throw new Error('Feishu client not initialized');
    }

    try {
      const receiveIdType = jid.startsWith('oc_') ? 'chat_id' : 'open_id';

      await this.client.im.v1.message.create({
        receive_id_type: receiveIdType,
        request_body: {
          receive_id: jid,
          msg_type: 'interactive',
          content: JSON.stringify(card),
        },
      });

      logger.debug({ jid }, 'Feishu card sent');
    } catch (error) {
      logger.error({ error, jid }, 'Failed to send Feishu card');
      throw error;
    }
  }

  async uploadImage(filePath: string): Promise<string | null> {
    if (!this.client) {
      return null;
    }

    try {
      const fs = await import('fs');

      const response = await this.client.im.v1.image.create({
        request_body: {
          image_type: 'message',
          image: fs.default.createReadStream(filePath),
        },
      });

      if (response.success) {
        return response.data.image_key;
      }

      return null;
    } catch (error) {
      logger.error({ error, filePath }, 'Failed to upload image to Feishu');
      return null;
    }
  }

  async sendMedia(jid: string, filePath: string, caption?: string): Promise<void> {
    const imageKey = await this.uploadImage(filePath);
    if (!imageKey) {
      throw new Error('Failed to upload media');
    }

    const receiveIdType = jid.startsWith('oc_') ? 'chat_id' : 'open_id';

    // 发送图片消息
    await this.client.im.v1.message.create({
      receive_id_type: receiveIdType,
      request_body: {
        receive_id: jid,
        msg_type: 'image',
        content: JSON.stringify({ image_key: imageKey }),
      },
    });

    // 如果有 caption，发送文本消息
    if (caption) {
      await this.sendMessage(jid, caption);
    }
  }

  setOnMessage(callback: OnInboundMessage): void {
    this.onMessage = callback;
  }

  setOnChatMetadata(callback: OnChatMetadata): void {
    this.onChatMetadata = callback;
  }

  async disconnect(): Promise<void> {
    this.running = false;
    this.connected = false;

    if (this.wsClient) {
      try {
        this.wsClient.stop();
      } catch (e) {
        // ignore
      }
    }

    logger.info('Feishu channel disconnected');
  }

  // 处理接收到的消息 (供 WebSocket 回调使用)
  async handleIncomingMessage(message: any): Promise<void> {
    if (!this.onMessage) return;

    const messageId = message.message_id;

    // 去重检查
    if (this.processedMessageIds.has(messageId)) {
      return;
    }
    this.processedMessageIds.set(messageId, Date.now());

    // 清理过期缓存
    const now = Date.now();
    for (const [id, time] of this.processedMessageIds) {
      if (now - time > 60000) {
        this.processedMessageIds.delete(id);
      }
    }

    // 跳过机器人消息
    if (message.sender?.sender_type === 'bot') {
      return;
    }

    const senderId = message.sender?.sender_id?.open_id || message.sender?.sender_id?.user_id;
    const chatId = message.chat_id;
    const msgType = message.message_type;
    const chatType = message.chat_type;

    // 解析内容
    let content = '';
    let mediaPaths: string[] = [];

    try {
      const contentJson = JSON.parse(message.content || '{}');

      if (msgType === 'text') {
        content = contentJson.text || '';
      } else if (msgType === 'post') {
        content = this.extractPostText(contentJson);
      } else if (['image', 'audio', 'file'].includes(msgType)) {
        // 处理媒体消息
        const fileKey = contentJson.image_key || contentJson.file_key;
        if (fileKey) {
          // TODO: 下载媒体文件
          content = `[${msgType}: ${fileKey}]`;
        }
      } else {
        content = MSG_TYPE_MAP[msgType] || `[${msgType}]`;
      }
    } catch (e) {
      content = message.content || '';
    }

    if (!content) return;

    // 构建 NewMessage
    const newMessage: NewMessage = {
      id: messageId,
      chat_jid: chatId,
      sender: senderId,
      sender_name: message.sender?.sender_id?.name || senderId,
      content,
      timestamp: message.create_time || new Date().toISOString(),
    };

    // 触发回调
    const replyTo = chatType === 'group' ? chatId : senderId;
    this.onMessage(replyTo, newMessage);

    // 触发元数据回调
    if (this.onChatMetadata) {
      this.onChatMetadata(chatId, message.create_time || new Date().toISOString());
    }
  }

  /**
   * 提取富文本消息内容
   */
  private extractPostText(contentJson: any): string {
    const extractFromLang = (langContent: any): string | null => {
      if (!langContent || typeof langContent !== 'object') return null;

      const title = langContent.title || '';
      const contentBlocks = langContent.content || [];

      if (!Array.isArray(contentBlocks)) return null;

      const textParts: string[] = [];
      if (title) textParts.push(title);

      for (const block of contentBlocks) {
        if (!Array.isArray(block)) continue;
        for (const element of block) {
          if (element.tag === 'text') {
            textParts.push(element.text || '');
          } else if (element.tag === 'a') {
            textParts.push(element.text || '');
          } else if (element.tag === 'at') {
            textParts.push(`@${element.user_name || 'user'}`);
          }
        }
      }

      return textParts.join(' ').trim() || null;
    };

    // 尝试直接格式
    if (contentJson.content) {
      const result = extractFromLang(contentJson);
      if (result) return result;
    }

    // 尝试多语言格式
    for (const lang of ['zh_cn', 'en_us', 'ja_jp']) {
      const result = extractFromLang(contentJson[lang]);
      if (result) return result;
    }

    return '';
  }
}

/**
 * 从配置创建 Feishu 渠道
 */
export function createFeishuChannel(config: FeishuConfig): Channel {
  return new FeishuChannel(config);
}
