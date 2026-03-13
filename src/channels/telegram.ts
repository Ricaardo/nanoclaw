/**
 * Telegram Channel for NanoClaw
 * 使用 Telegram Bot API 收发消息
 */

import { Channel, NewMessage, OnInboundMessage, OnChatMetadata } from '../types.js';
import { logger } from '../logger.js';

export interface TelegramConfig {
  botToken: string;
  allowedUsernames?: string[];  // 用户名白名单
  allowedChatIds?: number[];   // 聊天ID白名单
  groupPolicy?: 'mention' | 'open' | 'allowlist';  // 群组策略
}

interface TelegramUpdate {
  update_id: number;
  message?: TelegramMessage;
  edited_message?: TelegramMessage;
  callback_query?: TelegramCallbackQuery;
}

interface TelegramMessage {
  message_id: number;
  from?: TelegramUser;
  chat: TelegramChat;
  date: number;
  text?: string;
  photo?: TelegramPhoto[];
  document?: TelegramDocument;
  voice?: TelegramVoice;
  sticker?: TelegramSticker;
}

interface TelegramUser {
  id: number;
  is_bot: boolean;
  first_name: string;
  last_name?: string;
  username?: string;
  language_code?: string;
}

interface TelegramChat {
  id: number;
  type: 'private' | 'group' | 'supergroup' | 'channel';
  title?: string;
  username?: string;
  first_name?: string;
  last_name?: string;
}

interface TelegramPhoto {
  file_id: string;
  width: number;
  height: number;
  file_size?: number;
}

interface TelegramDocument {
  file_id: string;
  file_name?: string;
  file_size?: number;
}

interface TelegramVoice {
  file_id: string;
  duration: number;
  mime_type?: string;
  file_size?: number;
}

interface TelegramSticker {
  file_id: string;
  width: number;
  height: number;
  is_animated?: boolean;
}

interface TelegramCallbackQuery {
  id: string;
  from: TelegramUser;
  message?: TelegramMessage;
  data?: string;
}

export class TelegramChannel implements Channel {
  name = 'telegram';
  prefixAssistantName = false;  // Telegram bot 已显示名称

  private config: TelegramConfig;
  private botToken: string;
  private connected = false;
  private running = false;
  private pollingOffset = 0;
  private onMessage: OnInboundMessage | null = null;
  private onChatMetadata: OnChatMetadata | null = null;
  private processedMessageIds: Set<number> = new Set();

  constructor(config: TelegramConfig) {
    this.config = config;
    this.botToken = config.botToken;
  }

  async connect(): Promise<void> {
    if (!this.botToken) {
      throw new Error('Telegram botToken is required');
    }

    try {
      // 测试连接 - 获取 bot 信息
      const response = await this.apiCall('getMe', {});
      if (!response.ok) {
        throw new Error(`Telegram API error: ${response.status}`);
      }

      const botInfo = await response.json() as { result: { username: string } };
      logger.info({ username: botInfo.result.username }, 'Telegram bot connected');

      this.connected = true;
      this.running = true;

      // 启动长轮询
      this.startPolling();

    } catch (error) {
      logger.error({ error }, 'Failed to connect to Telegram');
      throw error;
    }
  }

