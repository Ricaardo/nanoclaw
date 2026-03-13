"""
AI Investor Skill for NanoClaw
AI 投资分析助手 - 模拟巴菲特、索罗斯、芒格、达利欧等大师的投资风格
"""

__version__ = "1.0.0"
__author__ = "NanoClaw"

# 导出主要函数
from .get_market_data import get_market_data, TRADING_PAIRS as MARKET_SYMBOLS
from .get_indicators import get_indicators

__all__ = [
    'get_market_data',
    'get_indicators',
    'MARKET_SYMBOLS',
]
