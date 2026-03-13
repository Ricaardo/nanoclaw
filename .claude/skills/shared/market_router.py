"""
市场路由模块 - 根据 Ticker 格式自动识别市场并路由到对应数据源

用法:
    from market_router import detect_market, get_data_source_config

    market = detect_market("600519.SH")  # -> "A_SHARE"
    config = get_data_source_config("600519.SH")  # -> {"market": "A_SHARE", "source": "akshare", ...}
"""

import re
from typing import Literal

MarketType = Literal["US", "A_SHARE", "HK", "CRYPTO", "COMMODITY", "UNKNOWN"]

# 已知加密货币代码
CRYPTO_SYMBOLS = {
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "DOT", "AVAX", "MATIC",
    "LINK", "UNI", "ATOM", "LTC", "ETC", "FIL", "APT", "ARB", "OP", "NEAR",
    "SHIB", "PEPE", "TRX", "TON", "SUI",
    # DeFi 代币
    "AAVE", "CRV", "MKR", "SUSHI", "COMP", "SNX",
}

# 贵金属/商品代码
COMMODITY_SYMBOLS = {
    "XAU", "XAG", "GLD", "SLV", "GDX", "IAU",
    "CL", "NG", "HG", "SI", "GC", "PL", "PA",
    # 能源商品
    "WTI", "BRENT", "BZ",
}

# A 股指数代码
A_SHARE_INDEX = {
    "000001.SH",  # 上证指数
    "399001.SZ",  # 深证成指
    "399006.SZ",  # 创业板指
    "000300.SH",  # 沪深300
    "000905.SH",  # 中证500
    "000852.SH",  # 中证1000
}


def detect_market(ticker: str) -> MarketType:
    """
    根据 ticker 格式自动识别市场

    规则:
    - 6位数字.SH/.SZ -> A 股
    - 4-5位数字.HK -> 港股
    - BTC/ETH 等已知代码 -> 加密货币
    - XAU/XAG/GLD 等 -> 贵金属/商品
    - 1-5位大写字母 -> 美股
    """
    ticker = ticker.strip().upper()

    # A 股: 6位数字.SH 或 .SZ
    if re.match(r"^\d{6}\.(SH|SZ)$", ticker):
        return "A_SHARE"

    # 港股: 4-5位数字.HK
    if re.match(r"^\d{4,5}\.HK$", ticker):
        return "HK"

    # 加密货币: 已知符号或 XXX-USD/USDT 格式
    base = ticker.split("-")[0].split("/")[0]
    if base in CRYPTO_SYMBOLS:
        return "CRYPTO"
    if re.match(r"^[A-Z]{2,10}[-/](USD|USDT|BTC|ETH)$", ticker):
        return "CRYPTO"

    # 贵金属/商品
    if base in COMMODITY_SYMBOLS:
        return "COMMODITY"

    # 美股: 1-5 位大写字母（可含点号如 BRK.B）
    if re.match(r"^[A-Z]{1,5}(\.[A-Z])?$", ticker):
        return "US"

    return "UNKNOWN"


def get_data_source_config(ticker: str) -> dict:
    """
    返回 ticker 对应的数据源配置

    Returns:
        dict: {
            "market": MarketType,
            "ticker": str (标准化后的 ticker),
            "source": str (推荐数据源),
            "fallback": str | None (备选数据源),
            "notes": str (使用说明)
        }
    """
    market = detect_market(ticker)
    ticker = ticker.strip().upper()

    configs = {
        "A_SHARE": {
            "market": "A_SHARE",
            "ticker": ticker,
            "source": "akshare",
            "fallback": None,
            "notes": "使用 AKShare 获取 A 股数据，支持行情/财务/资金流向",
        },
        "HK": {
            "market": "HK",
            "ticker": ticker,
            "source": "akshare",
            "fallback": "yfinance",
            "notes": "港股优先使用 AKShare，yfinance 作为备选",
        },
        "CRYPTO": {
            "market": "CRYPTO",
            "ticker": ticker,
            "source": "binance",
            "fallback": "okx",
            "notes": "加密货币优先使用 Binance API，OKX 作为备选",
        },
        "COMMODITY": {
            "market": "COMMODITY",
            "ticker": ticker,
            "source": "akshare",
            "fallback": "yfinance",
            "notes": "贵金属/商品使用 AKShare 获取现货/期货价格",
        },
        "US": {
            "market": "US",
            "ticker": ticker,
            "source": "fmp",
            "fallback": "yfinance",
            "notes": "美股优先使用 FMP API，yfinance 作为备选",
        },
        "UNKNOWN": {
            "market": "UNKNOWN",
            "ticker": ticker,
            "source": "websearch",
            "fallback": None,
            "notes": "无法识别市场，建议使用 WebSearch 获取数据",
        },
    }

    return configs[market]


def normalize_ticker(ticker: str) -> str:
    """标准化 ticker 格式"""
    ticker = ticker.strip().upper()
    # A 股简写补全: "600519" -> "600519.SH"
    if re.match(r"^\d{6}$", ticker):
        code = int(ticker[:3])
        if code >= 600:
            return f"{ticker}.SH"
        else:
            return f"{ticker}.SZ"
    # 港股简写补全: "00700" -> "00700.HK"
    if re.match(r"^0\d{4}$", ticker):
        return f"{ticker}.HK"
    return ticker


def batch_detect(tickers: list[str]) -> dict[str, MarketType]:
    """批量识别 ticker 市场"""
    return {t: detect_market(normalize_ticker(t)) for t in tickers}


def to_binance_symbol(ticker: str) -> str:
    """将 ticker 转换为 Binance 格式 (BTCUSDT)"""
    s = ticker.strip().upper()
    for sep in ["-", "/"]:
        s = s.replace(sep, "")
    for suffix in ["USD", "BUSD"]:
        if s.endswith(suffix) and not s.endswith("USDT"):
            s = s[: -len(suffix)] + "USDT"
    # 只有当 ticker 本身包含报价币种后缀时才不追加
    # 排除 ticker 本身就是基础币种的情况（如 BTC, ETH）
    has_quote = False
    for q in ["USDT", "BUSD"]:
        if s.endswith(q) and len(s) > len(q):
            has_quote = True
            break
    if not has_quote:
        s = s + "USDT"
    return s


def to_okx_symbol(ticker: str, inst_type: str = "SPOT") -> str:
    """将 ticker 转换为 OKX 格式 (BTC-USDT / BTC-USDT-SWAP)"""
    s = ticker.strip().upper()
    if "-" in s:
        return s
    for suffix in ["USDT", "USD", "BUSD"]:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    if inst_type == "SWAP":
        return f"{s}-USDT-SWAP"
    return f"{s}-USDT"
