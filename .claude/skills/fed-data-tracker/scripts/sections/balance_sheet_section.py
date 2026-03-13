"""资产负债表面板 — WALCL, TREAST, WSHOMCB"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

BS_SERIES = {
    "WALCL": "Fed 总资产",
    "TREAST": "持有国债",
    "WSHOMCB": "持有 MBS",
}


def analyze(fred_client, lookback_days=365):
    """分析资产负债表面板"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    data = {}
    for sid in BS_SERIES:
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

        # FRED 资产负债表数据单位为百万美元
        val_trillions = round(current["value"] / 1_000_000, 3)
        metrics[sid] = {
            "name": BS_SERIES[sid],
            "value_millions": current["value"],
            "value_trillions": val_trillions,
            "date": current["date"],
        }

        # QT pace: weekly and monthly changes
        ch = {}
        for label, days in [("1w", 7), ("1m", 30), ("3m", 90)]:
            prev = _find_nearest(series, current["date"], days)
            if prev is not None:
                change_m = round(current["value"] - prev, 0)
                change_b = round(change_m / 1000, 1)
                ch[label] = {"millions": change_m, "billions": change_b}
        changes[sid] = ch

    # QT 速度计算（月均缩表速度）
    qt_pace = None
    walcl = data.get("WALCL")
    if walcl and len(walcl) >= 5:
        recent = walcl[-1]["value"]
        month_ago = _find_nearest(walcl, walcl[-1]["date"], 30)
        if month_ago is not None:
            qt_pace = round((recent - month_ago) / 1000, 1)  # 十亿美元/月

    return {
        "data_available": True,
        "as_of": latest_date,
        "metrics": metrics,
        "changes": changes,
        "qt_pace_billions_per_month": qt_pace,
    }


def _find_nearest(series, ref_date, days_back):
    """找到 days_back 天前最近的值"""
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
