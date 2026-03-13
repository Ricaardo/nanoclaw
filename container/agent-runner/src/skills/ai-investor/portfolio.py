"""
AI Investor - Portfolio Management Module
持仓管理模块
"""

import json
import os
from typing import List, Dict, Any, Optional
from datetime import datetime

# 默认持仓数据文件路径
PORTFOLIO_FILE = os.environ.get('PORTFOLIO_FILE', '/workspace/financial-data/portfolio.json')

# 默认模拟持仓
DEFAULT_PORTFOLIO = {
    "holdings": [
        {"symbol": "gold_usd", "quantity": 10, "avg_price": 4800, "current_price": 5175},
        {"symbol": "btc_usd", "quantity": 0.5, "avg_price": 65000, "current_price": 71600},
        {"symbol": "sp500", "quantity": 100, "avg_price": 5800, "current_price": 6816},
    ],
    "cash": 0,
    "last_updated": None
}


def load_portfolio() -> Dict[str, Any]:
    """加载持仓数据"""
    try:
        if os.path.exists(PORTFOLIO_FILE):
            with open(PORTFOLIO_FILE, 'r') as f:
                return json.load(f)
    except Exception:
        pass
    return DEFAULT_PORTFOLIO.copy()


def save_portfolio(portfolio: Dict[str, Any]) -> None:
    """保存持仓数据"""
    os.makedirs(os.path.dirname(PORTFOLIO_FILE), exist_ok=True)
    portfolio['last_updated'] = datetime.now().isoformat()
    with open(PORTFOLIO_FILE, 'w') as f:
        json.dump(portfolio, f, indent=2, ensure_ascii=False)


def get_portfolio() -> Dict[str, Any]:
    """获取完整持仓信息"""
    portfolio = load_portfolio()
    holdings = portfolio.get('holdings', [])

    results = []
    total_value = 0
    total_cost = 0

    for h in holdings:
        current_value = h['quantity'] * h['current_price']
        cost_basis = h['quantity'] * h['avg_price']
        profit = current_value - cost_basis
        profit_percent = ((h['current_price'] - h['avg_price']) / h['avg_price']) * 100

        results.append({
            "symbol": h['symbol'],
            "quantity": h['quantity'],
            "avg_price": h['avg_price'],
            "current_price": h['current_price'],
            "current_value": round(current_value, 2),
            "cost_basis": round(cost_basis, 2),
            "profit": round(profit, 2),
            "profit_percent": f"{profit_percent:.2f}%"
        })

        total_value += current_value
        total_cost += cost_basis

    total_profit = total_value - total_cost
    total_profit_percent = ((total_value - total_cost) / total_cost * 100) if total_cost > 0 else 0

    return {
        "holdings": results,
        "cash": portfolio.get('cash', 0),
        "summary": {
            "total_value": round(total_value, 2),
            "total_cost": round(total_cost, 2),
            "total_profit": round(total_profit, 2),
            "total_profit_percent": f"{total_profit_percent:.2f}%",
            "positions_count": len(holdings)
        },
        "last_updated": portfolio.get('last_updated')
    }


def add_position(symbol: str, quantity: float, price: float, portfolio: Optional[Dict] = None) -> Dict[str, Any]:
    """添加或更新持仓"""
    if portfolio is None:
        portfolio = load_portfolio()

    holdings = portfolio.get('holdings', [])

    # 检查是否已存在持仓
    existing = None
    for h in holdings:
        if h['symbol'] == symbol:
            existing = h
            break

    if existing:
        # 计算新的平均价格
        total_quantity = existing['quantity'] + quantity
        total_cost = (existing['quantity'] * existing['avg_price']) + (quantity * price)
        existing['avg_price'] = total_cost / total_quantity
        existing['quantity'] = total_quantity
    else:
        holdings.append({
            "symbol": symbol,
            "quantity": quantity,
            "avg_price": price,
            "current_price": price
        })

    portfolio['holdings'] = holdings
    save_portfolio(portfolio)

    return {
        "success": True,
        "message": f"Added {quantity} {symbol} at ${price}",
        "action": "buy",
        "symbol": symbol,
        "quantity": quantity,
        "price": price
    }


def remove_position(symbol: str, quantity: float, price: float, portfolio: Optional[Dict] = None) -> Dict[str, Any]:
    """减少持仓"""
    if portfolio is None:
        portfolio = load_portfolio()

    holdings = portfolio.get('holdings', [])

    for h in holdings:
        if h['symbol'] == symbol:
            if h['quantity'] < quantity:
                return {
                    "success": False,
                    "error": f"Not enough {symbol} holdings. Have {h['quantity']}, trying to sell {quantity}"
                }

            h['quantity'] -= quantity

            # 如果全部卖出，移除持仓
            if h['quantity'] <= 0:
                holdings.remove(h)

            portfolio['holdings'] = holdings
            save_portfolio(portfolio)

            return {
                "success": True,
                "message": f"Sold {quantity} {symbol} at ${price}",
                "action": "sell",
                "symbol": symbol,
                "quantity": quantity,
                "price": price
            }

    return {
        "success": False,
        "error": f"No position found for {symbol}"
    }


def update_prices(prices: Dict[str, float]) -> Dict[str, Any]:
    """批量更新当前价格"""
    portfolio = load_portfolio()
    holdings = portfolio.get('holdings', [])

    updated = []
    for h in holdings:
        if h['symbol'] in prices:
            h['current_price'] = prices[h['symbol']]
            updated.append(h['symbol'])

    portfolio['holdings'] = holdings
    save_portfolio(portfolio)

    return {
        "success": True,
        "updated": updated,
        "holdings": holdings
    }


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python portfolio.py <command> [args]")
        print("Commands:")
        print("  get                    - Get portfolio")
        print("  add <symbol> <qty> <price>")
        print("  remove <symbol> <qty> <price>")
        sys.exit(1)

    cmd = sys.argv[1]

    if cmd == "get":
        print(json.dumps(get_portfolio(), indent=2, ensure_ascii=False))
    elif cmd == "add" and len(sys.argv) == 5:
        result = add_position(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    elif cmd == "remove" and len(sys.argv) == 5:
        result = remove_position(sys.argv[2], float(sys.argv[3]), float(sys.argv[4]))
        print(json.dumps(result, indent=2, ensure_ascii=False))
    else:
        print("Invalid command")
        sys.exit(1)
