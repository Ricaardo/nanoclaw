---
name: add-imessage
description: Add iMessage as a channel. Can replace WhatsApp entirely or run alongside it. Also configurable as a control-only channel or passive channel for notifications.
---

# Add iMessage Channel

This skill adds iMessage support to NanoClaw. Users can choose to:

1. **Replace WhatsApp** - Use iMessage as the only messaging channel
2. **Add alongside WhatsApp** - Both channels active
3. **Control channel** - iMessage triggers agent but doesn't receive all outputs
4. **Notification channel** - Receives outputs but limited triggering

## Prerequisites

### 1. Install imsg CLI

```bash
brew install steipete/tap/imsg
```

imsg is a command-line tool for macOS that brings iMessage to your terminal. It uses AppleScript and read-only DB access - no private Apple APIs.

### 2. Verify imsg Works

```bash
imsg rpc --help
```

If you get a permission error, you may need to grant Automation permissions in System Preferences > Security & Privacy > Privacy > Automation.

### 3. Grant Full Disk Access (for reading messages)

For imsg to read messages from the Messages database, grant Full Disk Access:

1. Go to System Preferences > Security & Privacy > Privacy > Full Disk Access
2. Add Terminal (or the app you run nanoclaw from)
3. Or run: `open /System/Library/PreferencePanes/Security.prefPane`

## Questions to Ask

Before making changes, ask:

1. **Mode**: Replace WhatsApp or add alongside it?
   - If replace: Set `IMESSAGE_ONLY=true`
   - If alongside: Both will run

2. **Chat behavior**: Should this chat respond to all messages or only when triggered?
   - Main chat: Responds to all (set `requiresTrigger: false`)
   - Other chats: Default requires trigger (`requiresTrigger: true`)

## Architecture

NanoClaw uses a **Channel abstraction** (`Channel` interface in `src/types.ts`). Each messaging platform implements this interface. Key files:

| File | Purpose |
|------|---------|
| `src/types.ts` | `Channel` interface definition |
| `src/channels/whatsapp.ts` | `WhatsAppChannel` class (reference implementation) |
| `src/router.ts` | `findChannel()`, `routeOutbound()`, `formatOutbound()` |
| `src/index.ts` | Orchestrator: creates channels, wires callbacks, starts subsystems |
| `src/ipc.ts` | IPC watcher (uses `sendMessage` dep for outbound) |

The iMessage channel follows the same pattern as WhatsApp:
- Implements `Channel` interface (`connect`, `sendMessage`, `ownsJid`, `disconnect`, `setTyping`)
- Delivers inbound messages via `onMessage` / `onChatMetadata` callbacks
- Uses `imsg rpc` for communication (JSON-RPC over stdio)

## Implementation

### Step 1: Update Configuration

Read `src/config.ts` and add iMessage config exports:

```typescript
export const IMESSAGE_ONLY = process.env.IMESSAGE_ONLY === "true";
export const IMESSAGE_CLI_PATH = process.env.IMESSAGE_CLI_PATH || "/usr/local/bin/imsg";
export const IMESSAGE_DB_PATH = process.env.IMESSAGE_DB_PATH || 
  path.join(os.homedir(), "Library/Messages/chat.db");
```

These should be added near the top with other configuration exports.

### Step 2: Create iMessage Channel

Create `src/channels/imessage.ts` implementing the `Channel` interface. Use `src/channels/whatsapp.ts` as a reference for the pattern.

