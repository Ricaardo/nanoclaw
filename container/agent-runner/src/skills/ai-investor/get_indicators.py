"""
AI Investor - Technical Indicators Module
计算技术分析指标: RSI, MACD, MA, Bollinger Bands 等
"""

import sys
import json
from datetime import datetime
from typing import Optional, List, Dict, Any

# Try to import yfinance
try:
    import yfinance as yf
    import pandas as pd
    import numpy as np
    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False


# 标的映射表 (复用 get_market_data 的映射)
TRADING_PAIRS = {
    "gold": "GC=F", "gold_usd": "GC=F", "xau": "GC=F",
    "silver": "SI=F", "silver_usd": "SI=F", "xag": "SI=F",
    "crude_oil": "CL=F", "oil": "CL=F", "wti": "CL=F",
    "brent_oil": "BZ=F", "brent": "BZ=F",
    "sp500": "^GSPC", "spx": "^GSPC",
    "nasdaq": "^NDX", "ndx": "^NDX",
    "dow": "^DJI", "djia": "^DJI",
    "nvda": "NVDA", "aapl": "AAPL", "msft": "MSFT",
    "googl": "GOOGL", "amzn": "AMZN", "meta": "META", "tsla": "TSLA",
    "btc": "BTC-USD", "btc_usd": "BTC-USD", "bitcoin": "BTC-USD",
    "eth": "ETH-USD", "eth_usd": "ETH-USD", "ethereum": "ETH-USD",
}


def get_ticker(symbol: str) -> str:
    """获取 Yahoo Finance ticker 代码"""
    return TRADING_PAIRS.get(symbol.lower().strip(), symbol.upper())


