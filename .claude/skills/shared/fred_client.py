"""
FRED (Federal Reserve Economic Data) API 客户端

支持:
- 经济数据时间序列（利率/通胀/就业/资产负债表）
- 批量获取多个 Series
- 元数据查询

用法:
    from fred_client import FREDClient
    client = FREDClient()  # 使用 FRED_API_KEY 环境变量
    print(client.get_latest("FEDFUNDS"))
    data = client.get_series("WALCL", start="2023-01-01")

API 文档: https://fred.stlouisfed.org/docs/api/fred/
免费额度: 120 req/min
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


# 常用 FRED Series 快速参考
FRED_SERIES = {
    # 利率
    "FEDFUNDS": "联邦基金有效利率",
    "DFF": "联邦基金日利率",
    "SOFR": "担保隔夜融资利率",
    "GS2": "2 年期国债收益率",
    "GS5": "5 年期国债收益率",
    "GS10": "10 年期国债收益率",
    "GS30": "30 年期国债收益率",
    "DGS1MO": "1 月期国债收益率",
    "DGS3MO": "3 月期国债收益率",
    # 资产负债表
    "WALCL": "Fed 总资产",
    "TREAST": "Fed 持有国债",
    "WSHOMCB": "Fed 持有 MBS",
    # TGA & RRP
    "WTREGEN": "财政部一般账户 (TGA)",
    "RRPONTSYD": "隔夜逆回购 (RRP)",
    # 通胀
    "CPIAUCSL": "CPI（所有城市消费者）",
    "CPILFESL": "核心 CPI（剔除食品能源）",
    "PCEPI": "PCE 价格指数",
    "PCEPILFE": "核心 PCE",
    # 就业
    "UNRATE": "失业率",
    "PAYEMS": "非农就业人数",
    "ICSA": "首次申请失业救济",
    # 美元
    "DTWEXBGS": "美元贸易加权指数",
    # 信用
    "BAMLH0A0HYM2": "高收益债 OAS 利差",
}


def _parse_value(val: str) -> Optional[float]:
    """将 FRED 返回的字符串值转为 float，'.' 表示缺失"""
    if val is None or val == "." or val == "":
        return None
    try:
        return float(val)
    except (ValueError, TypeError):
        return None


class FREDClient:
    """FRED API 客户端"""

    BASE = "https://api.stlouisfed.org/fred"
    RATE_LIMIT_DELAY = 0.5  # 500ms 限速（免费 120req/min）

    def __init__(self, api_key: Optional[str] = None):
        if not HAS_REQUESTS:
            raise RuntimeError("requests 未安装: pip install requests")
        self._api_key = api_key or os.environ.get("FRED_API_KEY", "")
        if not self._api_key:
            logger.warning("FRED_API_KEY 未设置，API 调用将失败")
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
        req_params = {"api_key": self._api_key, "file_type": "json"}
        if params:
            req_params.update(params)

        try:
            resp = self._session.get(url, params=req_params, timeout=15)
            self._last_call = time.time()
            self._call_count += 1

            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                logger.warning("FRED API 限速，等待 2 秒后重试")
                time.sleep(2)
                resp = self._session.get(url, params=req_params, timeout=15)
                self._last_call = time.time()
                self._call_count += 1
                if resp.status_code == 200:
                    return resp.json()
            logger.warning("FRED API %s 返回 %d: %s", endpoint, resp.status_code, resp.text[:200])
            return None
        except Exception as e:
            logger.error("FRED 请求失败: %s", e)
            return None

    def get_series(
        self,
        series_id: str,
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: Optional[int] = None,
        sort_order: str = "asc",
    ) -> list[dict]:
        """
        获取时间序列数据 /series/observations

        Args:
            series_id: FRED Series ID（如 FEDFUNDS, WALCL）
            start: 开始日期 YYYY-MM-DD
            end: 结束日期 YYYY-MM-DD
            limit: 返回数量限制
            sort_order: asc 或 desc

        Returns:
            list[dict]: [{"date": "2024-01-01", "value": 5.33}, ...]
        """
        params = {
            "series_id": series_id,
            "sort_order": sort_order,
        }
        if start:
            params["observation_start"] = start
        if end:
            params["observation_end"] = end
        if limit:
            params["limit"] = limit

        data = self._get("series/observations", params)
        if not data or "observations" not in data:
            logger.warning("FRED series %s 无数据", series_id)
            return []

        results = []
        for obs in data["observations"]:
            val = _parse_value(obs.get("value"))
            if val is not None:
                results.append({
                    "date": obs.get("date"),
                    "value": val,
                })
        return results

    def get_latest(self, series_id: str) -> Optional[dict]:
        """
        获取 Series 最新值

        Returns:
            dict: {"series_id": "FEDFUNDS", "date": "2024-01-01", "value": 5.33}
        """
        data = self.get_series(series_id, limit=1, sort_order="desc")
        if data:
            return {
                "series_id": series_id,
                "date": data[0]["date"],
                "value": data[0]["value"],
            }
        return None

    def get_series_info(self, series_id: str) -> Optional[dict]:
        """
        获取 Series 元数据 /series

        Returns:
            dict: 包含 title, frequency, units, notes 等
        """
        data = self._get("series", {"series_id": series_id})
        if data and "seriess" in data and data["seriess"]:
            info = data["seriess"][0]
            return {
                "series_id": info.get("id"),
                "title": info.get("title"),
                "frequency": info.get("frequency"),
                "units": info.get("units"),
                "seasonal_adjustment": info.get("seasonal_adjustment"),
                "last_updated": info.get("last_updated"),
                "notes": info.get("notes", "")[:500],
            }
        return None

    def get_multiple_series(
        self,
        series_ids: list[str],
        start: Optional[str] = None,
        end: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> dict[str, list[dict]]:
        """
        批量获取多个 Series

        Returns:
            dict: {series_id: [observations]}
        """
        results = {}
        for sid in series_ids:
            data = self.get_series(sid, start=start, end=end, limit=limit)
            results[sid] = data
        return results

    def get_api_stats(self) -> dict:
        """返回 API 使用统计"""
        return {
            "client": "FRED",
            "has_api_key": bool(self._api_key),
            "call_count": self._call_count,
            "rate_limit": "120 req/min",
        }