```typescript
import { spawn } from "child_process";
import readline from "readline";

import { ASSISTANT_NAME, TRIGGER_PATTERN, IMESSAGE_CLI_PATH, IMESSAGE_DB_PATH } from "../config.js";
import { logger } from "../logger.js";
import { Channel, OnInboundMessage, OnChatMetadata, RegisteredGroup } from "../types.js";

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

export class IMessageChannel implements Channel {
  name = "imessage";
  prefixAssistantName = true;

  private opts: IMessageChannelOpts;
  private cliPath: string;
  private dbPath: string;
  private rpcProcess: any = null;
  private rl: readline.Interface | null = null;
  private pendingRequests: Map<string, any> = new Map();
  private chats: Map<string, IMessageChat> = new Map();

  constructor(cliPath: string, dbPath: string, opts: IMessageChannelOpts) {
    this.cliPath = cliPath;
    this.dbPath = dbPath;
    this.opts = opts;
  }

  async connect(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      this.startRpcDaemon()
        .then(() => this.fetchChats())
        .then(() => {
          logger.info("iMessage channel connected");
          console.log("\n  iMessage channel ready");
          resolve();
        })
        .catch(reject);
    });
  }

  private async startRpcDaemon(): Promise<void> {
    return new Promise<void>((resolve, reject) => {
      const args = [
        "rpc",
        "--db-path", this.dbPath,
        "--json"
      ];

      this.rpcProcess = spawn(this.cliPath, args, {
        stdio: ["pipe", "pipe", "pipe"]
      });

      this.rl = readline.createInterface({
        input: this.rpcProcess.stdout,
        crlfDelay: Infinity
      });

      this.rpcProcess.stderr.on("data", (data: Buffer) => {
        logger.debug({ err: data.toString() }, "imsg stderr");
      });

      this.rpcProcess.on("error", (err: Error) => {
        logger.error({ err }, "imsg rpc process error");
        reject(err);
      });

      this.rpcProcess.on("close", (code: number) => {
        logger.info({ code }, "imsg rpc process exited");
      });

      this.rl.on("line", (line: string) => {
        this.handleRpcResponse(line);
      });

      this.rpcProcess.stdin.on("error", (err: Error) => {
        logger.error({ err }, "imsg stdin error");
      });

      setTimeout(resolve, 1000);
    });
  }

  private async rpcCall(method: string, params: any = {}): Promise<any> {
    const id = Math.random().toString(36).substring(7);
    
    return new Promise((resolve, reject) => {
      const request = { jsonrpc: "2.0", method, params, id };
      this.pendingRequests.set(id, { resolve, reject });
      
      this.rpcProcess.stdin.write(JSON.stringify(request) + "\n");
      
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
      const response = JSON.parse(line);
      
      if (response.id && this.pendingRequests.has(response.id)) {
        const { resolve, reject } = this.pendingRequests.get(response.id);
        this.pendingRequests.delete(response.id);
        
        if (response.error) {
          reject(new Error(response.error.message || response.error));
        } else {
          resolve(response.result);
        }
        return;
      }

      if (response.method === "message") {
        this.handleInboundMessage(response.params);
      }
    } catch (err) {
      logger.debug({ line, err }, "Failed to parse RPC response");
    }
  }

  private async handleInboundMessage(params: any): Promise<void> {
    const chatId = params.chatId || params.chat_id;
    const text = params.text || params.body || "";
    const senderId = params.senderId || params.sender_id || "";
    const timestamp = params.timestamp ? new Date(params.timestamp * 1000).toISOString() : new Date().toISOString();
    
    if (!chatId || !text) return;

    const chatJid = `imessage:${chatId}`;
    const group = this.opts.registeredGroups()[chatJid];
    
    if (!group) {
      logger.debug({ chatJid }, "Message from unregistered iMessage chat");
      return;
    }

    const senderName = params.senderName || params.sender_name || this.chats.get(chatId)?.displayName || "Unknown";
    const msgId = params.messageId || params.message_id || Date.now().toString();

    this.opts.onChatMetadata(chatJid, timestamp, this.chats.get(chatId)?.displayName);

    this.opts.onMessage(chatJid, {
      id: msgId,
      chat_jid: chatJid,
      sender: senderId,
      sender_name: senderName,
      content: text,
      timestamp,
      is_from_me: false,
    });

    logger.info({ chatJid, senderName }, "iMessage stored");
  }

  private async fetchChats(): Promise<void> {
    try {
      const result = await this.rpcCall("chats.list");
      
      if (result && result.chats) {
        for (const chat of result.chats) {
          this.chats.set(chat.id, {
            id: chat.id,
            displayName: chat.displayName || chat.name || chat.id,
            isGroup: chat.isGroup || chat.is_group || false
          });
        }
      }
    } catch (err) {
      logger.warn({ err }, "Failed to fetch iMessage chats");
    }
  }

  async sendMessage(jid: string, text: string): Promise<void> {
    if (!this.rpcProcess) {
      logger.warn("iMessage rpc not initialized");
      return;
    }

    try {
      const chatId = jid.replace(/^imessage:/, "");
      
      await this.rpcCall("messages.send", {
        chatId,
        text
      });
      
      logger.info({ jid, length: text.length }, "iMessage sent");
    } catch (err) {
      logger.error({ jid, err }, "Failed to send iMessage");
    }
  }

  isConnected(): boolean {
    return this.rpcProcess !== null;
  }

  ownsJid(jid: string): boolean {
    return jid.startsWith("imessage:");
  }

  async disconnect(): Promise<void> {
    if (this.rpcProcess) {
      this.rpcProcess.kill();
      this.rpcProcess = null;
      this.rl = null;
      logger.info("iMessage channel stopped");
    }
  }

  async setTyping(jid: string, isTyping: boolean): Promise<void> {
    // iMessage doesn't support typing indicators via imsg
  }
}
```

