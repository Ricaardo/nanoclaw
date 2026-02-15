import { spawn, ChildProcess } from 'child_process';
import os from 'os';
import path from 'path';
import readline from 'readline';

import { IMESSAGE_CLI_PATH, IMESSAGE_DB_PATH } from '../config.js';
import { logger } from '../logger.js';
import {
  Channel,
  OnInboundMessage,
  OnChatMetadata,
  RegisteredGroup,
} from '../types.js';

export interface IMessageChannelOpts {
  onMessage: OnInboundMessage;
  onChatMetadata: OnChatMetadata;
  registeredGroups: () => Record<string, RegisteredGroup>;
}

interface IMessageChat {
  id: string;
  displayName: string;
  isGroup: boolean;
}

interface RpcResponse {
  jsonrpc?: string;
  id?: string;
  result?: any;
  error?: { message?: string };
  method?: string;
  params?: any;
}

export class IMessageChannel implements Channel {
  name = 'imessage';
  prefixAssistantName = true;

  private opts: IMessageChannelOpts;
  private cliPath: string;
  private dbPath: string;
  private rpcProcess: ChildProcess | null = null;
  private rl: readline.Interface | null = null;
  private pendingRequests: Map<string, { resolve: (v: any) => void; reject: (e: Error) => void }> =
    new Map();
  private chats: Map<string, IMessageChat> = new Map();

  constructor(cliPath: string, dbPath: string, opts: IMessageChannelOpts) {
    this.cliPath = cliPath;
    this.dbPath = dbPath;
    this.opts = opts;
  }

  async connect(): Promise<void> {
    await this.startRpcDaemon();
    await this.fetchChats();
    logger.info('iMessage channel connected');
    console.log('\n  iMessage channel ready');
  }

  private async startRpcDaemon(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const args = ['rpc', '--db-path', this.dbPath, '--json'];

      this.rpcProcess = spawn(this.cliPath, args, {
        stdio: ['pipe', 'pipe', 'pipe'],
      });

      this.rl = readline.createInterface({
        input: this.rpcProcess.stdout as NodeJS.ReadableStream,
        crlfDelay: Infinity,
      });

      this.rpcProcess.stderr?.on('data', (data: Buffer) => {
        logger.debug({ err: data.toString() }, 'imsg stderr');
      });

      this.rpcProcess.on('error', (err: Error) => {
        logger.error({ err }, 'imsg rpc process error');
        reject(err);
      });

      this.rpcProcess.on('close', (code: number) => {
        logger.info({ code }, 'imsg rpc process exited');
      });

      this.rl.on('line', (line: string) => {
        this.handleRpcResponse(line);
      });

      this.rpcProcess.stdin?.on('error', (err: Error) => {
        logger.error({ err }, 'imsg stdin error');
      });

      setTimeout(resolve, 1000);
    });
  }

  private async rpcCall(method: string, params: Record<string, any> = {}): Promise<any> {
    const id = Math.random().toString(36).substring(7);

    return new Promise((resolve, reject) => {
      const request = { jsonrpc: '2.0', method, params, id };
      this.pendingRequests.set(id, { resolve, reject });

      this.rpcProcess?.stdin?.write(JSON.stringify(request) + '\n');

      setTimeout(() => {
        if (this.pendingRequests.has(id)) {
          this.pendingRequests.delete(id);
          reject(new Error(`RPC call ${method} timed out`));
        }
      }, 30000);
    });
  }

  private handleRpcResponse(line: string): void {
    try {
      const response: RpcResponse = JSON.parse(line);

      if (response.id && this.pendingRequests.has(response.id)) {
        const { resolve, reject } = this.pendingRequests.get(response.id)!;
        this.pendingRequests.delete(response.id);

        if (response.error) {
          reject(new Error(response.error.message || 'Unknown error'));
        } else {
          resolve(response.result);
        }
        return;
      }

      if (response.method === 'message') {
        this.handleInboundMessage(response.params);
      }
    } catch (err) {
      logger.debug({ line, err }, 'Failed to parse RPC response');
    }
  }

  private async handleInboundMessage(params: any): Promise<void> {
    const chatId = params.chatId || params.chat_id;
    const text = params.text || params.body || '';
    const senderId = params.senderId || params.sender_id || '';
    const timestamp = params.timestamp
      ? new Date(params.timestamp * 1000).toISOString()
      : new Date().toISOString();

    if (!chatId || !text) return;

    const chatJid = `imessage:${chatId}`;
    const group = this.opts.registeredGroups()[chatJid];

    if (!group) {
      logger.debug({ chatJid }, 'Message from unregistered iMessage chat');
      return;
    }

    const senderName =
      params.senderName ||
      params.sender_name ||
      this.chats.get(chatId)?.displayName ||
      'Unknown';
    const msgId = params.messageId || params.message_id || Date.now().toString();

    this.opts.onChatMetadata(
      chatJid,
      timestamp,
      this.chats.get(chatId)?.displayName,
    );

    this.opts.onMessage(chatJid, {
      id: msgId,
      chat_jid: chatJid,
      sender: senderId,
      sender_name: senderName,
      content: text,
      timestamp,
      is_from_me: false,
    });

    logger.info({ chatJid, senderName }, 'iMessage stored');
  }

  private async fetchChats(): Promise<void> {
    try {
      const result = await this.rpcCall('chats.list');

      if (result?.chats) {
        for (const chat of result.chats) {
          this.chats.set(chat.id, {
            id: chat.id,
            displayName: chat.displayName || chat.name || chat.id,
            isGroup: chat.isGroup || chat.is_group || false,
          });
        }
      }
    } catch (err) {
      logger.warn({ err }, 'Failed to fetch iMessage chats');
    }
  }

  async sendMessage(jid: string, text: string): Promise<void> {
    if (!this.rpcProcess) {
      logger.warn('iMessage rpc not initialized');
      return;
    }

    try {
      const chatId = jid.replace(/^imessage:/, '');

      await this.rpcCall('messages.send', {
        chatId,
        text,
      });

      logger.info({ jid, length: text.length }, 'iMessage sent');
    } catch (err) {
      logger.error({ jid, err }, 'Failed to send iMessage');
    }
  }

  isConnected(): boolean {
    return this.rpcProcess !== null;
  }

  ownsJid(jid: string): boolean {
    return jid.startsWith('imessage:');
  }

  async disconnect(): Promise<void> {
    if (this.rpcProcess) {
      this.rpcProcess.kill();
      this.rpcProcess = null;
      this.rl = null;
      logger.info('iMessage channel stopped');
    }
  }

  async setTyping(jid: string, isTyping: boolean): Promise<void> {
    // iMessage doesn't support typing indicators via imsg
  }
}
