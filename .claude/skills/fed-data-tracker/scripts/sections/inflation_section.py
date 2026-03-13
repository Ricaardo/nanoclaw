"""通胀面板 — CPIAUCSL, CPILFESL, PCEPI, PCEPILFE"""

import logging
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

INFLATION_SERIES = {
    "CPIAUCSL": "CPI（所有项目）",
    "CPILFESL": "核心 CPI（剔除食品能源）",
    "PCEPI": "PCE 价格指数",
    "PCEPILFE": "核心 PCE",
}

FED_TARGET = 2.0  # Fed 2% 通胀目标


def analyze(fred_client, lookback_days=730):
    """分析通胀面板（需要更长回溯期计算 YoY）"""
    end = datetime.now().strftime("%Y-%m-%d")
    start = (datetime.now() - timedelta(days=lookback_days)).strftime("%Y-%m-%d")

    data = {}
    for sid in INFLATION_SERIES:
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

    for sid, series in data.items():
        if not series or len(series) < 2:
            continue

        current = series[-1]
        if latest_date is None or current["date"] > (latest_date or ""):
            latest_date = current["date"]

        m = {"name": INFLATION_SERIES[sid], "date": current["date"], "level": current["value"]}

        # YoY%
        yoy_prev = _find_by_offset(series, current["date"], 12)
        if yoy_prev is not None and yoy_prev > 0:
            m["yoy_pct"] = round((current["value"] / yoy_prev - 1) * 100, 2)
            m["vs_target"] = round(m["yoy_pct"] - FED_TARGET, 2)

        # MoM%
        if len(series) >= 2:
            prev_month = series[-2]["value"]
            if prev_month > 0:
                m["mom_pct"] = round((current["value"] / prev_month - 1) * 100, 3)

        # 3-month annualized
        three_mo_prev = _find_by_offset(series, current["date"], 3)
        if three_mo_prev is not None and three_mo_prev > 0:
            ratio = current["value"] / three_mo_prev
            m["three_month_annualized"] = round((ratio ** 4 - 1) * 100, 2)

        metrics[sid] = m

    return {
        "data_available": True,
        "as_of": latest_date,
        "metrics": metrics,
        "fed_target": FED_TARGET,
    }


def _find_by_offset(series, ref_date, months_back):
    """找到约 N 个月前的值"""
    ref = datetime.strptime(ref_date, "%Y-%m-%d")
    target = ref - timedelta(days=months_back * 30)
    target_str = target.strftime("%Y-%m-%d")
    best = None
    best_dist = float("inf")
    for obs in series:
        dist = abs((datetime.strptime(obs["date"], "%Y-%m-%d") - target).days)
        if dist < best_dist:
            best_dist = dist
            best = obs["value"]
    if best_dist <= 20:
        return best
    return None
