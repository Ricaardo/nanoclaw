"""美元面板 — DTWEXBGS (yfinance UUP fallback)"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)


def analyze(fred_client, lookback_days=730):
    """分析美元面板"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    # 尝试 FRED DTWEXBGS
    series = []
    source = "FRED"
    try:
        series = fred_client.get_series("DTWEXBGS", start=start, end=end)
    except Exception as e:
        logger.warning("FRED DTWEXBGS 获取失败: %s", e)

    # Fallback to yfinance UUP
    if not series:
        try:
            import yfinance as yf
            df = yf.download("UUP", start=start, end=end, progress=False)
            if df is not None and len(df) > 0:
                series = [
                    {"date": d.strftime("%Y-%m-%d"), "value": float(row["Close"])}
                    for d, row in df.iterrows()
                ]
                source = "yfinance (UUP)"
        except Exception as e:
            logger.warning("yfinance UUP fallback 失败: %s", e)

    if not series:
        return {"data_available": False, "as_of": None, "metrics": {}, "changes": {}}

    current = series[-1]
    metrics = {
        "current": current["value"],
        "date": current["date"],
        "source": source,
    }

    # 30d/90d changes
    changes = {}
    for label, days in [("30d", 30), ("90d", 90)]:
        prev = _find_nearest(series, current["date"], days)
        if prev is not None:
            change = round(current["value"] - prev, 2)
            change_pct = round((current["value"] / prev - 1) * 100, 2) if prev != 0 else None
            changes[label] = {"absolute": change, "pct": change_pct}

    # 2-year percentile
    if len(series) > 20:
        values = [obs["value"] for obs in series]
        current_val = current["value"]
        below = sum(1 for v in values if v < current_val)
        percentile = round(below / len(values) * 100, 1)
        metrics["percentile_2y"] = percentile

    return {
        "data_available": True,
        "as_of": current["date"],
        "metrics": metrics,
        "changes": changes,
    }


def _find_nearest(series, ref_date, days_back):
    if not series:
        return None
    target = (datetime.strptime(ref_date, "%Y-%m-%d") - timedelta(days=days_back)).strftime("%Y-%m-%d")
    best = None
    best_dist = float("inf")
    for obs in series:
        dist = abs((datetime.strptime(obs["date"], "%Y-%m-%d") - datetime.strptime(target, "%Y-%m-%d")).days)
        if dist < best_dist:
            best_dist = dist
            best = obs["value"]
    if best_dist <= 5:
        return best
    return None
