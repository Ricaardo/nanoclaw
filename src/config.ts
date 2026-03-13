import os from 'os';
import path from 'path';

export const ASSISTANT_NAME = process.env.ASSISTANT_NAME || 'Andy';
export const POLL_INTERVAL = 2000;
export const SCHEDULER_POLL_INTERVAL = 60000;

// Absolute paths needed for container mounts
const PROJECT_ROOT = process.cwd();
const HOME_DIR = process.env.HOME || '/Users/user';

// Mount security: allowlist stored OUTSIDE project root, never mounted into containers
export const MOUNT_ALLOWLIST_PATH = path.join(
  HOME_DIR,
  '.config',
  'nanoclaw',
  'mount-allowlist.json',
);
export const STORE_DIR = path.resolve(PROJECT_ROOT, 'store');
export const GROUPS_DIR = path.resolve(PROJECT_ROOT, 'groups');
export const DATA_DIR = path.resolve(PROJECT_ROOT, 'data');
export const MAIN_GROUP_FOLDER = 'main';

export const CONTAINER_IMAGE =
  process.env.CONTAINER_IMAGE || 'nanoclaw-agent:latest';
export const CONTAINER_TIMEOUT = parseInt(
  process.env.CONTAINER_TIMEOUT || '1800000',
  10,
);
export const CONTAINER_MAX_OUTPUT_SIZE = parseInt(
  process.env.CONTAINER_MAX_OUTPUT_SIZE || '10485760',
  10,
); // 10MB default
export const IPC_POLL_INTERVAL = 1000;
export const IDLE_TIMEOUT = parseInt(
  process.env.IDLE_TIMEOUT || '1800000',
  10,
); // 30min default — how long to keep container alive after last result
export const MAX_CONCURRENT_CONTAINERS = Math.max(
  1,
  parseInt(process.env.MAX_CONCURRENT_CONTAINERS || '5', 10) || 5,
);

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

export const TRIGGER_PATTERN = new RegExp(
  `^@${escapeRegex(ASSISTANT_NAME)}\\b`,
  'i',
);

// Timezone for scheduled tasks (cron expressions, etc.)
// Uses system timezone by default
export const TIMEZONE =
  process.env.TZ || Intl.DateTimeFormat().resolvedOptions().timeZone;

// iMessage configuration
export const IMESSAGE_ONLY = process.env.IMESSAGE_ONLY === 'true' || true; // Default to iMessage only
export const IMESSAGE_CLI_PATH =
  process.env.IMESSAGE_CLI_PATH || '/usr/local/bin/imsg';
export const IMESSAGE_DB_PATH =
  process.env.IMESSAGE_DB_PATH ||
  path.join(os.homedir(), 'Library/Messages/chat.db');

// API Server configuration
export const API_HOST = process.env.API_HOST || '0.0.0.0';  // 默认允许局域网访问
export const API_PORT = parseInt(process.env.API_PORT || '3456', 10);
export const API_KEY = process.env.NANOCLAW_API_KEY;
export const API_UPLOAD_DIR = path.join(DATA_DIR, 'uploads');
export const API_DOWNLOAD_DIR = path.join(DATA_DIR, 'downloads');
export const API_MAX_FILE_SIZE = parseInt(process.env.API_MAX_FILE_SIZE || '52428800', 10); // 50MB
export const API_ALLOWED_EXTENSIONS = [
  '.pdf', '.txt', '.md', '.json', '.zip', '.csv', '.png', '.jpg', '.jpeg', '.gif', '.xlsx', '.docx',
  '.js', '.ts', '.jsx', '.tsx', '.py', '.go', '.java', '.c', '.cpp', '.h', '.rs', '.rb', '.php'
];

// API Runner mode: "container" (default) or "local" (use local Claude CLI)
export const API_RUNNER_MODE = process.env.API_RUNNER_MODE || 'local';
// Path to local Claude CLI (auto-detected if not set)
export const CLAUDE_CLI_PATH = process.env.CLAUDE_CLI_PATH || 'claude';
// Working directory for API requests
export const API_WORK_DIR = process.env.API_WORK_DIR || path.join(DATA_DIR, '..', 'groups', 'main');

// Supported models
export const SUPPORTED_MODELS: Record<string, string> = {
  'claude-sonnet-4-20250514': 'Claude Sonnet 4',
  'claude-opus-4-20250514': 'Claude Opus 4',
  'claude-3-5-sonnet-20241022': 'Claude 3.5 Sonnet',
  'claude-3-5-haiku-20241022': 'Claude 3.5 Haiku',
  'claude-3-haiku-20240307': 'Claude 3 Haiku',
};
export const DEFAULT_MODEL = 'claude-sonnet-4-20250514';

// Supported tools
export const SUPPORTED_TOOLS: Record<string, string> = {
  'Bash': '执行 shell 命令',
  'Read': '读取文件',
  'Edit': '编辑文件',
  'Write': '写入文件',
  'Glob': '文件搜索',
  'Grep': '内容搜索',
  'WebFetch': '抓取网页',
  'WebSearch': '网络搜索',
  'TodoWrite': '任务管理',
  'Task': '子任务调用',
};

// Feishu configuration
export const FEISHU_ENABLED = process.env.FEISHU_ENABLED === 'true';
export const FEISHU_APP_ID = process.env.FEISHU_APP_ID;
export const FEISHU_APP_SECRET = process.env.FEISHU_APP_SECRET;
export const FEISHU_ENCRYPT_KEY = process.env.FEISHU_ENCRYPT_KEY;
export const FEISHU_VERIFICATION_TOKEN = process.env.FEISHU_VERIFICATION_TOKEN;
export const FEISHU_ALLOW_FROM = process.env.FEISHU_ALLOW_FROM
  ? process.env.FEISHU_ALLOW_FROM.split(',')
  : [];

// Telegram configuration
export const TELEGRAM_ENABLED = process.env.TELEGRAM_ENABLED === 'true';
export const TELEGRAM_BOT_TOKEN = process.env.TELEGRAM_BOT_TOKEN;
export const TELEGRAM_ALLOWED_USERNAMES = process.env.TELEGRAM_ALLOWED_USERNAMES
  ? process.env.TELEGRAM_ALLOWED_USERNAMES.split(',')
  : [];
export const TELEGRAM_ALLOWED_CHAT_IDS = process.env.TELEGRAM_ALLOWED_CHAT_IDS
  ? process.env.TELEGRAM_ALLOWED_CHAT_IDS.split(',').map(Number)
  : [];
export const TELEGRAM_GROUP_POLICY = process.env.TELEGRAM_GROUP_POLICY || 'mention';
