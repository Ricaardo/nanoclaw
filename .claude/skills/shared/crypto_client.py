"""
统一加密货币客户端 — Binance → OKX → AKShare fallback 链

用法:
    from crypto_client import CryptoClient
    client = CryptoClient()
    print(client.get_price("BTC"))
    df = client.get_ohlcv("ETH", "1d", 30)
    print(client.get_funding_comparison("BTC"))
"""

import logging
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)


class CryptoClient:
    """统一加密货币客户端，实现多数据源 fallback"""

    def __init__(self, preferred: str = "binance"):
        self._preferred = preferred
        self._binance = None
        self._okx = None
        self._akshare = None

    def _get_binance(self):
        if self._binance is None:
            try:
                from binance_client import BinanceClient
                self._binance = BinanceClient()
            except Exception as e:
                logger.debug("Binance 客户端初始化失败: %s", e)
        return self._binance

    def _get_okx(self):
        if self._okx is None:
            try:
                from okx_client import OKXClient
                self._okx = OKXClient()
            except Exception as e:
                logger.debug("OKX 客户端初始化失败: %s", e)
        return self._okx

    def _get_akshare(self):
        if self._akshare is None:
            try:
                from akshare_client import AKShareClient
                self._akshare = AKShareClient()
            except Exception as e:
                logger.debug("AKShare 客户端初始化失败: %s", e)
        return self._akshare

    def _sources(self):
        """按偏好顺序返回数据源列表"""
        if self._preferred == "okx":
            return [("okx", self._get_okx), ("binance", self._get_binance), ("akshare", self._get_akshare)]
        return [("binance", self._get_binance), ("okx", self._get_okx), ("akshare", self._get_akshare)]

    # ==================== 价格 ====================

    def get_price(self, symbol: str) -> Optional[dict]:
        """获取最新价格"""
        for name, getter in self._sources():
            client = getter()
            if client is None:
                continue
            try:
                if name == "binance":
                    result = client.get_price(symbol)
                    if result:
                        return {**result, "source": "binance"}
                elif name == "okx":
                    result = client.get_ticker(symbol)
                    if result:
                        return {"symbol": result["inst_id"], "price": result["price"], "source": "okx"}
                elif name == "akshare":
                    base = symbol.split("-")[0].split("/")[0].upper()
                    df = client.get_stock_price(base, count=1)
                    if not df.empty:
                        return {"symbol": base, "price": float(df.iloc[-1]["close"]), "source": "akshare"}
            except Exception as e:
                logger.debug("get_price via %s 失败: %s", name, e)
                continue
        return None

    # ==================== OHLCV ====================

    def get_ohlcv(self, symbol: str, interval: str = "1d", count: int = 100) -> pd.DataFrame:
        """获取 K 线数据"""
        for name, getter in self._sources():
            client = getter()
            if client is None:
                continue
            try:
                if name == "binance":
                    df = client.get_klines(symbol, interval, count)
                elif name == "okx":
                    bar_map = {"1d": "1D", "1h": "1H", "4h": "4H", "1w": "1W", "1m": "1m", "5m": "5m", "15m": "15m"}
                    bar = bar_map.get(interval.lower(), "1D")
                    df = client.get_candles(symbol, bar, count)
                elif name == "akshare":
                    base = symbol.split("-")[0].split("/")[0].upper()
                    df = client.get_stock_price(base, count=count)
                else:
                    continue

                if df is not None and not df.empty:
                    return df
            except Exception as e:
                logger.debug("get_ohlcv via %s 失败: %s", name, e)
                continue
        return pd.DataFrame()

    # ==================== 24hr 统计 ====================

    def get_24hr(self, symbol: str) -> Optional[dict]:
        """获取 24 小时统计"""
        for name, getter in self._sources():
            client = getter()
            if client is None:
                continue
            try:
                if name == "binance":
                    result = client.get_24hr(symbol)
                    if result:
                        return {**result, "source": "binance"}
                elif name == "okx":
                    result = client.get_ticker(symbol)
                    if result:
                        return {
                            "symbol": result["inst_id"],
                            "price": result["price"],
                            "high": result["high_24h"],
                            "low": result["low_24h"],
                            "volume": result["volume_24h"],
                            "source": "okx",
                        }
            except Exception as e:
                logger.debug("get_24hr via %s 失败: %s", name, e)
                continue
        return None

    # ==================== 持仓量 ====================

    def get_open_interest(self, symbol: str) -> Optional[dict]:
        """获取持仓量"""
        for name, getter in self._sources():
            client = getter()
            if client is None:
                continue
            try:
                if name == "binance":
                    result = client.get_futures_oi(symbol)
                    if result:
                        return {**result, "source": "binance"}
                elif name == "okx":
                    result = client.get_open_interest(symbol)
                    if result:
                        return {
                            "symbol": result["inst_id"],
                            "open_interest": result["oi"],
                            "source": "okx",
                        }
            except Exception as e:
                logger.debug("get_open_interest via %s 失败: %s", name, e)
                continue
        return None

    # ==================== 资金费率 ====================

    def get_funding_rate(self, symbol: str) -> pd.DataFrame:
        """获取资金费率历史（优先 Binance）"""
        binance = self._get_binance()
        if binance:
            try:
                df = binance.get_funding_rate(symbol)
                if not df.empty:
                    df["source"] = "binance"
                    return df
            except Exception:
                pass

        okx = self._get_okx()
        if okx:
            try:
                result = okx.get_funding_rate(symbol)
                if result:
                    return pd.DataFrame([{
                        "date": pd.Timestamp.now(),
                        "funding_rate": result["funding_rate"],
                        "source": "okx",
                    }])
            except Exception:
                pass

        return pd.DataFrame()

    # ==================== 双交易所对比 ====================

    def get_funding_comparison(self, symbol: str) -> dict:
        """Binance vs OKX 资金费率对比"""
        result = {"symbol": symbol, "binance": None, "okx": None}

        binance = self._get_binance()
        if binance:
            try:
                df = binance.get_funding_rate(symbol, limit=1)
                if not df.empty:
                    result["binance"] = float(df.iloc[-1]["funding_rate"])
            except Exception:
                pass

        okx = self._get_okx()
        if okx:
            try:
                r = okx.get_funding_rate(symbol)
                if r:
                    result["okx"] = r["funding_rate"]
            except Exception:
                pass

        if result["binance"] is not None and result["okx"] is not None:
            result["spread"] = result["binance"] - result["okx"]

        return result
