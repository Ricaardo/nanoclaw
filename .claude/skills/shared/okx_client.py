"""
OKX 公开 REST API 客户端（无需 API Key）

支持:
- 现货行情（Ticker、K 线）
- 合约数据（资金费率、持仓量）
- 期权数据（合约列表、Greeks）

用法:
    from okx_client import OKXClient
    client = OKXClient()
    print(client.get_ticker("BTC-USDT"))
    df = client.get_option_market_data("BTC-USD")
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


def _normalize_inst_id(symbol: str, inst_type: str = "SPOT") -> str:
    """
    标准化为 OKX 格式

    BTC -> BTC-USDT (现货) / BTC-USDT-SWAP (永续)
    BTC-USDT -> BTC-USDT
    """
    s = symbol.strip().upper()
    # 已经是 OKX 格式
    if "-" in s:
        return s
    # 移除常见后缀
    for suffix in ["USDT", "USD", "BUSD"]:
        if s.endswith(suffix):
            s = s[: -len(suffix)]
            break
    if inst_type == "SWAP":
        return f"{s}-USDT-SWAP"
    return f"{s}-USDT"


class OKXClient:
    """OKX 公开 REST API 客户端"""

    BASE = "https://www.okx.com"
    RATE_LIMIT_DELAY = 0.2

    def __init__(self):
        if not HAS_REQUESTS:
            raise RuntimeError("requests 未安装: pip install requests")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "InvestSkills/2.1"})
        self._last_call = 0

    def _get(self, path: str, params: Optional[dict] = None) -> Optional[list]:
        """带限速的 GET 请求，自动解包 {"code":"0","data":[...]}"""
        elapsed = time.time() - self._last_call
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)

        url = f"{self.BASE}{path}"
        try:
            resp = self._session.get(url, params=params, timeout=15)
            self._last_call = time.time()
            if resp.status_code != 200:
                logger.warning("OKX API %s 返回 %d", path, resp.status_code)
                return None

            body = resp.json()
            if body.get("code") != "0":
                logger.warning("OKX API 错误: code=%s msg=%s", body.get("code"), body.get("msg"))
                return None
            return body.get("data", [])
        except Exception as e:
            logger.error("OKX 请求失败: %s", e)
            return None

    # ==================== 现货 ====================

    def get_ticker(self, inst_id: str) -> Optional[dict]:
        """获取行情 /api/v5/market/ticker"""
        inst = _normalize_inst_id(inst_id)
        data = self._get("/api/v5/market/ticker", {"instId": inst})
        if data and len(data) > 0:
            t = data[0]
            return {
                "inst_id": t.get("instId"),
                "price": float(t.get("last", 0)),
                "open_24h": float(t.get("open24h", 0)),
                "high_24h": float(t.get("high24h", 0)),
                "low_24h": float(t.get("low24h", 0)),
                "volume_24h": float(t.get("vol24h", 0)),
                "volume_ccy_24h": float(t.get("volCcy24h", 0)),
            }
        return None

    def get_candles(self, inst_id: str, bar: str = "1D", limit: int = 100) -> pd.DataFrame:
        """
        获取 K 线 /api/v5/market/candles

        Args:
            inst_id: 合约 ID
            bar: 1m/5m/15m/1H/4H/1D/1W/1M
            limit: 数据条数 (最大 300)
        """
        inst = _normalize_inst_id(inst_id)
        data = self._get("/api/v5/market/candles", {
            "instId": inst,
            "bar": bar,
            "limit": str(min(limit, 300)),
        })
        if not data:
            return pd.DataFrame()

        df = pd.DataFrame(data, columns=[
            "ts", "open", "high", "low", "close", "vol", "volCcy", "volCcyQuote", "confirm",
        ])
        df["date"] = pd.to_datetime(df["ts"].astype(int), unit="ms")
        for col in ["open", "high", "low", "close", "vol"]:
            df[col] = df[col].astype(float)
        df = df[["date", "open", "high", "low", "close", "vol"]].rename(columns={"vol": "volume"})
        return df.sort_values("date").reset_index(drop=True)

    # ==================== 合约 ====================

    def get_funding_rate(self, inst_id: str) -> Optional[dict]:
        """获取当前资金费率 /api/v5/public/funding-rate"""
        inst = _normalize_inst_id(inst_id, "SWAP")
        data = self._get("/api/v5/public/funding-rate", {"instId": inst})
        if data and len(data) > 0:
            r = data[0]
            return {
                "inst_id": r.get("instId"),
                "funding_rate": float(r.get("fundingRate", 0)),
                "next_funding_rate": float(r.get("nextFundingRate", 0)) if r.get("nextFundingRate") else None,
                "funding_time": r.get("fundingTime"),
            }
        return None

    def get_open_interest(self, inst_id: str) -> Optional[dict]:
        """获取持仓量 /api/v5/public/open-interest"""
        inst = _normalize_inst_id(inst_id, "SWAP")
        data = self._get("/api/v5/public/open-interest", {"instId": inst, "instType": "SWAP"})
        if data and len(data) > 0:
            r = data[0]
            return {
                "inst_id": r.get("instId"),
                "oi": float(r.get("oi", 0)),
                "oi_ccy": float(r.get("oiCcy", 0)),
                "ts": r.get("ts"),
            }
        return None

    # ==================== 期权 ====================

    def get_option_instruments(self, underlying: str) -> list:
        """
        获取期权合约列表 /api/v5/public/instruments?instType=OPTION

        Args:
            underlying: 标的，如 BTC-USD
        """
        ul = underlying.strip().upper()
        if "-" not in ul:
            ul = f"{ul}-USD"
        data = self._get("/api/v5/public/instruments", {
            "instType": "OPTION",
            "uly": ul,
        })
        if not data:
            return []
        return [
            {
                "inst_id": d.get("instId"),
                "underlying": d.get("uly"),
                "opt_type": d.get("optType"),  # C / P
                "strike": float(d.get("stk", 0)),
                "expiry": d.get("expTime"),
                "state": d.get("state"),
            }
            for d in data
            if d.get("state") == "live"
        ]

    def get_option_market_data(self, underlying: str) -> pd.DataFrame:
        """
        获取期权行情（含 Greeks）/api/v5/market/option/market-data（公开接口，无需登录）

        注意: 此接口仅在 OKX 国际站可用，且仅返回活跃合约数据。
        如接口不可用，返回空 DataFrame。
        """
        ul = underlying.strip().upper()
        if "-" not in ul:
            ul = f"{ul}-USD"

        # OKX 公开期权行情需要 instFamily 参数
        data = self._get("/api/v5/public/opt-summary", {"instFamily": ul})
        if not data:
            return pd.DataFrame()

        rows = []
        for d in data:
            rows.append({
                "inst_id": d.get("instId"),
                "underlying": ul,
                "bid": float(d.get("bidPx", 0)) if d.get("bidPx") else 0,
                "ask": float(d.get("askPx", 0)) if d.get("askPx") else 0,
                "mark_price": float(d.get("markPx", 0)) if d.get("markPx") else 0,
                "delta": float(d.get("delta", 0)) if d.get("delta") else 0,
                "gamma": float(d.get("gamma", 0)) if d.get("gamma") else 0,
                "theta": float(d.get("theta", 0)) if d.get("theta") else 0,
                "vega": float(d.get("vega", 0)) if d.get("vega") else 0,
                "vol": float(d.get("vol", 0)) if d.get("vol") else 0,
                "open_interest": float(d.get("oi", 0)) if d.get("oi") else 0,
            })
        return pd.DataFrame(rows)