  /**
   * 调用 Telegram Bot API
   */
  private async apiCall(method: string, params: Record<string, any>): Promise<Response> {
    const url = `https://api.telegram.org/bot${this.botToken}/${method}`;
    return fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(params),
    });
  }

  /**
   * 启动长轮询获取消息
   */
  private async startPolling(): Promise<void> {
    const poll = async () => {
      if (!this.running || !this.connected) return;

      try {
        const response = await this.apiCall('getUpdates', {
          timeout: 30,
          offset: this.pollingOffset + 1,
          allowed_updates: ['message', 'edited_message', 'callback_query'],
        });

        if (!response.ok) {
          logger.warn({ status: response.status }, 'Telegram polling error');
          setTimeout(poll, 5000);
          return;
        }

        const data = await response.json() as { ok: boolean; result: TelegramUpdate[] };

        if (data.ok && data.result) {
          for (const update of data.result) {
            await this.handleUpdate(update);
            this.pollingOffset = update.update_id;
          }
        }

      } catch (error) {
        logger.error({ error }, 'Telegram polling failed');
      }

      // 继续轮询
      setTimeout(poll, 1000);
    };

    poll();
  }

  /**
   * 处理收到的更新
   */
  private async handleUpdate(update: TelegramUpdate): Promise<void> {
    const message = update.message || update.callback_query?.message;
    if (!message) return;

    // 去重检查
    if (this.processedMessageIds.has(message.message_id)) {
      return;
    }
    this.processedMessageIds.add(message.message_id);

    // 清理过期缓存
    if (this.processedMessageIds.size > 1000) {
      const arr = Array.from(this.processedMessageIds);
      this.processedMessageIds = new Set(arr.slice(-500));
    }

    // 跳过机器人消息
    if (message.from?.is_bot) {
      return;
    }

    // 白名单检查
    if (!this.isAllowed(message)) {
      return;
    }

    // 解析消息内容
    let content = '';
    const mediaPaths: string[] = [];

    if (message.text) {
      content = message.text;
    } else if (message.photo) {
      content = '[photo]';
      // TODO: 下载图片
    } else if (message.document) {
      content = `[document: ${message.document.file_name || 'file'}]`;
    } else if (message.voice) {
      content = '[voice]';
    } else if (message.sticker) {
      content = '[sticker]';
    }

    if (!content) return;

    // 构建 NewMessage
    const chat = message.chat;
    const chatId = String(chat.id);

    const newMessage: NewMessage = {
      id: String(message.message_id),
      chat_jid: chatId,
      sender: String(message.from?.id || 'unknown'),
      sender_name: message.from?.username || message.from?.first_name || 'Unknown',
      content,
      timestamp: new Date(message.date * 1000).toISOString(),
    };

    // 触发回调
    if (this.onMessage) {
      this.onMessage(chatId, newMessage);
    }

    // 触发元数据回调
    if (this.onChatMetadata) {
      this.onChatMetadata(chatId, newMessage.timestamp, chat.title || chat.username);
    }
  }

  /**
   * 检查是否允许处理该消息
   */
  private isAllowed(message: TelegramMessage): boolean {
    const from = message.from;
    const chat = message.chat;

    if (!from) return false;

    // 私聊: 检查用户名白名单
    if (chat.type === 'private') {
      if (this.config.allowedUsernames && this.config.allowedUsernames.length > 0) {
        return !!(from.username && this.config.allowedUsernames.includes(from.username));
      }
      if (this.config.allowedChatIds && this.config.allowedChatIds.length > 0) {
        return this.config.allowedChatIds.includes(from.id);
      }
      return true;  // 无白名单则允许
    }

    // 群聊: 检查群组策略
    if (chat.type === 'group' || chat.type === 'supergroup') {
      const policy = this.config.groupPolicy || 'mention';

      if (policy === 'allowlist') {
        return !!(this.config.allowedChatIds && this.config.allowedChatIds.includes(chat.id));
      }

      // mention 和 open 都允许
      return true;
    }

    return false;
  }

  isConnected(): boolean {
    return this.connected;
  }

  ownsJid(jid: string): boolean {
    // Telegram JID 格式: 数字ID
    return /^\d+$/.test(jid);
  }

  async sendMessage(jid: string, text: string): Promise<void> {
    if (!this.connected) {
      throw new Error('Telegram bot not connected');
    }

    const chatId = jid;

    try {
      // 分割长消息 (Telegram 限制 4096 字符)
      const maxLength = 4096;
      const messages = this.splitMessage(text, maxLength);

      for (const msg of messages) {
        const response = await this.apiCall('sendMessage', {
          chat_id: chatId,
          text: msg,
          parse_mode: 'Markdown',
        });

        if (!response.ok) {
          // 如果 Markdown 解析失败，尝试纯文本
          const errorData = await response.json() as { description?: string };
          if (errorData.description?.includes('parse')) {
            await this.apiCall('sendMessage', {
              chat_id: chatId,
              text: msg,
            });
          }
        }
      }

      logger.debug({ jid, messages: messages.length }, 'Telegram message sent');
    } catch (error) {
      logger.error({ error, jid }, 'Failed to send Telegram message');
      throw error;
    }
  }

  /**
   * 分割长消息
   */
  private splitMessage(text: string, maxLength: number): string[] {
    if (text.length <= maxLength) {
      return [text];
    }

    const messages: string[] = [];
    const lines = text.split('\n');
    let current = '';

    for (const line of lines) {
      if ((current + '\n' + line).length <= maxLength) {
        current += (current ? '\n' : '') + line;
      } else {
        if (current) messages.push(current);
        current = line;
      }
    }

    if (current) messages.push(current);

    return messages;
  }

  async sendMedia(jid: string, filePath: string, caption?: string): Promise<void> {
    if (!this.connected) {
      throw new Error('Telegram bot not connected');
    }

    try {
      const fs = await import('fs');

      // 读取文件
      const fileBuffer = fs.readFileSync(filePath);
      const fileName = filePath.split('/').pop() || 'file';

      // 创建 FormData
      const formData = new FormData();
      formData.append('chat_id', jid);
      if (caption) {
        formData.append('caption', caption);
      }

      // 根据文件类型选择方法
      const ext = fileName.split('.').pop()?.toLowerCase();
      const isPhoto = ['jpg', 'jpeg', 'png', 'gif', 'webp'].includes(ext || '');
      const method = isPhoto ? 'sendPhoto' : 'sendDocument';

      formData.append(isPhoto ? 'photo' : 'document', new Blob([fileBuffer]), fileName);

      const response = await fetch(
        `https://api.telegram.org/bot${this.botToken}/${method}`,
        { method: 'POST', body: formData }
      );

      if (!response.ok) {
        throw new Error(`Telegram API error: ${response.status}`);
      }

      logger.debug({ jid, file: fileName }, 'Telegram media sent');
    } catch (error) {
      logger.error({ error, jid }, 'Failed to send Telegram media');
      throw error;
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
    logger.info('Telegram channel disconnected');
  }
}

/**
 * 从配置创建 Telegram 渠道
 */
export function createTelegramChannel(config: TelegramConfig): Channel {
  return new TelegramChannel(config);
}
