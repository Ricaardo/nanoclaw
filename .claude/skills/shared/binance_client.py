"""
Binance 公开 REST API 客户端（无需 API Key）

支持:
- 现货行情（价格、K线、24hr 统计）
- 合约数据（持仓量、资金费率）

用法:
    from binance_client import BinanceClient
    client = BinanceClient()
    print(client.get_price("BTC"))
    df = client.get_klines("ETH", "1d", 30)
"""

import logging
import time
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


def _normalize_symbol(symbol: str) -> str:
    """
    将各种格式标准化为 Binance 格式 (BTCUSDT)

    BTC / BTC-USD / BTC/USDT / btcusdt -> BTCUSDT
    """
    s = symbol.strip().upper()
    # 移除分隔符
    for sep in ["-", "/"]:
        s = s.replace(sep, "")
    # 移除常见后缀并统一为 USDT
    for suffix in ["USD", "BUSD"]:
        if s.endswith(suffix) and not s.endswith("USDT"):
            s = s[: -len(suffix)] + "USDT"
    # 只有当 ticker 已包含报价币种后缀（且不是 ticker 本身）时才不追加
    has_quote = False
    for q in ["USDT", "BUSD"]:
        if s.endswith(q) and len(s) > len(q):
            has_quote = True
            break
    if not has_quote:
        s = s + "USDT"
    return s


class BinanceClient:
    """Binance 公开 REST API 客户端"""

    BASE = "https://api.binance.com"
    FAPI = "https://fapi.binance.com"
    RATE_LIMIT_DELAY = 0.2  # 200ms 限速

    def __init__(self):
        if not HAS_REQUESTS:
            raise RuntimeError("requests 未安装: pip install requests")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "InvestSkills/2.1"})
        self._last_call = 0

    def _get(self, url: str, params: Optional[dict] = None) -> Optional[dict]:
        """带限速的 GET 请求"""
        elapsed = time.time() - self._last_call
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)

        try:
            resp = self._session.get(url, params=params, timeout=15)
            self._last_call = time.time()
            if resp.status_code == 200:
                return resp.json()
            logger.warning("Binance API %s 返回 %d: %s", url, resp.status_code, resp.text[:200])
            return None
        except Exception as e:
            logger.error("Binance 请求失败: %s", e)
            return None

    # ==================== 现货 ====================

    def get_price(self, symbol: str) -> Optional[dict]:
        """获取最新价格 /api/v3/ticker/price"""
        sym = _normalize_symbol(symbol)
        data = self._get(f"{self.BASE}/api/v3/ticker/price", {"symbol": sym})
        if data:
            return {"symbol": sym, "price": float(data["price"])}
        return None

    def get_klines(self, symbol: str, interval: str = "1d", limit: int = 100) -> pd.DataFrame:
        """
        获取 K 线数据 /api/v3/klines

        Args:
            symbol: 交易对
            interval: 1m/5m/15m/1h/4h/1d/1w/1M
            limit: 数据条数 (最大 1000)

        Returns:
            DataFrame: date, open, high, low, close, volume
        """
        sym = _normalize_symbol(symbol)
        data = self._get(f"{self.BASE}/api/v3/klines", {
            "symbol": sym,
            "interval": interval,
            "limit": min(limit, 1000),
        })
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            "open_time", "open", "high", "low", "close", "volume",
            "close_time", "quote_volume", "trades", "taker_buy_base",
            "taker_buy_quote", "ignore",
        ])
        df["date"] = pd.to_datetime(df["open_time"], unit="ms")
        for col in ["open", "high", "low", "close", "volume"]:
            df[col] = df[col].astype(float)
        return df[["date", "open", "high", "low", "close", "volume"]].reset_index(drop=True)

    def get_24hr(self, symbol: str) -> Optional[dict]:
        """获取 24 小时统计 /api/v3/ticker/24hr"""
        sym = _normalize_symbol(symbol)
        data = self._get(f"{self.BASE}/api/v3/ticker/24hr", {"symbol": sym})
        if data:
            return {
                "symbol": sym,
                "price": float(data.get("lastPrice", 0)),
                "price_change_pct": float(data.get("priceChangePercent", 0)),
                "high": float(data.get("highPrice", 0)),
                "low": float(data.get("lowPrice", 0)),
                "volume": float(data.get("volume", 0)),
                "quote_volume": float(data.get("quoteVolume", 0)),
            }
        return None

    # ==================== 合约 ====================

    def get_futures_oi(self, symbol: str) -> Optional[dict]:
        """获取合约持仓量 /fapi/v1/openInterest"""
        sym = _normalize_symbol(symbol)
        data = self._get(f"{self.FAPI}/fapi/v1/openInterest", {"symbol": sym})
        if data:
            return {
                "symbol": sym,
                "open_interest": float(data.get("openInterest", 0)),
                "time": data.get("time"),
            }
        return None

    def get_funding_rate(self, symbol: str, limit: int = 30) -> pd.DataFrame:
        """获取资金费率历史 /fapi/v1/fundingRate"""
        sym = _normalize_symbol(symbol)
        data = self._get(f"{self.FAPI}/fapi/v1/fundingRate", {
            "symbol": sym,
            "limit": min(limit, 1000),
        })
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data)
        df["date"] = pd.to_datetime(df["fundingTime"], unit="ms")
        df["funding_rate"] = df["fundingRate"].astype(float)
        return df[["date", "funding_rate", "fundingTime"]].reset_index(drop=True)
