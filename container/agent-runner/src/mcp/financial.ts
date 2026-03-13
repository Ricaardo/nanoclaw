/**
 * Financial MCP Server for NanoClaw
 * Provides tools for stock market analysis, technical indicators, and investor-style analysis
 */

import { McpServer } from '@modelcontextprotocol/sdk/server/mcp.js';
import { StdioServerTransport } from '@modelcontextprotocol/sdk/server/stdio.js';
import { z } from 'zod';
import { spawn } from 'child_process';
import * as fs from 'fs';
import * as path from 'path';

const FINANCIAL_DATA_DIR = '/workspace/financial-data';
const SCRIPTS_DIR = path.join(FINANCIAL_DATA_DIR, 'scripts');
const DATA_FILE = path.join(FINANCIAL_DATA_DIR, 'portfolio.json');

// Ensure directories exist
fs.mkdirSync(SCRIPTS_DIR, { recursive: true });

// ============================================================================
// Helper Functions
// ============================================================================

/**
 * Run a Python script and return the result
 */
function runPythonScript(scriptName: string, args: string[] = []): Promise<any> {
  return new Promise((resolve, reject) => {
    const scriptPath = path.join(SCRIPTS_DIR, scriptName);

    // Check if script exists, if not use built-in
    if (!fs.existsSync(scriptPath)) {
      // Fallback: try running Python directly with inline code
      const pythonCmd = spawn('python3', ['-c', `print("{}")`], {
        cwd: SCRIPTS_DIR
      });

      let stdout = '';
      let stderr = '';

      pythonCmd.stdout.on('data', (data) => { stdout += data.toString(); });
      pythonCmd.stderr.on('data', (data) => { stderr += data.toString(); });

      pythonCmd.on('close', (code) => {
        if (code === 0) {
          try {
            resolve(JSON.parse(stdout.trim()));
          } catch {
            resolve({ raw: stdout, error: stderr });
          }
        } else {
          reject(new Error(stderr || `Script exited with code ${code}`));
        }
      });
      return;
    }

    const python = spawn('python3', [scriptPath, ...args], {
      cwd: SCRIPTS_DIR,
      shell: false
    });

    let stdout = '';
    let stderr = '';

    python.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    python.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    python.on('close', (code) => {
      if (code === 0) {
        try {
          resolve(JSON.parse(stdout.trim()));
        } catch {
          resolve({ raw: stdout, error: stderr });
        }
      } else {
        reject(new Error(stderr || `Script exited with code ${code}`));
      }
    });

    python.on('error', (err) => {
      reject(err);
    });
  });
}

/**
 * Load portfolio data
 */
function loadPortfolio(): any {
  try {
    if (fs.existsSync(DATA_FILE)) {
      return JSON.parse(fs.readFileSync(DATA_FILE, 'utf-8'));
    }
  } catch (e) {
    // Return default portfolio
  }
  return {
    holdings: [
      { symbol: 'gold_usd', quantity: 10, avg_price: 4800, current_price: 5175 },
      { symbol: 'btc_usd', quantity: 0.5, avg_price: 65000, current_price: 71600 },
      { symbol: 'sp500', quantity: 100, avg_price: 5800, current_price: 6816 },
    ]
  };
}

/**
 * Save portfolio data
 */
function savePortfolio(portfolio: any): void {
  fs.writeFileSync(DATA_FILE, JSON.stringify(portfolio, null, 2));
}

// ============================================================================
// Investor Style Prompts
// ============================================================================

const INVESTOR_PROMPTS = {
  buffett: `You are Warren Buffett. Analyze from a value investing perspective:
- Focus on intrinsic value and long-term fundamentals
- Look for companies with strong competitive advantages (moats)
- Emphasize cash flow, earnings quality, and management quality
- Consider the margin of safety
- Provide conservative, patient investment advice`,

  soros: `You are George Soros. Analyze from a macro/trend trading perspective:
- Focus on macroeconomic trends and market momentum
- Look for reflexive dynamics and feedback loops
- Be prepared to cut losses quickly if thesis is wrong
- Consider currency flows and geopolitical factors
- Provide opportunistic, adaptive trading advice`,

  munger: `You are Charlie Munger. Analyze from an inverted thinking perspective:
- Focus on what could go wrong (inversion)
- Look for cognitive biases and common mistakes
- Emphasize multidisciplinary thinking
- Seek asymmetric risk-reward opportunities
- Provide contrarian, rational advice`,

  dalio: `You are Ray Dalio. Analyze from an all-weather/risk parity perspective:
- Focus on diversification across asset classes
- Consider inflation, growth, and recession scenarios
- Balance risk across different environments
- Use systematic, rules-based approach
- Provide balanced, portfolio-level advice`
};

// ============================================================================
// MCP Server Setup
// ============================================================================

const server = new McpServer({
  name: 'financial',
  version: '1.0.0',
});

// ============================================================================
// Tool: get_market_data
// ============================================================================

