"""利率面板 — FEDFUNDS, DFF, SOFR, GS2/5/10/30, DGS1MO/3MO"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

RATE_SERIES = {
    "FEDFUNDS": "联邦基金有效利率",
    "DFF": "联邦基金日利率",
    "SOFR": "SOFR",
    "DGS1MO": "1 月期国债",
    "DGS3MO": "3 月期国债",
    "GS2": "2 年期国债",
    "GS5": "5 年期国债",
    "GS10": "10 年期国债",
    "GS30": "30 年期国债",
}


def analyze(fred_client, lookback_days=365):
    """分析利率面板"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    data = {}
    for sid in RATE_SERIES:
        try:
            series = fred_client.get_series(sid, start=start, end=end)
            if series:
                data[sid] = series
        except Exception as e:
            logger.warning("获取 %s 失败: %s", sid, e)

    if not data:
        return {"data_available": False, "as_of": None, "metrics": {}, "changes": {}}

    metrics = {}
    changes = {}
    latest_date = None

    for sid, series in data.items():
        if not series:
            continue
        current = series[-1]
        if latest_date is None or current["date"] > (latest_date or ""):
            latest_date = current["date"]

        metrics[sid] = {
            "name": RATE_SERIES[sid],
            "value": current["value"],
            "date": current["date"],
        }

        # Calculate changes
        ch = {}
        for label, days in [("1w", 7), ("1m", 30), ("3m", 90)]:
            target_date = (datetime.strptime(current["date"], "%Y-%m-%d") - timedelta(days=days)).strftime("%Y-%m-%d")
            prev = _find_nearest(series, target_date)
            if prev is not None:
                ch[label] = round(current["value"] - prev, 4)
        changes[sid] = ch

    # Yield curve spreads
    spreads = {}
    gs2 = _latest_val(data.get("GS2"))
    gs10 = _latest_val(data.get("GS10"))
    dgs3mo = _latest_val(data.get("DGS3MO"))
    gs30 = _latest_val(data.get("GS30"))

    if gs2 is not None and gs10 is not None:
        spreads["2s10s"] = round(gs10 - gs2, 4)
    if dgs3mo is not None and gs10 is not None:
        spreads["3m10y"] = round(gs10 - dgs3mo, 4)
    if gs2 is not None and gs30 is not None:
        spreads["2s30s"] = round(gs30 - gs2, 4)

    return {
        "data_available": True,
        "as_of": latest_date,
        "metrics": metrics,
        "changes": changes,
        "spreads": spreads,
    }


def _latest_val(series):
    if series and len(series) > 0:
        return series[-1]["value"]
    return None


def _find_nearest(series, target_date):
    """找到最接近目标日期的值"""
    if not series:
        return None
    best = None
    best_dist = float("inf")
    for obs in series:
        dist = abs((datetime.strptime(obs["date"], "%Y-%m-%d") - datetime.strptime(target_date, "%Y-%m-%d")).days)
        if dist < best_dist:
            best_dist = dist
            best = obs["value"]
    if best_dist <= 5:
        return best
    return None
