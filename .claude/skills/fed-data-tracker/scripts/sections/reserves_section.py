"""TGA & RRP 面板 — WTREGEN, RRPONTSYD"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

RESERVE_SERIES = {
    "WTREGEN": "财政部一般账户 (TGA)",
    "RRPONTSYD": "隔夜逆回购 (RRP)",
}


def analyze(fred_client, lookback_days=365):
    """分析 TGA & RRP 面板"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    data = {}
    for sid in RESERVE_SERIES:
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

        val_billions = round(current["value"] / 1000, 1) if sid == "WTREGEN" else round(current["value"] / 1000, 1)
        metrics[sid] = {
            "name": RESERVE_SERIES[sid],
            "value_millions": current["value"],
            "value_billions": val_billions,
            "date": current["date"],
        }

        ch = {}
        for label, days in [("1w", 7), ("1m", 30), ("3m", 90)]:
            prev = _find_nearest(series, current["date"], days)
            if prev is not None:
                change_m = round(current["value"] - prev, 0)
                change_b = round(change_m / 1000, 1)
                ch[label] = {"millions": change_m, "billions": change_b}
        changes[sid] = ch

    return {
        "data_available": True,
        "as_of": latest_date,
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
