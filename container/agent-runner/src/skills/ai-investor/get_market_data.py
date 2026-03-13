"""
AI Investor - Market Data Module
获取股票、加密货币、贵金属、原油的实时行情和历史数据
"""

import sys
import json
from datetime import datetime

# Try to import yfinance, provide fallback
try:
    import yfinance as yf
    YFINANCE_AVAILABLE = True
except ImportError:
    YFINANCE_AVAILABLE = False


# 标的映射表
TRADING_PAIRS = {
    # 贵金属
    "gold": "GC=F",
    "gold_usd": "GC=F",
    "xau": "GC=F",
    "silver": "SI=F",
    "silver_usd": "SI=F",
    "xag": "SI=F",

    # 原油
    "crude_oil": "CL=F",
    "oil": "CL=F",
    "wti": "CL=F",
    "brent_oil": "BZ=F",
    "brent": "BZ=F",

    # 股指
    "sp500": "^GSPC",
    "spx": "^GSPC",
    "nasdaq": "^NDX",
    "ndx": "^NDX",
    "dow": "^DJI",
    "djia": "^DJI",

    # 科技股 (MAG7)
    "nvda": "NVDA",
    "aapl": "AAPL",
    "msft": "MSFT",
    "googl": "GOOGL",
    "amzn": "AMZN",
    "meta": "META",
    "tsla": "TSLA",

    # 加密货币
    "btc": "BTC-USD",
    "btc_usd": "BTC-USD",
    "bitcoin": "BTC-USD",
    "eth": "ETH-USD",
    "eth_usd": "ETH-USD",
    "ethereum": "ETH-USD",
}


def get_ticker(symbol: str) -> str:
    """获取 Yahoo Finance ticker 代码"""
    symbol_lower = symbol.lower().strip()
    return TRADING_PAIRS.get(symbol_lower, symbol.upper())


def get_market_data(symbol: str, period: str = "1mo") -> dict:
    """
    获取市场数据

    Args:
        symbol: 标的代码
        period: 时间周期 (1d, 1wk, 1mo, 3mo, 1y)

    Returns:
        dict: 市场数据
    """
    if not YFINANCE_AVAILABLE:
        return {
            "error": "yfinance not installed",
            "symbol": symbol,
            "fallback": "Please install yfinance: pip install yfinance"
        }

    ticker_symbol = get_ticker(symbol)

    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        hist = ticker.history(period=period)

        if hist.empty:
            return {
                "error": f"No data found for {symbol}",
                "symbol": symbol
            }

        # 最新价格
        latest = hist.iloc[-1]
        previous = hist.iloc[-2] if len(hist) > 1 else latest

        # 计算涨跌幅
        change = latest['Close'] - previous['Close']
        change_percent = (change / previous['Close']) * 100 if previous['Close'] else 0

        # 提取关键信息
        data = {
            "symbol": symbol,
            "ticker": ticker_symbol,
            "name": info.get('shortName', info.get('longName', symbol)),
            "current_price": round(latest['Close'], 2),
            "previous_close": round(previous['Close'], 2),
            "change": round(change, 2),
            "change_percent": round(change_percent, 2),
            "open": round(latest['Open'], 2),
            "high": round(latest['High'], 2),
            "low": round(latest['Low'], 2),
            "volume": int(latest['Volume']),
            "timestamp": datetime.now().isoformat(),
            "period": period,
        }

        # 添加股票特有信息
        if 'marketCap' in info:
            data['market_cap'] = info['marketCap']
        if 'peRatio' in info:
            data['pe_ratio'] = info['peRatio']
        if 'fiftyTwoWeekHigh' in info:
            data['52w_high'] = info['fiftyTwoWeekHigh']
        if 'fiftyTwoWeekLow' in info:
            data['52w_low'] = info['fiftyTwoWeekLow']

        # 添加历史数据 (最近30个数据点)
        hist_data = []
        for idx, row in hist.tail(30).iterrows():
            hist_data.append({
                "date": idx.isoformat(),
                "open": round(row['Open'], 2),
                "high": round(row['High'], 2),
                "low": round(row['Low'], 2),
                "close": round(row['Close'], 2),
                "volume": int(row['Volume'])
            })
        data['history'] = hist_data

        return data

    except Exception as e:
        return {
            "error": str(e),
            "symbol": symbol
        }


def main():
    """CLI 入口"""
    args = sys.argv[1:]

    if len(args) < 1:
        print(json.dumps({"error": "Usage: python get_market_data.py <symbol> [period]"}))
        sys.exit(1)

    symbol = args[0]
    period = args[1] if len(args) > 1 else "1mo"

    result = get_market_data(symbol, period)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