Key differences from WhatsApp:
- Uses `imsg rpc` process for communication (JSON-RPC over stdio)
- `prefixAssistantName = true` - iMessage displays contact names, needs prefix
- No typing indicator support (iMessage limitation)
- Chat IDs use `imessage:` prefix

### Step 3: Update Main Application

Modify `src/index.ts` to support multiple channels. Read the file first to understand the current structure.

1. **Add imports** at the top:

```typescript
import { IMessageChannel } from "./channels/imessage.js";
import { IMESSAGE_ONLY, IMESSAGE_CLI_PATH, IMESSAGE_DB_PATH } from "./config.js";
import { findChannel } from "./router.js";
```

2. **Add a channels array** alongside the existing `whatsapp` variable:

```typescript
let whatsapp: WhatsAppChannel;
const channels: Channel[] = [];
```

Import `Channel` from `./types.js` if not already imported.

3. **Update `processGroupMessages`** to find the correct channel for the JID instead of using `whatsapp` directly. Replace the direct `whatsapp.setTyping()` and `whatsapp.sendMessage()` calls:

```typescript
// Find the channel that owns this JID
const channel = findChannel(channels, chatJid);
if (!channel) return true; // No channel for this JID

// ... (existing code for message fetching, trigger check, formatting)

await channel.setTyping?.(chatJid, true);
// ... (existing agent invocation, replacing whatsapp.sendMessage with channel.sendMessage)
await channel.setTyping?.(chatJid, false);
```

In the `onOutput` callback inside `processGroupMessages`, replace:
```typescript
await whatsapp.sendMessage(chatJid, `${ASSISTANT_NAME}: ${text}`);
```
with:
```typescript
const formatted = formatOutbound(channel, text);
if (formatted) await channel.sendMessage(chatJid, formatted);
```

4. **Update `main()` function** to create channels conditionally and use them for deps:

```typescript
async function main(): Promise<void> {
  ensureContainerSystemRunning();
  initDatabase();
  logger.info('Database initialized');
  loadState();

  // Graceful shutdown handlers
  const shutdown = async (signal: string) => {
    logger.info({ signal }, 'Shutdown signal received');
    await queue.shutdown(10000);
    for (const ch of channels) await ch.disconnect();
    process.exit(0);
  };
  process.on('SIGTERM', () => shutdown('SIGTERM'));
  process.on('SIGINT', () => shutdown('SIGINT'));

  // Channel callbacks (shared by all channels)
  const channelOpts = {
    onMessage: (chatJid: string, msg: NewMessage) => storeMessage(msg),
    onChatMetadata: (chatJid: string, timestamp: string, name?: string) =>
      storeChatMetadata(chatJid, timestamp, name),
    registeredGroups: () => registeredGroups,
  };

  // Create and connect channels
  if (!IMESSAGE_ONLY) {
    whatsapp = new WhatsAppChannel(channelOpts);
    channels.push(whatsapp);
    await whatsapp.connect();
  }

  if (IMESSAGE_CLI_PATH) {
    const imessage = new IMessageChannel(IMESSAGE_CLI_PATH, IMESSAGE_DB_PATH, channelOpts);
    channels.push(imessage);
    await imessage.connect();
  }

  // Start subsystems
  startSchedulerLoop({
    registeredGroups: () => registeredGroups,
    getSessions: () => sessions,
    queue,
    onProcess: (groupJid, proc, containerName, groupFolder) =>
      queue.registerProcess(groupJid, proc, containerName, groupFolder),
    sendMessage: async (jid, rawText) => {
      const channel = findChannel(channels, jid);
      if (!channel) return;
      const text = formatOutbound(channel, rawText);
      if (text) await channel.sendMessage(jid, text);
    },
  });
  startIpcWatcher({
    sendMessage: (jid, text) => {
      const channel = findChannel(channels, jid);
      if (!channel) throw new Error(`No channel for JID: ${jid}`);
      return channel.sendMessage(jid, text);
    },
    registeredGroups: () => registeredGroups,
    registerGroup,
    syncGroupMetadata: (force) => whatsapp?.syncGroupMetadata(force) ?? Promise.resolve(),
    getAvailableGroups,
    writeGroupsSnapshot: (gf, im, ag, rj) => writeGroupsSnapshot(gf, im, ag, rj),
  });
  queue.setProcessMessagesFn(processGroupMessages);
  recoverPendingMessages();
  startMessageLoop();
}
```

5. **Update `getAvailableGroups`** to include iMessage chats:

