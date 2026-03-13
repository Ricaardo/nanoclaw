/**
 * Channel Manager for NanoClaw
 * 统一管理多渠道的注册、路由、消息收发
 */

import { Channel, NewMessage } from './types.js';
import { logger } from './logger.js';

export interface ChannelInfo {
  channel: Channel;
  jidPatterns: RegExp[];
}

export class ChannelManager {
  private channels: Map<string, Channel> = new Map();
  private channelJidMap: Map<string, Channel> = new Map();

  /**
   * 注册一个渠道
   */
  register(channel: Channel): void {
    if (this.channels.has(channel.name)) {
      logger.warn({ name: channel.name }, 'Channel already registered, replacing');
    }

    this.channels.set(channel.name, channel);
    logger.info({ name: channel.name, connected: channel.isConnected() }, 'Channel registered');
  }

  /**
   * 注销一个渠道
   */
  async unregister(name: string): Promise<void> {
    const channel = this.channels.get(name);
    if (!channel) {
      logger.warn({ name }, 'Channel not found');
      return;
    }

    try {
      await channel.disconnect();
    } catch (e) {
      logger.warn({ name, error: e }, 'Error disconnecting channel');
    }

    this.channels.delete(name);
    logger.info({ name }, 'Channel unregistered');
  }

  /**
   * 根据 JID 查找对应的渠道
   */
  getByJid(jid: string): Channel | undefined {
    // 首先尝试精确匹配
    for (const channel of this.channels.values()) {
      if (channel.ownsJid(jid)) {
        return channel;
      }
    }

    // 如果没有精确匹配，尝试前缀匹配
    for (const channel of this.channels.values()) {
      if (this.channelOwnsJidPrefix(channel, jid)) {
        return channel;
      }
    }

    return undefined;
  }

  /**
   * 检查渠道是否拥有该 JID (支持前缀匹配)
   */
  private channelOwnsJidPrefix(channel: Channel, jid: string): boolean {
    // 实现前缀匹配逻辑
    // 例如: feishu:ou_xxx -> 返回 feishu 渠道
    return false; // 默认不启用前缀匹配
  }

  /**
   * 获取所有已连接的渠道
   */
  getConnected(): Channel[] {
    return Array.from(this.channels.values()).filter(c => c.isConnected());
  }

  /**
   * 获取所有渠道
   */
  getAll(): Channel[] {
    return Array.from(this.channels.values());
  }

  /**
   * 根据名称获取渠道
   */
  get(name: string): Channel | undefined {
    return this.channels.get(name);
  }

  /**
   * 检查是否有任何渠道已连接
   */
  hasConnected(): boolean {
    return this.getConnected().length > 0;
  }

  /**
   * 列出所有渠道状态
   */
  listStatus(): { name: string; connected: boolean }[] {
    return Array.from(this.channels.entries()).map(([name, channel]) => ({
      name,
      connected: channel.isConnected(),
    }));
  }

  /**
   * 断开所有渠道
   */
  async disconnectAll(): Promise<void> {
    const promises: Promise<void>[] = [];

    for (const channel of this.channels.values()) {
      promises.push(
        channel.disconnect().catch((e) => {
          logger.warn({ name: channel.name, error: e }, 'Error disconnecting');
        })
      );
    }

    await Promise.all(promises);
    logger.info('All channels disconnected');
  }
}

// 默认导出
export default ChannelManager;
