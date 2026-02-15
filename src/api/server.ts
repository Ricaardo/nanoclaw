import fastify, { FastifyRequest, FastifyReply } from 'fastify';
import multipart from '@fastify/multipart';
import cors from '@fastify/cors';
import fastifyStatic from '@fastify/static';
import fs from 'fs';
import path from 'path';
import { randomUUID } from 'crypto';
import { spawn, ChildProcess } from 'child_process';
import {
  API_HOST,
  API_PORT,
  API_KEY,
  API_UPLOAD_DIR,
  API_DOWNLOAD_DIR,
  API_MAX_FILE_SIZE,
  API_ALLOWED_EXTENSIONS,
  SUPPORTED_MODELS,
  SUPPORTED_TOOLS,
  DEFAULT_MODEL,
  MAIN_GROUP_FOLDER,
  DATA_DIR,
  API_RUNNER_MODE,
  CLAUDE_CLI_PATH,
  API_WORK_DIR,
} from '../config.js';
import { logger } from '../logger.js';
import {
  runContainerAgent,
} from '../container-runner.js';
import { getAllRegisteredGroups } from '../db.js';

interface ChatRequest {
  message: string;
  group?: string;
  model?: string;
  tools?: string[];
}

interface SseConnection {
  write: (data: string) => void;
}

const sseConnections = new Map<string, SseConnection>();