server.tool(
  'get_market_data',
  `获取股票、加密货币、贵金属、原油的实时行情和历史数据。

支持以下标的:
- 贵金属: gold (黄金), silver (白银)
- 原油: crude_oil (WTI), brent_oil (布伦特)
- 股指: sp500, nasdaq, dow
- 科技股: nvda, aapl, msft, googl, amzn, meta, tsla (MAG7)
- 加密货币: btc, eth

时间周期: 1d (1天), 1wk (1周), 1mo (1月), 3mo (3月), 1y (1年)`,
  {
    symbol: z.string().describe('标的代码: gold, silver, crude_oil, sp500, nasdaq, nvda, aapl, msft, btc, eth 等'),
    period: z.enum(['1d', '1wk', '1mo', '3mo', '1y']).default('1mo').describe('时间周期'),
  },
  async ({ symbol, period }) => {
    try {
      const data = await runPythonScript('get_market_data.py', [symbol, period]);
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }]
      };
    } catch (error) {
      // Fallback to error message
      return {
        content: [{ type: 'text' as const, text: `Error fetching market data: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Tool: get_technical_indicators
// ============================================================================

server.tool(
  'get_technical_indicators',
  `计算并返回技术分析指标。

支持的指标:
- rsi: Relative Strength Index (14日)
- macd: Moving Average Convergence Divergence
- ma: Moving Averages (5, 20, 60日)
- bb: Bollinger Bands
- adx: Average Directional Index

返回当前指标值和历史数据，以及基于指标的交易建议。`,
  {
    symbol: z.string().describe('标的代码'),
    indicators: z.array(z.enum(['rsi', 'macd', 'ma', 'bb', 'adx'])).optional()
      .describe('要计算的指标，默认全部'),
  },
  async ({ symbol, indicators }) => {
    try {
      const indArray = indicators || ['rsi', 'macd', 'ma', 'bb'];
      const data = await runPythonScript('get_indicators.py', [symbol, indArray.join(',')]);
      return {
        content: [{ type: 'text' as const, text: JSON.stringify(data, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text' as const, text: `Error calculating indicators: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Tool: get_portfolio
// ============================================================================

server.tool(
  'get_portfolio',
  `获取当前投资组合的持仓信息、盈亏情况、仓位分配。

返回:
- 各持仓的当前价格、市值、成本价
- 盈亏金额和盈亏率
- 仓位占比
- 总资产和总盈亏`,
  {},
  async () => {
    try {
      const portfolio = loadPortfolio();
      const holdings = portfolio.holdings || [];

      // Calculate current values
      const results = holdings.map((h: any) => {
        const currentValue = h.quantity * h.current_price;
        const costBasis = h.quantity * h.avg_price;
        const profit = currentValue - costBasis;
        const profitPercent = ((h.current_price - h.avg_price) / h.avg_price) * 100;

        return {
          symbol: h.symbol,
          quantity: h.quantity,
          avg_price: h.avg_price,
          current_price: h.current_price,
          current_value: currentValue,
          cost_basis: costBasis,
          profit: profit,
          profit_percent: profitPercent.toFixed(2) + '%'
        };
      });

      const totalValue = results.reduce((sum: number, h: any) => sum + h.current_value, 0);
      const totalCost = results.reduce((sum: number, h: any) => sum + h.cost_basis, 0);
      const totalProfit = totalValue - totalCost;
      const totalProfitPercent = ((totalValue - totalCost) / totalCost * 100).toFixed(2) + '%';

      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            holdings: results,
            summary: {
              total_value: totalValue,
              total_cost: totalCost,
              total_profit: totalProfit,
              total_profit_percent: totalProfitPercent
            }
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text' as const, text: `Error: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Tool: add_to_portfolio
// ============================================================================

server.tool(
  'add_to_portfolio',
  '添加新的持仓到投资组合',
  {
    symbol: z.string().describe('标的代码'),
    quantity: z.number().describe('数量'),
    price: z.number().describe('买入价格'),
  },
  async ({ symbol, quantity, price }) => {
    try {
      const portfolio = loadPortfolio();
      const holdings = portfolio.holdings || [];

      // Check if position exists
      const((h: any existing = holdings.find) => h.symbol === symbol);
      if (existing) {
        // Calculate new average price
        const totalQuantity = existing.quantity + quantity;
        const totalCost = (existing.quantity * existing.avg_price) + (quantity * price);
        existing.avg_price = totalCost / totalQuantity;
        existing.quantity = totalQuantity;
      } else {
        holdings.push({
          symbol,
          quantity,
          avg_price: price,
          current_price: price // Will be updated when fetching market data
        });
      }

      portfolio.holdings = holdings;
      savePortfolio(portfolio);

      return {
        content: [{ type: 'text' as const, text: `Added ${quantity} ${symbol} at $${price}` }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text' as const, text: `Error: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Tool: get_trading_signals
// ============================================================================

server.tool(
  'get_trading_signals',
  `获取基于技术分析的交易信号。

分析多个标的的技术指标，返回:
- 买入/卖出/持有信号
- 置信度
- 关键价位 (支撑/阻力)
- 风险提示`,
  {
    symbols: z.array(z.string()).optional().describe('要分析的标的列表，默认分析持仓中的标的'),
  },
  async ({ symbols }) => {
    try {
      const portfolio = loadPortfolio();
      const symbolsToAnalyze = symbols || portfolio.holdings?.map((h: any) => h.symbol) || ['sp500', 'btc_usd'];

      const signals = [];
      for (const symbol of symbolsToAnalyze) {
        try {
          const indicators = await runPythonScript('get_indicators.py', [symbol, 'rsi,macd,ma']);

          // Generate signal based on indicators
          let signal = 'hold';
          let confidence = 0;
          const reasons: string[] = [];

          // RSI analysis
          if (indicators.rsi?.current) {
            if (indicators.rsi.current < 30) {
              signal = 'buy';
              confidence += 30;
              reasons.push('RSI oversold');
            } else if (indicators.rsi.current > 70) {
              signal = 'sell';
              confidence += 30;
              reasons.push('RSI overbought');
            }
          }

          // MACD analysis
          if (indicators.macd?.signal === 'bullish') {
            confidence += 20;
            reasons.push('MACD golden cross');
          } else if (indicators.macd?.signal === 'bearish') {
            confidence += 20;
            reasons.push('MACD death cross');
          }

          // MA analysis
          if (indicators.ma?.trend === 'uptrend') {
            confidence += 20;
            reasons.push('Price above moving averages');
          } else if (indicators.ma?.trend === 'downtrend') {
            confidence += 20;
            reasons.push('Price below moving averages');
          }

          signals.push({
            symbol,
            signal,
            confidence: Math.min(confidence, 100),
            reasons
          });
        } catch (e) {
          signals.push({ symbol, signal: 'error', error: String(e) });
        }
      }

      return {
        content: [{ type: 'text' as const, text: JSON.stringify(signals, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text' as const, text: `Error: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Tool: analyze_investor_style
// ============================================================================

server.tool(
  'analyze_investor_style',
  `模拟某位投资大师的风格分析市场。

支持的投资人风格:
- buffett: Warren Buffett (价值投资，安全边际)
- soros: George Soros (宏观趋势，果断止损)
- munger: Charlie Munger (逆向思考，认知偏差)
- dalio: Ray Dalio (全天候，风险平价)

输入标的，工具会:
1. 获取实时市场数据
2. 计算技术指标
3. 返回该投资人风格的分析和建议`,
  {
    symbol: z.string().describe('要分析的标的'),
    investor: z.enum(['buffett', 'soros', 'munger', 'dalio']).describe('投资人风格'),
    include_market_data: z.boolean().default(true).describe('是否包含详细市场数据'),
  },
  async ({ symbol, investor, include_market_data }) => {
    try {
      // Get market data and indicators in parallel
      const [marketData, indicators] = await Promise.all([
        runPythonScript('get_market_data.py', [symbol, '1mo']).catch(() => ({})),
        runPythonScript('get_indicators.py', [symbol, 'rsi,macd,ma,bb']).catch(() => ({}))
      ]);

      const prompt = INVESTOR_PROMPTS[investor];

      // Format the analysis request
      const analysisContext = {
        symbol,
        investor_style: investor,
        market_data: include_market_data ? marketData : undefined,
        technical_indicators: indicators,
        prompt
      };

      // Return the analysis context - the agent should use this with Claude
      // to generate the actual analysis
      return {
        content: [{
          type: 'text' as const,
          text: JSON.stringify({
            status: 'ready_for_analysis',
            ...analysisContext,
            _instruction: `Use this data to generate a ${investor} style analysis for ${symbol}.
${prompt}

Provide investment advice based on the data provided.`
          }, null, 2)
        }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text' as const, text: `Error: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Tool: get_market_overview
// ============================================================================

server.tool(
  'get_market_overview',
  `获取市场概览，包括多个主要市场指数的当前状态。

返回:
- 标普500、纳斯达克、道琼斯
- 黄金、原油
- 比特币、以太坊
- 各市场的涨跌幅
- 市场情绪指标`,
  {},
  async () => {
    try {
      const symbols = ['sp500', 'nasdaq', 'dow', 'gold_usd', 'crude_oil', 'btc_usd', 'eth_usd'];
      const results = [];

      for (const symbol of symbols) {
        try {
          const data = await runPythonScript('get_market_data.py', [symbol, '1d']);
          results.push({
            symbol,
            ...data
          });
        } catch (e) {
          results.push({ symbol, error: String(e) });
        }
      }

      return {
        content: [{ type: 'text' as const, text: JSON.stringify(results, null, 2) }]
      };
    } catch (error) {
      return {
        content: [{ type: 'text' as const, text: `Error: ${error}` }],
        isError: true
      };
    }
  }
);

// ============================================================================
// Start the Server
// ============================================================================

const transport = new StdioServerTransport();
await server.connect(transport);