```typescript
export function getAvailableGroups(): AvailableGroup[] {
  const chats = getAllChats();
  const registeredJids = new Set(Object.keys(registeredGroups));

  return chats
    .filter((c) => c.jid !== '__group_sync__' && 
      (c.jid.endsWith('@g.us') || c.jid.startsWith('imessage:')))
    .map((c) => ({
      jid: c.jid,
      name: c.name,
      lastActivity: c.last_message_time,
      isRegistered: registeredJids.has(c.jid),
    }));
}
```

### Step 4: Update Environment

Add to `.env`:

```bash
IMESSAGE_CLI_PATH=/usr/local/bin/imsg
IMESSAGE_DB_PATH=~/Library/Messages/chat.db

# Optional: Set to "true" to disable WhatsApp entirely
# IMESSAGE_ONLY=true
```

**Important**: After modifying `.env`, sync to the container environment:

```bash
cp .env data/env/env
```

The container reads environment from `data/env/env`, not `.env` directly.

### Step 5: Register an iMessage Chat

After installing and starting, tell the user:

> 1. Send a message to your NanoClaw from the iMessage chat you want to register
> 2. I'll detect the chat and register it for you

Or manually register using the chat ID (you can find it via `imsg chats list`):

```typescript
// For private chat (main group):
registerGroup("imessage:+1234567890", {
  name: "Personal",
  folder: "main",
  trigger: `@${ASSISTANT_NAME}`,
  added_at: new Date().toISOString(),
  requiresTrigger: false,
});

// For group chat:
registerGroup("imessage:+1234567890;+0987654321", {
  name: "My iMessage Group",
  folder: "imessage-group",
  trigger: `@${ASSISTANT_NAME}`,
  added_at: new Date().toISOString(),
  requiresTrigger: true,
});
```

The `RegisteredGroup` type requires a `trigger` string field and has an optional `requiresTrigger` boolean (defaults to `true`). Set `requiresTrigger: false` for chats that should respond to all messages.

### Step 6: Build and Restart

```bash
npm run build
launchctl kickstart -k gui/$(id -u)/com.nanoclaw
```

Or for systemd:

```bash
npm run build
systemctl --user restart nanoclaw
```

### Step 7: Test

Tell the user:

> Send a message to your registered iMessage chat:
> - For main chat: Any message works
> - For non-main: `@Andy hello` or use the trigger word
>
> Check logs: `tail -f logs/nanoclaw.log`

## Replace WhatsApp Entirely

If user wants iMessage-only:

1. Set `IMESSAGE_ONLY=true` in `.env`
2. Run `cp .env data/env/env` to sync to container
3. The WhatsApp channel is not created — only iMessage

## Features

### Chat ID Formats

- **WhatsApp**: `120363336345536173@g.us` (groups) or `1234567890@s.whatsapp.net` (DM)
- **iMessage**: `imessage:+1234567890` (phone) or `imessage:user@icloud.com` (email)

### Trigger Options

The bot responds when:
1. Chat has `requiresTrigger: false` in its registration (e.g., main group)
2. Message matches TRIGGER_PATTERN directly (e.g., starts with @Andy)

### Permissions

First time setup may require:
1. **Automation permission**: For imsg to control Messages app
2. **Full Disk Access**: For imsg to read Messages database

You can check/grant these in System Preferences > Security & Privacy > Privacy.

## Troubleshooting

### imsg not found

Check the path:
```bash
which imsg
ls -la /usr/local/bin/imsg
```

If installed elsewhere, update `IMESSAGE_CLI_PATH` in `.env`.

### Permission errors

1. **Automation**: System Preferences > Security & Privacy > Privacy > Automation > Enable Terminal/Messages
2. **Full Disk Access**: System Preferences > Security & Privacy > Privacy > Full Disk Access > Add Terminal

### Bot not responding

Check:
1. `IMESSAGE_CLI_PATH` is set in `.env` AND synced to `data/env/env`
2. Chat is registered in SQLite
3. Service is running: `launchctl list | grep nanoclaw`

### Service conflicts

If running `npm run dev` while launchd service is active:
```bash
launchctl unload ~/Library/LaunchAgents/com.nanoclaw.plist
npm run dev
# When done testing:
launchctl load ~/Library/LaunchAgents/com.nanoclaw.plist
```

## Removal

To remove iMessage integration:

1. Delete `src/channels/imessage.ts`
2. Remove `IMessageChannel` import and creation from `src/index.ts`
3. Remove `channels` array and revert to using `whatsapp` directly
4. Revert `getAvailableGroups()` filter
5. Remove iMessage config from `src/config.ts`
6. Remove iMessage registrations from SQLite
7. Rebuild: `npm run build && launchctl kickstart -k gui/$(id -u)/com.nanoclaw`