def calculate_rsi(prices: pd.Series, period: int = 14) -> pd.Series:
    """计算 RSI (Relative Strength Index)"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=period).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=period).mean()

    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi


def calculate_macd(prices: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9):
    """计算 MACD (Moving Average Convergence Divergence)"""
    ema_fast = prices.ewm(span=fast, adjust=False).mean()
    ema_slow = prices.ewm(span=slow, adjust=False).mean()

    macd_line = ema_fast - ema_slow
    signal_line = macd_line.ewm(span=signal, adjust=False).mean()
    histogram = macd_line - signal_line

    return {
        "macd": macd_line.values,
        "signal": signal_line.values,
        "histogram": histogram.values,
        "current": {
            "macd": float(macd_line.iloc[-1]),
            "signal": float(signal_line.iloc[-1]),
            "histogram": float(histogram.iloc[-1])
        }
    }


def calculate_ma(prices: pd.Series) -> Dict[str, Any]:
    """计算移动平均线"""
    ma5 = prices.rolling(window=5).mean()
    ma20 = prices.rolling(window=20).mean()
    ma60 = prices.rolling(window=60).mean()

    current_price = float(prices.iloc[-1])
    ma5_current = float(ma5.iloc[-1])
    ma20_current = float(ma20.iloc[-1])
    ma60_current = float(ma60.iloc[-1]) if len(ma60) >= 60 else None

    # 判断趋势
    if ma5_current > ma20_current:
        trend = "uptrend"
    elif ma5_current < ma20_current:
        trend = "downtrend"
    else:
        trend = "sideways"

    return {
        "ma5": [float(x) for x in ma5.values if pd.notna(x)],
        "ma20": [float(x) for x in ma20.values if pd.notna(x)],
        "ma60": [float(x) for x in ma60.values if pd.notna(x)],
        "current": {
            "ma5": ma5_current,
            "ma20": ma20_current,
            "ma60": ma60_current
        },
        "price_vs_ma": {
            "above_ma5": current_price > ma5_current,
            "above_ma20": current_price > ma20_current,
            "above_ma60": current_price > ma60_current if ma60_current else None
        },
        "trend": trend
    }


def calculate_bollinger_bands(prices: pd.Series, period: int = 20, std_dev: float = 2.0):
    """计算布林带 (Bollinger Bands)"""
    ma = prices.rolling(window=period).mean()
    std = prices.rolling(window=period).std()

    upper_band = ma + (std * std_dev)
    lower_band = ma - (std * std_dev)

    current_price = float(prices.iloc[-1])
    current_upper = float(upper_band.iloc[-1])
    current_ma = float(ma.iloc[-1])
    current_lower = float(lower_band.iloc[-1])

    # 计算价格位置百分比
    position = (current_price - current_lower) / (current_upper - current_lower) * 100 if current_upper != current_lower else 50

    return {
        "upper": [float(x) for x in upper_band.values if pd.notna(x)],
        "middle": [float(x) for x in ma.values if pd.notna(x)],
        "lower": [float(x) for x in lower_band.values if pd.notna(x)],
        "current": {
            "upper": current_upper,
            "middle": current_ma,
            "lower": current_lower,
            "position_percent": round(position, 2)
        }
    }


def calculate_adx(high: pd.Series, low: pd.Series, close: pd.Series, period: int = 14):
    """计算 ADX (Average Directional Index)"""
    # 计算 +DM 和 -DM
    high_diff = high.diff()
    low_diff = -low.diff()

    plus_dm = high_diff.where((high_diff > low_diff) & (high_diff > 0), 0)
    minus_dm = low_diff.where((low_diff > high_diff) & (low_diff > 0), 0)

    # 计算 True Range
    tr1 = high - low
    tr2 = abs(high - close.shift())
    tr3 = abs(low - close.shift())
    tr = pd.concat([tr1, tr2, tr3], axis=1).max(axis=1)

    # 计算平均值
    atr = tr.rolling(window=period).mean()
    plus_di = 100 * (plus_dm.rolling(window=period).mean() / atr)
    minus_di = 100 * (minus_dm.rolling(window=period).mean() / atr)

    # 计算 DX 和 ADX
    dx = 100 * abs(plus_di - minus_di) / (plus_di + minus_di)
    adx = dx.rolling(window=period).mean()

    current_adx = float(adx.iloc[-1]) if len(adx) >= period else None

    return {
        "adx": [float(x) for x in adx.values if pd.notna(x)],
        "plus_di": [float(x) for x in plus_di.values if pd.notna(x)],
        "minus_di": [float(x) for x in minus_di.values if pd.notna(x)],
        "current": {
            "adx": current_adx,
            "plus_di": float(plus_di.iloc[-1]),
            "minus_di": float(minus_di.iloc[-1])
        },
        "signal": "strong_trend" if current_adx and current_adx > 25 else "weak_trend"
    }


def get_indicators(symbol: str, indicator_list: Optional[List[str]] = None) -> dict:
    """
    获取技术指标

    Args:
        symbol: 标的代码
        indicator_list: 要计算的指标列表 ['rsi', 'macd', 'ma', 'bb', 'adx']

    Returns:
        dict: 技术指标数据
    """
    if not PANDAS_AVAILABLE:
        return {
            "error": "pandas/numpy not installed",
            "symbol": symbol,
            "fallback": "Please install: pip install pandas numpy yfinance"
        }

    ticker_symbol = get_ticker(symbol)

    try:
        ticker = yf.Ticker(ticker_symbol)
        hist = ticker.history(period="3mo")

        if hist.empty:
            return {"error": f"No data found for {symbol}"}

        close = hist['Close']
        high = hist['High']
        low = hist['Low']

        result = {
            "symbol": symbol,
            "timestamp": datetime.now().isoformat()
        }

        # 默认计算所有指标
        if indicator_list is None:
            indicator_list = ['rsi', 'macd', 'ma', 'bb', 'adx']

        # RSI
        if 'rsi' in indicator_list:
            rsi = calculate_rsi(close)
            current_rsi = float(rsi.iloc[-1])

            # RSI 信号
            rsi_signal = "oversold" if current_rsi < 30 else "overbought" if current_rsi > 70 else "neutral"

            result['rsi'] = {
                "values": [float(x) for x in rsi.values if pd.notna(x)],
                "current": round(current_rsi, 2),
                "signal": rsi_signal
            }

        # MACD
        if 'macd' in indicator_list:
            macd_data = calculate_macd(close)

            # MACD 信号
            macd_current = macd_data['current']
            if macd_current['macd'] > macd_current['signal']:
                macd_signal = "bullish" if macd_current['histogram'] > 0 else "weakening_bullish"
            else:
                macd_signal = "bearish" if macd_current['histogram'] < 0 else "weakening_bearish"

            result['macd'] = {
                **macd_data,
                "signal": macd_signal
            }

        # Moving Averages
        if 'ma' in indicator_list:
            ma_data = calculate_ma(close)
            result['ma'] = ma_data

        # Bollinger Bands
        if 'bb' in indicator_list:
            bb_data = calculate_bollinger_bands(close)
            result['bb'] = bb_data

        # ADX
        if 'adx' in indicator_list and len(high) >= 20:
            adx_data = calculate_adx(high, low, close)
            result['adx'] = adx_data

        return result

    except Exception as e:
        return {"error": str(e), "symbol": symbol}


def main():
    """CLI 入口"""
    args = sys.argv[1:]

    if len(args) < 1:
        print(json.dumps({"error": "Usage: python get_indicators.py <symbol> [indicators]"}))
        sys.exit(1)

    symbol = args[0]
    indicators = args[1].split(',') if len(args) > 1 else None

    result = get_indicators(symbol, indicators)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
