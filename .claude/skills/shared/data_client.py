"""
统一数据路由客户端 — 根据 ticker 自动路由到正确数据源

封装 FMP + AKShare + Crypto + 商品，提供统一接口。

用法:
    from data_client import DataClient
    client = DataClient()

    # 自动路由
    print(client.get_quote("AAPL"))       # 美股 → FMP/yfinance
    print(client.get_quote("BTC"))        # 加密 → Binance
    print(client.get_quote("CL"))         # 原油 → AKShare/yfinance
    print(client.get_quote("600519.SH"))  # A 股 → AKShare
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class DataClient:
    """根据 ticker 自动路由到正确数据源"""

    def __init__(self, fmp_api_key: Optional[str] = None):
        self._fmp_api_key = fmp_api_key
        self._akshare = None
        self._crypto = None
        self._options = None

    def _get_akshare(self):
        if self._akshare is None:
            try:
                from akshare_client import AKShareClient
                self._akshare = AKShareClient()
            except Exception as e:
                logger.debug("AKShare 客户端初始化失败: %s", e)
        return self._akshare

    def _get_crypto(self):
        if self._crypto is None:
            try:
                from crypto_client import CryptoClient
                self._crypto = CryptoClient()
            except Exception as e:
                logger.debug("Crypto 客户端初始化失败: %s", e)
        return self._crypto

    def _get_options(self):
        if self._options is None:
            try:
                from options_client import OptionsClient
                self._options = OptionsClient()
            except Exception as e:
                logger.debug("Options 客户端初始化失败: %s", e)
        return self._options

    def get_quote(self, ticker: str) -> Optional[dict]:
        """
        获取最新报价

        Returns:
            dict: {"symbol": str, "price": float, "source": str, ...}
        """
        from market_router import detect_market, normalize_ticker
        ticker = normalize_ticker(ticker)
        market = detect_market(ticker)

        if market == "CRYPTO":
            crypto = self._get_crypto()
            if crypto:
                return crypto.get_price(ticker)

        if market in ("A_SHARE", "HK", "COMMODITY"):
            akshare = self._get_akshare()
            if akshare:
                try:
                    df = akshare.get_stock_price(ticker, count=1)
                    if not df.empty:
                        row = df.iloc[-1]
                        return {
                            "symbol": ticker,
                            "price": float(row["close"]),
                            "open": float(row.get("open", 0)),
                            "high": float(row.get("high", 0)),
                            "low": float(row.get("low", 0)),
                            "volume": float(row.get("volume", 0)),
                            "date": str(row.get("date", "")),
                            "source": "akshare",
                            "market": market,
                        }
                except Exception as e:
                    logger.warning("AKShare 获取 %s 失败: %s", ticker, e)

        # US 股票 — 尝试 yfinance
        if market == "US":
            try:
                import yfinance as yf
                data = yf.download(ticker, period="1d", progress=False)
                if not data.empty:
                    data = data.reset_index()
                    if isinstance(data.columns, pd.MultiIndex):
                        data.columns = [c[0].lower() for c in data.columns]
                    else:
                        data.columns = [c.lower() for c in data.columns]
                    row = data.iloc[-1]
                    return {
                        "symbol": ticker,
                        "price": float(row["close"]),
                        "open": float(row.get("open", 0)),
                        "high": float(row.get("high", 0)),
                        "low": float(row.get("low", 0)),
                        "volume": float(row.get("volume", 0)),
                        "source": "yfinance",
                        "market": "US",
                    }
            except Exception as e:
                logger.warning("yfinance 获取 %s 失败: %s", ticker, e)

        return None

    def get_historical(self, ticker: str, days: int = 250) -> pd.DataFrame:
        """
        获取历史行情

        Returns:
            DataFrame: date, open, high, low, close, volume
        """
        from market_router import detect_market, normalize_ticker
        ticker = normalize_ticker(ticker)
        market = detect_market(ticker)

        if market == "CRYPTO":
            crypto = self._get_crypto()
            if crypto:
                return crypto.get_ohlcv(ticker, "1d", days)

        if market in ("A_SHARE", "HK", "COMMODITY"):
            akshare = self._get_akshare()
            if akshare:
                try:
                    return akshare.get_stock_price(ticker, count=days)
                except Exception as e:
                    logger.warning("AKShare 历史数据 %s 失败: %s", ticker, e)

        # US — yfinance
        try:
            import yfinance as yf
            data = yf.download(ticker, period=f"{days}d", progress=False)
            if not data.empty:
                data = data.reset_index()
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [c[0].lower() for c in data.columns]
                else:
                    data.columns = [c.lower() for c in data.columns]
                return data[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)
        except Exception as e:
            logger.warning("yfinance 历史数据 %s 失败: %s", ticker, e)

        return pd.DataFrame()

    def get_option_chain(self, ticker: str, expiry: Optional[str] = None) -> dict:
        """
        获取期权链

        Returns:
            dict: {"symbol", "expiry", "calls": DataFrame, "puts": DataFrame, "source"}
        """
        options = self._get_options()
        if options:
            return options.get_option_chain(ticker, expiry)
        return {"symbol": ticker, "error": "期权客户端不可用", "calls": pd.DataFrame(), "puts": pd.DataFrame()}
