"""就业面板 — UNRATE, PAYEMS, ICSA"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

EMPLOYMENT_SERIES = {
    "UNRATE": "失业率",
    "PAYEMS": "非农就业人数（千人）",
    "ICSA": "首次申请失业救济",
}


def analyze(fred_client, lookback_days=365):
    """分析就业面板"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    data = {}
    for sid in EMPLOYMENT_SERIES:
        try:
            series = fred_client.get_series(sid, start=start, end=end)
            if series:
                data[sid] = series
        except Exception as e:
            logger.warning("获取 %s 失败: %s", sid, e)

    if not data:
        return {"data_available": False, "as_of": None, "metrics": {}, "changes": {}}

    metrics = {}
    latest_date = None

    # 失业率
    unrate = data.get("UNRATE")
    if unrate and len(unrate) >= 2:
        current = unrate[-1]
        metrics["UNRATE"] = {
            "name": "失业率",
            "value": current["value"],
            "date": current["date"],
            "prev_month": unrate[-2]["value"] if len(unrate) >= 2 else None,
            "change_mom": round(current["value"] - unrate[-2]["value"], 2) if len(unrate) >= 2 else None,
        }
        if latest_date is None or current["date"] > (latest_date or ""):
            latest_date = current["date"]

    # 非农
    payems = data.get("PAYEMS")
    if payems and len(payems) >= 2:
        current = payems[-1]
        nfp_change = round(current["value"] - payems[-2]["value"], 0)
        metrics["PAYEMS"] = {
            "name": "非农就业人数",
            "value_thousands": current["value"],
            "date": current["date"],
            "monthly_change_thousands": nfp_change,
        }
        # 3-month average
        if len(payems) >= 4:
            changes = [payems[-i]["value"] - payems[-i - 1]["value"] for i in range(1, 4)]
            metrics["PAYEMS"]["three_month_avg_thousands"] = round(sum(changes) / 3, 0)
        if latest_date is None or current["date"] > (latest_date or ""):
            latest_date = current["date"]

    # 初请
    icsa = data.get("ICSA")
    if icsa and len(icsa) >= 1:
        current = icsa[-1]
        metrics["ICSA"] = {
            "name": "首次申请失业救济",
            "value": current["value"],
            "date": current["date"],
        }
        # 4-week moving average
        if len(icsa) >= 4:
            four_week_avg = round(sum(obs["value"] for obs in icsa[-4:]) / 4, 0)
            metrics["ICSA"]["four_week_avg"] = four_week_avg
        if latest_date is None or current["date"] > (latest_date or ""):
            latest_date = current["date"]

    return {
        "data_available": True,
        "as_of": latest_date,
        "metrics": metrics,
    }