export async function startApiServer(): Promise<void> {
  const uploadDir = API_UPLOAD_DIR;
  const downloadDir = API_DOWNLOAD_DIR;
  fs.mkdirSync(uploadDir, { recursive: true });
  fs.mkdirSync(downloadDir, { recursive: true });

  const server = fastify({
    logger: false,
  });

  await server.register(cors, {
    origin: true,
  });

  await server.register(multipart, {
    limits: {
      fileSize: API_MAX_FILE_SIZE,
    },
  });

  await server.register(fastifyStatic, {
    root: downloadDir,
    prefix: '/api/download/',
    decorateReply: false,
  });

  server.addHook('onRequest', async (request, reply) => {
    if (API_KEY) {
      const authHeader = request.headers.authorization;
      if (!authHeader || authHeader !== `Bearer ${API_KEY}`) {
        reply.code(401).send({ error: 'Unauthorized' });
        return;
      }
    }
  });

  server.get('/api/health', async () => {
    return { status: 'ok', timestamp: new Date().toISOString() };
  });

  server.get('/api/groups', async () => {
    const groups = getAllRegisteredGroups();
    return {
      groups: Object.entries(groups).map(([jid, g]) => ({
        jid,
        name: g.name,
        folder: g.folder,
        trigger: g.trigger,
      })),
    };
  });

  server.get('/api/models', async () => {
    return {
      models: Object.entries(SUPPORTED_MODELS).map(([id, name]) => ({
        id,
        name,
      })),
      default: DEFAULT_MODEL,
    };
  });

  server.get('/api/tools', async () => {
    return {
      tools: Object.entries(SUPPORTED_TOOLS).map(([id, description]) => ({
        id,
        description,
      })),
    };
  });

  // Get available skills
  server.get('/api/skills', async () => {
    const skillsDir = path.join(process.cwd(), '.claude', 'skills');
    const skills: { name: string; description: string }[] = [];
    
    if (fs.existsSync(skillsDir)) {
      const entries = fs.readdirSync(skillsDir, { withFileTypes: true });
      for (const entry of entries) {
        if (entry.isDirectory()) {
          const skillMdPath = path.join(skillsDir, entry.name, 'SKILL.md');
          if (fs.existsSync(skillMdPath)) {
            const content = fs.readFileSync(skillMdPath, 'utf-8');
            const nameMatch = content.match(/^name:\s*(.+)$/m);
            const descMatch = content.match(/^description:\s*(.+)$/m);
            skills.push({
              name: nameMatch?.[1] || entry.name,
              description: descMatch?.[1] || '',
            });
          }
        }
      }
    }
    
    return { skills };
  });

  // Run a specific skill
  server.post('/api/skills/run', async (request: FastifyRequest, reply: FastifyReply) => {
    let skill = '';
    let message = '';
    let model = DEFAULT_MODEL;
    let tools: string[] | undefined;
    const uploadedFiles: { filename: string; path: string }[] = [];
    const requestId = randomUUID();
    const requestDir = path.join(uploadDir, `req-${requestId}`);
    fs.mkdirSync(requestDir, { recursive: true });

    let connectionId = '';
    try {
      const parts = request.parts();
      for await (const part of parts) {
        if (part.type === 'file') {
          const ext = path.extname(part.filename).toLowerCase();
          if (!API_ALLOWED_EXTENSIONS.includes(ext)) {
            fs.rmSync(requestDir, { recursive: true });
            return reply.code(400).send({ error: `File type not allowed: ${ext}` });
          }

          const fileId = randomUUID();
          const savedFilename = `${fileId}${ext}`;
          const filePath = path.join(requestDir, savedFilename);

          await part.file.pipe(fs.createWriteStream(filePath));
          await part.file;

          uploadedFiles.push({ filename: part.filename, path: filePath });
        } else {
          const val = part.value;
          const value = Buffer.isBuffer(val) ? val.toString('utf-8') : String(val);

          if (part.fieldname === 'skill') skill = value.trim();
          else if (part.fieldname === 'message') message = value;
          else if (part.fieldname === 'model') {
            if (value && SUPPORTED_MODELS[value]) model = value;
          } else if (part.fieldname === 'tools') {
            if (value) {
              tools = value.split(',').map((t: string) => t.trim()).filter((t: string) => SUPPORTED_TOOLS[t]);
            }
          }
        }
      }

      if (!skill) {
        fs.rmSync(requestDir, { recursive: true });
        return reply.code(400).send({ error: 'Skill name is required' });
      }

      // Validate skill exists
      const skillsDir = path.join(process.cwd(), '.claude', 'skills');
      const skillPath = path.join(skillsDir, skill, 'SKILL.md');
      if (!fs.existsSync(skillPath)) {
        fs.rmSync(requestDir, { recursive: true });
        return reply.code(404).send({ error: `Skill not found: ${skill}` });
      }

      // Build message
      let fullMessage = message;
      if (uploadedFiles.length > 0) {
        const fileList = uploadedFiles.map((f) => `- ${f.filename}`).join('\n');
        fullMessage = `${message}\n\n已上传文件:\n${fileList}\n\n文件路径: ${requestDir}`;
      }

      // Add skill prefix
      fullMessage = `/${skill} ${fullMessage}`;

      const workDir = path.join(path.resolve('./groups'), MAIN_GROUP_FOLDER);

      reply.raw.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      });

      connectionId = randomUUID();
      sseConnections.set(connectionId, {
        write: (data) => reply.raw.write(`data: ${JSON.stringify(data)}\n\n`),
      });

      const sendSse = (data: Record<string, unknown>) => {
        const conn = sseConnections.get(connectionId);
        if (conn) conn.write(JSON.stringify(data));
      };

      sendSse({ type: 'start', requestId, skill });

      // Run with local Claude
      const result = await runLocalClaude(fullMessage, { model, tools, workDir });

      if (result.result) {
        sendSse({ type: 'content', text: result.result });
      }

      if (result.status === 'error') {
        sendSse({ type: 'error', error: result.error });
      }

      sendSse({ type: 'done' });
      sseConnections.delete(connectionId);
      reply.raw.end();

      fs.rmSync(requestDir, { recursive: true });

    } catch (err) {
      logger.error({ err }, 'Skill run error');

      const conn = sseConnections.get(connectionId);
      if (conn) {
        conn.write(JSON.stringify({ type: 'error', error: String(err) }));
        sseConnections.delete(connectionId);
      }

      if (fs.existsSync(requestDir)) fs.rmSync(requestDir, { recursive: true });
      if (!reply.raw.writableEnded) reply.raw.end();
    }

    return reply;
  });

  server.post('/api/chat', async (request: FastifyRequest, reply: FastifyReply) => {
    let message = '';
    let group = MAIN_GROUP_FOLDER;
    let model = DEFAULT_MODEL;
    let tools: string[] | undefined;
    let skill: string | undefined;
    const uploadedFiles: { filename: string; path: string }[] = [];
    const requestId = randomUUID();
    const requestDir = path.join(uploadDir, `req-${requestId}`);
    fs.mkdirSync(requestDir, { recursive: true });

    let connectionId = '';
    try {
      // Get fields using part() method
      const fields: Record<string, string> = {};
      
      // Process fields
      async function processField(field: any) {
        const buffer = await field.toBuffer();
        fields[field.fieldname] = buffer.toString('utf-8');
      }
      
      // Get all parts
      const parts = request.parts();
      for await (const part of parts) {
        if (part.type === 'file') {
          // Handle file
          const ext = path.extname(part.filename).toLowerCase();
          if (!API_ALLOWED_EXTENSIONS.includes(ext)) {
            fs.rmSync(requestDir, { recursive: true });
            return reply.code(400).send({
              error: `File type not allowed: ${ext}`,
            });
          }

          const fileId = randomUUID();
          const savedFilename = `${fileId}${ext}`;
          const filePath = path.join(requestDir, savedFilename);

          await part.file.pipe(fs.createWriteStream(filePath));
          await part.file;

          uploadedFiles.push({
            filename: part.filename,
            path: filePath,
          });
        } else {
          // Handle field
          const val = part.value;
          const value = Buffer.isBuffer(val) ? val.toString('utf-8') : String(val);
          if (part.fieldname === 'message') {
            message = value;
          } else if (part.fieldname === 'group') {
            group = value || MAIN_GROUP_FOLDER;
          } else if (part.fieldname === 'model') {
            if (value && SUPPORTED_MODELS[value]) {
              model = value;
            }
          } else if (part.fieldname === 'tools') {
            if (value) {
              tools = value.split(',').map((t: string) => t.trim()).filter((t: string) => SUPPORTED_TOOLS[t]);
            }
          } else if (part.fieldname === 'skill') {
            if (value) {
              skill = value.trim();
            }
          }
        }
      }

      // Validate skill if provided
      if (skill) {
        const skillsDir = path.join(process.cwd(), '.claude', 'skills');
        const skillPath = path.join(skillsDir, skill, 'SKILL.md');
        if (!fs.existsSync(skillPath)) {
          fs.rmSync(requestDir, { recursive: true });
          return reply.code(404).send({ error: `Skill not found: ${skill}` });
        }
      }

      if (!message.trim() && uploadedFiles.length === 0) {
        fs.rmSync(requestDir, { recursive: true });
        return reply.code(400).send({ error: 'Message or file required' });
      }

      let groups = getAllRegisteredGroups();
      
      // Auto-create main group in API-only mode if no groups exist
      const apiOnly = process.env.API_ONLY === 'true';
      if (apiOnly && Object.keys(groups).length === 0) {
        const mainJid = 'api:main';
        groups = {
          [mainJid]: {
            name: 'API Main',
            folder: MAIN_GROUP_FOLDER,
            trigger: '@Andy',
            added_at: new Date().toISOString(),
          },
        };
        // Register the group
        const groupDir = path.join(path.resolve('./groups'), MAIN_GROUP_FOLDER);
        fs.mkdirSync(path.join(groupDir, 'logs'), { recursive: true });
      }
      
      const groupEntry = Object.values(groups).find((g) => g.folder === group);
      if (!groupEntry) {
        fs.rmSync(requestDir, { recursive: true });
        return reply.code(404).send({ error: `Group not found: ${group}` });
      }

      let fullMessage = message;
      if (uploadedFiles.length > 0) {
        const fileList = uploadedFiles
          .map((f) => `- ${f.filename}`)
          .join('\n');
        fullMessage = `${message}\n\n已上传文件:\n${fileList}\n\n文件路径: ${requestDir}`;
      }

      // Add skill prefix if specified
      if (skill) {
        fullMessage = `/${skill} ${fullMessage}`;
      }

      const isMain = group === MAIN_GROUP_FOLDER;

      const connectionId = randomUUID();

      reply.raw.writeHead(200, {
        'Content-Type': 'text/event-stream',
        'Cache-Control': 'no-cache',
        'Connection': 'keep-alive',
      });

      sseConnections.set(connectionId, {
        write: (data) => {
          reply.raw.write(`data: ${JSON.stringify(data)}\n\n`);
        },
      });

      const sendSse = (data: Record<string, unknown>) => {
        const conn = sseConnections.get(connectionId);
        if (conn) {
          conn.write(JSON.stringify(data));
        }
      };

      sendSse({ type: 'start', requestId });

      const envOverrides: Record<string, string> = {};
      if (model) {
        envOverrides.ANTHROPIC_MODEL = model;
      }
      if (tools && tools.length > 0) {
        envOverrides.CLAUDE_CODE_ENABLED_TOOLS = tools.join(',');
      }

      const settingsPath = path.join(
        DATA_DIR,
        'sessions',
        group,
        '.claude',
        'settings.json',
      );
      if (fs.existsSync(settingsPath)) {
        try {
          const settings = JSON.parse(fs.readFileSync(settingsPath, 'utf-8'));
          settings.env = {
            ...settings.env,
            ...(model && { ANTHROPIC_MODEL: model }),
            ...(tools && tools.length > 0 && { CLAUDE_CODE_ENABLED_TOOLS: tools.join(',') }),
          };
          fs.writeFileSync(settingsPath, JSON.stringify(settings, null, 2) + '\n');
        } catch (err) {
          logger.warn({ err, group }, 'Failed to update settings for API request');
        }
      }

      // 根据 runner mode 选择使用容器还是本地 CLI
      if (API_RUNNER_MODE === 'local') {
        // 使用本地 Claude CLI
        const workDir = path.join(path.resolve('./groups'), group);
        
        const result = await runLocalClaude(fullMessage, {
          model,
          tools,
          workDir,
        });

        if (result.result) {
          sendSse({ type: 'content', text: result.result });
        }

        if (result.status === 'error') {
          sendSse({ type: 'error', error: result.error });
        }
      } else {
        // 使用容器
        await runContainerAgent(
          groupEntry,
          {
            prompt: fullMessage,
            groupFolder: group,
            chatJid: `api:${requestId}`,
            isMain,
          },
          () => {},
          async (output) => {
            if (output.result) {
              const raw = typeof output.result === 'string' ? output.result : JSON.stringify(output.result);
              const text = raw.replace(/<internal>[\s\S]*?<\/internal>/g, '').trim();
              if (text) {
                sendSse({ type: 'content', text });
              }
            }

            if (output.status === 'error') {
              sendSse({ type: 'error', error: output.error });
            }
          },
        );
      }

      sendSse({ type: 'done' });

      sseConnections.delete(connectionId);
      reply.raw.end();

      fs.rmSync(requestDir, { recursive: true });

    } catch (err) {
      logger.error({ err }, 'API chat error');
      
      const conn = sseConnections.get(connectionId);
      if (conn) {
        conn.write(JSON.stringify({ type: 'error', error: String(err) }));
        sseConnections.delete(connectionId);
      }

      if (fs.existsSync(requestDir)) {
        fs.rmSync(requestDir, { recursive: true });
      }

      if (!reply.raw.writableEnded) {
        reply.raw.end();
      }
    }

    return reply;
  });

  server.get<{ Params: { fileId: string } }>('/api/download/:fileId', async (request, reply) => {
    const { fileId } = request.params as { fileId: string };
    const filePath = path.join(downloadDir, fileId);

    if (!fs.existsSync(filePath)) {
      return reply.code(404).send({ error: 'File not found' });
    }

    const ext = path.extname(fileId);
    const mimeTypes: Record<string, string> = {
      '.pdf': 'application/pdf',
      '.txt': 'text/plain',
      '.md': 'text/markdown',
      '.json': 'application/json',
      '.zip': 'application/zip',
      '.csv': 'text/csv',
      '.png': 'image/png',
      '.jpg': 'image/jpeg',
      '.jpeg': 'image/jpeg',
      '.gif': 'image/gif',
      '.xlsx': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
      '.docx': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
    };

    const mimeType = mimeTypes[ext] || 'application/octet-stream';

    return reply
      .header('Content-Type', mimeType)
      .header('Content-Disposition', `attachment; filename="${fileId}"`)
      .send(fs.createReadStream(filePath));
  });

  server.delete<{ Params: { fileId: string } }>('/api/download/:fileId', async (request, reply) => {
    const { fileId } = request.params as { fileId: string };
    const filePath = path.join(downloadDir, fileId);

    if (!fs.existsSync(filePath)) {
      return reply.code(404).send({ error: 'File not found' });
    }

    fs.unlinkSync(filePath);
    return { success: true };
  });

  try {
    await server.listen({ host: API_HOST, port: API_PORT });
    logger.info({ host: API_HOST, port: API_PORT, runnerMode: API_RUNNER_MODE }, 'API server started');
  } catch (err) {
    logger.error({ err }, 'Failed to start API server');
    throw err;
  }
}

