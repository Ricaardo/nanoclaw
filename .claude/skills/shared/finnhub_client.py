"""
Finnhub API 客户端

支持:
- 市场新闻（general/forex/crypto/merger）
- 公司新闻（按 ticker）
- 经济日历

用法:
    from finnhub_client import FinnhubClient
    client = FinnhubClient()  # 使用 FINNHUB_API_KEY 环境变量
    news = client.get_market_news("general")
    print(f"{len(news)} articles")

API 文档: https://finnhub.io/docs/api
免费额度: 60 req/min
"""

import logging
import os
import time
from datetime import datetime, timedelta
from typing import Optional

logger = logging.getLogger(__name__)

try:
    import requests
    HAS_REQUESTS = True
except ImportError:
    HAS_REQUESTS = False


class FinnhubClient:
    """Finnhub API 客户端"""

    BASE = "https://finnhub.io/api/v1"
    RATE_LIMIT_DELAY = 1.0  # 1s 限速（免费 60req/min）

    def __init__(self, api_key: Optional[str] = None):
        if not HAS_REQUESTS:
            raise RuntimeError("requests 未安装: pip install requests")
        self._api_key = api_key or os.environ.get("FINNHUB_API_KEY", "")
        if not self._api_key:
            logger.warning("FINNHUB_API_KEY 未设置，API 调用将失败")
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "InvestSkills/2.2"})
        self._last_call = 0
        self._call_count = 0

    def _get(self, endpoint: str, params: Optional[dict] = None) -> Optional[any]:
        """带限速的 GET 请求"""
        elapsed = time.time() - self._last_call
        if elapsed < self.RATE_LIMIT_DELAY:
            time.sleep(self.RATE_LIMIT_DELAY - elapsed)

        url = f"{self.BASE}/{endpoint}"
        req_params = {"token": self._api_key}
        if params:
            req_params.update(params)

        try:
            resp = self._session.get(url, params=req_params, timeout=15)
            self._last_call = time.time()
            self._call_count += 1

            if resp.status_code == 200:
                return resp.json()
            if resp.status_code == 429:
                logger.warning("Finnhub API 限速，等待 3 秒后重试")
                time.sleep(3)
                resp = self._session.get(url, params=req_params, timeout=15)
                self._last_call = time.time()
                self._call_count += 1
                if resp.status_code == 200:
                    return resp.json()
            logger.warning("Finnhub API %s 返回 %d: %s", endpoint, resp.status_code, resp.text[:200])
            return None
        except Exception as e:
            logger.error("Finnhub 请求失败: %s", e)
            return None

    def get_market_news(self, category: str = "general", min_id: Optional[int] = None) -> list[dict]:
        """
        获取市场新闻 /news

        Args:
            category: general, forex, crypto, merger
            min_id: 只返回 id > min_id 的新闻（分页用）

        Returns:
            list[dict]: [{id, category, headline, summary, source, url, datetime, image}, ...]
        """
        params = {"category": category}
        if min_id is not None:
            params["minId"] = min_id

        data = self._get("news", params)
        if not data or not isinstance(data, list):
            return []

        results = []
        for article in data:
            results.append({
                "id": article.get("id"),
                "category": article.get("category", ""),
                "headline": article.get("headline", ""),
                "summary": article.get("summary", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "datetime": datetime.fromtimestamp(article["datetime"]).isoformat()
                    if article.get("datetime") else None,
                "timestamp": article.get("datetime"),
            })
        return results

    def get_company_news(
        self,
        symbol: str,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[dict]:
        """
        获取公司新闻 /company-news

        Args:
            symbol: 股票代码（如 AAPL）
            from_date: 开始日期 YYYY-MM-DD（默认 7 天前）
            to_date: 结束日期 YYYY-MM-DD（默认今天）

        Returns:
            list[dict]: [{headline, summary, source, url, datetime, category}, ...]
        """
        today = datetime.now()
        if not to_date:
            to_date = today.strftime("%Y-%m-%d")
        if not from_date:
            from_date = (today - timedelta(days=7)).strftime("%Y-%m-%d")

        params = {
            "symbol": symbol.upper(),
            "from": from_date,
            "to": to_date,
        }

        data = self._get("company-news", params)
        if not data or not isinstance(data, list):
            return []

        results = []
        for article in data:
            results.append({
                "category": article.get("category", ""),
                "headline": article.get("headline", ""),
                "summary": article.get("summary", ""),
                "source": article.get("source", ""),
                "url": article.get("url", ""),
                "datetime": datetime.fromtimestamp(article["datetime"]).isoformat()
                    if article.get("datetime") else None,
                "timestamp": article.get("datetime"),
            })
        return results

    def get_economic_calendar(
        self,
        from_date: Optional[str] = None,
        to_date: Optional[str] = None,
    ) -> list[dict]:
        """
        获取经济日历 /calendar/economic

        Args:
            from_date: 开始日期 YYYY-MM-DD（默认今天）
            to_date: 结束日期 YYYY-MM-DD（默认 14 天后）

        Returns:
            list[dict]: [{event, country, date, time, impact, actual, estimate, prev, unit}, ...]
        """
        today = datetime.now()
        if not from_date:
            from_date = today.strftime("%Y-%m-%d")
        if not to_date:
            to_date = (today + timedelta(days=14)).strftime("%Y-%m-%d")

        params = {
            "from": from_date,
            "to": to_date,
        }

        data = self._get("calendar/economic", params)
        if not data or not isinstance(data, dict):
            return []

        events = data.get("economicCalendar", [])
        results = []
        for evt in events:
            results.append({
                "event": evt.get("event", ""),
                "country": evt.get("country", ""),
                "date": evt.get("date", ""),
                "time": evt.get("time", ""),
                "impact": evt.get("impact", ""),
                "actual": evt.get("actual"),
                "estimate": evt.get("estimate"),
                "prev": evt.get("prev"),
                "unit": evt.get("unit", ""),
            })
        return results

    def get_quote(self, symbol: str) -> Optional[dict]:
        """
        获取实时报价 /quote

        支持: 美股 ETF (SPY, UUP, GLD, EFA, EEM), 期货 (CL), 加密 (BINANCE:BTCUSDT)

        Returns:
            dict: {"symbol", "price", "change", "change_pct", "high", "low", "open", "prev_close", "timestamp"}
        """
        data = self._get("quote", {"symbol": symbol})
        if not data or data.get("c", 0) == 0:
            return None

        return {
            "symbol": symbol,
            "price": data.get("c"),       # current
            "change": data.get("d"),       # change
            "change_pct": data.get("dp"),  # change percent
            "high": data.get("h"),
            "low": data.get("l"),
            "open": data.get("o"),
            "prev_close": data.get("pc"),
            "timestamp": data.get("t"),
        }

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
            "client": "Finnhub",
            "has_api_key": bool(self._api_key),
            "call_count": self._call_count,
            "rate_limit": "60 req/min",
        }
