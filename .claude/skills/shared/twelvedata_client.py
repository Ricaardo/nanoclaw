"""
Twelve Data REST API 客户端

支持:
- 实时报价（股票/ETF/商品/加密）
- 时间序列（日/周/月 K 线）

用法:
    from twelvedata_client import TwelveDataClient
    client = TwelveDataClient()  # 使用 TWELVEDATA_API_KEY 环境变量
    quote = client.get_quote("SPY")
    series = client.get_time_series("BTC/USD", interval="1day", outputsize=30)

API 文档: https://twelvedata.com/docs
免费额度: 800 req/day, 8 req/min
"""

import logging
import os
import time
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


# Yahoo Finance → Twelve Data 符号映射
_SYMBOL_MAP = {
    "GC=F": "XAU/USD",
    "SI=F": "XAG/USD",
    "CL=F": "WTI/USD",
    "BZ=F": "BZ/USD",
    "BTC-USD": "BTC/USD",
    "ETH-USD": "ETH/USD",
    "^VIX": "VIX",
    "^GSPC": "SPX",
    "^DJI": "DJI",
    "^IXIC": "IXIC",
}


def _map_symbol(symbol: str) -> str:
    """将 Yahoo Finance 格式符号转换为 Twelve Data 格式"""
    s = symbol.strip()
    if s in _SYMBOL_MAP:
        return _SYMBOL_MAP[s]
    # 去掉 ^
    if s.startswith("^"):
        return s[1:]
    return s


class TwelveDataClient:
    """Twelve Data REST API 客户端"""

    BASE = "https://api.twelvedata.com"
    RATE_LIMIT_DELAY = 8.0  # 8 req/min on free tier

    def __init__(self, api_key: Optional[str] = None):
        if not HAS_REQUESTS:
            raise RuntimeError("requests 未安装: pip install requests")
        self._api_key = api_key or os.environ.get("TWELVEDATA_API_KEY", "")
        if not self._api_key:
            logger.warning("TWELVEDATA_API_KEY 未设置，API 调用将失败")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "InvestSkills/2.2"})
        self._last_call = 0
        self._call_count = 0

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[dict]:
        """带限速的 GET 请求"""
        elapsed = time.time() - self._last_call
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)

        url = f"{self.BASE}/{endpoint}"
        req_params = {"apikey": self._api_key}
        if params:
            req_params.update(params)

        try:
            resp = self._session.get(url, params=req_params, timeout=15)
            self._last_call = time.time()
            self._call_count += 1

            if resp.status_code == 200:
                data = resp.json()
                # Twelve Data 错误响应: {"code": 400, "message": "..."}
                if isinstance(data, dict) and data.get("code") and data["code"] != 200:
                    logger.warning("Twelve Data %s 错误: %s", endpoint, data.get("message", ""))
                    return None
                return data
            if resp.status_code == 429:
                logger.warning("Twelve Data 限速，等待 10 秒后重试")
                time.sleep(10)
                resp = self._session.get(url, params=req_params, timeout=15)
                self._last_call = time.time()
                self._call_count += 1
                if resp.status_code == 200:
                    return resp.json()
            logger.warning("Twelve Data %s 返回 %d: %s", endpoint, resp.status_code, resp.text[:200])
            return None
        except Exception as e:
            logger.error("Twelve Data 请求失败: %s", e)
            return None

    def get_quote(self, symbol: str) -> Optional[dict]:
        """
        获取实时报价 /quote

        Returns:
            dict: {"symbol", "price", "change", "change_pct", "open", "high", "low", "prev_close", "volume"}
        """
        td_sym = _map_symbol(symbol)
        data = self._get("quote", {"symbol": td_sym})
        if not data or not data.get("close"):
            return None

        try:
            price = float(data["close"])
        except (ValueError, TypeError):
            return None

        if price <= 0:
            return None

        def _float(v):
            try:
                return float(v)
            except (ValueError, TypeError):
                return None

        return {
            "symbol": symbol,
            "td_symbol": td_sym,
            "price": price,
            "change": _float(data.get("change")),
            "change_pct": _float(data.get("percent_change")),
            "open": _float(data.get("open")),
            "high": _float(data.get("high")),
            "low": _float(data.get("low")),
            "prev_close": _float(data.get("previous_close")),
            "volume": _float(data.get("volume")),
        }

    def get_time_series(
        self,
        symbol: str,
        interval: str = "1day",
        outputsize: int = 30,
    ) -> list[dict]:
        """
        获取时间序列 /time_series

        Args:
            symbol: 符号（自动转换 Yahoo → Twelve Data 格式）
            interval: 1min/5min/15min/30min/45min/1h/2h/4h/1day/1week/1month
            outputsize: 数据条数

        Returns:
            list[dict]: [{"datetime", "open", "high", "low", "close", "volume"}, ...] 按时间升序
        """
        td_sym = _map_symbol(symbol)
        data = self._get("time_series", {
            "symbol": td_sym,
            "interval": interval,
            "outputsize": str(outputsize),
        })
        if not data or "values" not in data:
            return []

        results = []
        for row in data["values"]:
            try:
                results.append({
                    "datetime": row.get("datetime", ""),
                    "open": float(row["open"]),
                    "high": float(row["high"]),
                    "low": float(row["low"]),
                    "close": float(row["close"]),
                    "volume": float(row.get("volume", 0)),
                })
            except (ValueError, KeyError):
                continue

        # Twelve Data 返回降序，反转为升序
        results.reverse()
        return results

    def get_quotes_batch(self, symbols: list[str]) -> dict[str, dict]:
        """批量获取报价（逐个调用，遵循限速）"""
        results = {}
        for sym in symbols:
            q = self.get_quote(sym)
            if q:
                results[sym] = q
        return results

    def get_api_stats(self) -> dict:
        """返回 API 使用统计"""
        return {
            "client": "TwelveData",
            "has_api_key": bool(self._api_key),
            "call_count": self._call_count,
            "rate_limit": "800 req/day, 8 req/min",
        }