interface LocalClaudeResult {
  status: 'success' | 'error';
  result: string | null;
  error?: string;
}

export async function runLocalClaude(
  prompt: string,
  options: {
    model?: string;
    tools?: string[];
    workDir?: string;
    sessionId?: string;
  } = {},
): Promise<LocalClaudeResult> {
  const { model, tools, workDir = API_WORK_DIR, sessionId } = options;

  return new Promise((resolve) => {
    const args: string[] = [
      '-p',  // Print mode (non-interactive)
      '--output-format', 'stream-json',
      '--verbose',
    ];

    // 添加模型
    if (model) {
      args.push('--model', model);
    }

    // 添加工具限制
    if (tools && tools.length > 0) {
      args.push('--allowed-tools', tools.join(','));
    }

    // 添加工作目录
    if (workDir) {
      args.push('--add-dir', workDir);
    }

    // 添加 session ID 用于恢复会话
    if (sessionId) {
      args.push('--resume', sessionId);
    }

    args.push(prompt);

    logger.debug({ args: args.join(' '), workDir }, 'Running local Claude CLI');

    const proc = spawn(CLAUDE_CLI_PATH, args, {
      cwd: workDir,
      stdio: ['pipe', 'pipe', 'pipe'],
      env: {
        ...process.env,
        CLAUDE_CODE_DISABLE_AUTO_MEMORY: '0',
      },
    });

    let stdout = '';
    let stderr = '';
    let hasResponse = false;

    proc.stdout.on('data', (data) => {
      const chunk = data.toString();
      stdout += chunk;

      // 解析流式输出
      const lines = chunk.split('\n');
      for (const line of lines) {
        if (line.startsWith('{')) {
          try {
            const parsed = JSON.parse(line);
            
            // 处理 content 类型
            if (parsed.type === 'assistant' && parsed.message?.content) {
              for (const block of parsed.message.content) {
                if (block.type === 'text') {
                  hasResponse = true;
                }
              }
            }
            
            // 处理 result 类型
            if (parsed.type === 'result') {
              if (parsed.is_error) {
                resolve({
                  status: 'error',
                  result: null,
                  error: parsed.result || parsed.error || 'Unknown error',
                });
              } else {
                resolve({
                  status: 'success',
                  result: parsed.result || '',
                });
              }
            }
          } catch (e) {
            // 忽略解析错误
          }
        }
      }
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      if (!hasResponse && !stdout.includes('"type":"result"')) {
        resolve({
          status: 'error',
          result: null,
          error: stderr || `Process exited with code ${code}`,
        });
      }
    });

    proc.on('error', (err) => {
      resolve({
        status: 'error',
        result: null,
        error: err.message,
      });
    });
  });
}
