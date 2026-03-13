"""
期权数据客户端 — US 期权 (yfinance) + 加密期权 (OKX)

用法:
    from options_client import OptionsClient
    client = OptionsClient()

    # US 期权
    expiries = client.get_expiries("AAPL")
    chain = client.get_option_chain("AAPL", expiries[0])

    # 加密期权
    df = client.get_crypto_options("BTC")
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class OptionsClient:
    """期权数据客户端"""

    def __init__(self):
        self._okx = None

    def _get_okx(self):
        if self._okx is None:
            try:
                from okx_client import OKXClient
                self._okx = OKXClient()
            except Exception:
                pass
        return self._okx

    def get_expiries(self, symbol: str) -> list:
        """
        获取期权到期日列表

        Args:
            symbol: 股票代码 (如 AAPL) 或加密货币 (如 BTC)

        Returns:
            list[str]: 到期日列表 (YYYY-MM-DD 格式)
        """
        from market_router import detect_market
        market = detect_market(symbol)

        if market == "CRYPTO":
            return self._get_crypto_expiries(symbol)
        return self._get_us_expiries(symbol)

    def _get_us_expiries(self, symbol: str) -> list:
        """通过 yfinance 获取 US 期权到期日"""
        if not HAS_YFINANCE:
            logger.error("yfinance 未安装，无法获取 US 期权到期日")
            return []
        try:
            ticker = yf.Ticker(symbol)
            return list(ticker.options)
        except Exception as e:
            logger.error("获取 %s 期权到期日失败: %s", symbol, e)
            return []

    def _get_crypto_expiries(self, symbol: str) -> list:
        """通过 OKX 获取加密期权到期日"""
        okx = self._get_okx()
        if not okx:
            return []
        try:
            instruments = okx.get_option_instruments(symbol)
            # 提取唯一到期日
            expiries = sorted(set(d["expiry"] for d in instruments if d.get("expiry")))
            return expiries
        except Exception as e:
            logger.error("获取 %s 加密期权到期日失败: %s", symbol, e)
            return []

    def get_option_chain(self, symbol: str, expiry: Optional[str] = None) -> dict:
        """
        获取期权链数据

        Args:
            symbol: 股票代码或加密货币
            expiry: 到期日 (YYYY-MM-DD)

        Returns:
            dict: {
                "symbol": str,
                "expiry": str,
                "calls": DataFrame,
                "puts": DataFrame,
                "source": str
            }
        """
        from market_router import detect_market
        market = detect_market(symbol)

        if market == "CRYPTO":
            return self._get_crypto_chain(symbol, expiry)
        return self._get_us_chain(symbol, expiry)

    def _get_us_chain(self, symbol: str, expiry: Optional[str] = None) -> dict:
        """通过 yfinance 获取 US 期权链"""
        if not HAS_YFINANCE:
            return {"symbol": symbol, "error": "yfinance 未安装", "calls": pd.DataFrame(), "puts": pd.DataFrame()}

        try:
            ticker = yf.Ticker(symbol)
            if expiry is None:
                expiries = list(ticker.options)
                if not expiries:
                    return {"symbol": symbol, "error": "无可用期权", "calls": pd.DataFrame(), "puts": pd.DataFrame()}
                expiry = expiries[0]

            chain = ticker.option_chain(expiry)

            calls = chain.calls.copy()
            puts = chain.puts.copy()

            # 标准化列名
            col_map = {
                "contractSymbol": "contract",
                "lastTradeDate": "last_trade_date",
                "lastPrice": "last_price",
                "bid": "bid",
                "ask": "ask",
                "change": "change",
                "percentChange": "pct_change",
                "volume": "volume",
                "openInterest": "open_interest",
                "impliedVolatility": "iv",
                "inTheMoney": "itm",
                "strike": "strike",
            }
            calls = calls.rename(columns={k: v for k, v in col_map.items() if k in calls.columns})
            puts = puts.rename(columns={k: v for k, v in col_map.items() if k in puts.columns})

            return {
                "symbol": symbol,
                "expiry": expiry,
                "calls": calls,
                "puts": puts,
                "source": "yfinance",
            }
        except Exception as e:
            logger.error("获取 %s 期权链失败: %s", symbol, e)
            return {"symbol": symbol, "error": str(e), "calls": pd.DataFrame(), "puts": pd.DataFrame()}

    def _get_crypto_chain(self, symbol: str, expiry: Optional[str] = None) -> dict:
        """通过 OKX 获取加密期权链"""
        okx = self._get_okx()
        if not okx:
            return {"symbol": symbol, "error": "OKX 客户端不可用", "calls": pd.DataFrame(), "puts": pd.DataFrame()}

        try:
            instruments = okx.get_option_instruments(symbol)
            if not instruments:
                return {"symbol": symbol, "error": "无可用期权合约", "calls": pd.DataFrame(), "puts": pd.DataFrame()}

            # 按到期日筛选
            if expiry:
                instruments = [i for i in instruments if expiry in str(i.get("expiry", ""))]

            calls_data = [i for i in instruments if i.get("opt_type") == "C"]
            puts_data = [i for i in instruments if i.get("opt_type") == "P"]

            calls = pd.DataFrame(calls_data) if calls_data else pd.DataFrame()
            puts = pd.DataFrame(puts_data) if puts_data else pd.DataFrame()

            return {
                "symbol": symbol,
                "expiry": expiry,
                "calls": calls,
                "puts": puts,
                "source": "okx",
            }
        except Exception as e:
            logger.error("获取 %s 加密期权链失败: %s", symbol, e)
            return {"symbol": symbol, "error": str(e), "calls": pd.DataFrame(), "puts": pd.DataFrame()}

    def get_crypto_options(self, underlying: str) -> pd.DataFrame:
        """
        获取加密期权行情数据（含 Greeks）

        Args:
            underlying: 标的代码，如 BTC, ETH

        Returns:
            DataFrame with Greeks
        """
        okx = self._get_okx()
        if not okx:
            return pd.DataFrame()

        try:
            return okx.get_option_market_data(underlying)
        except Exception as e:
            logger.error("获取 %s 加密期权行情失败: %s", underlying, e)
            return pd.DataFrame()
