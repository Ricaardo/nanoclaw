"""
AKShare 统一数据客户端 - 多市场数据获取

支持市场: A 股、港股、加密货币、贵金属/商品
Fallback: AKShare 不可用时自动回退 yfinance（美股/港股）

依赖: akshare, pandas
可选依赖: yfinance (fallback)

用法:
    from akshare_client import AKShareClient
    client = AKShareClient()
    df = client.get_stock_price("600519.SH", period="daily", count=250)
    fin = client.get_financials("600519.SH")
"""

import logging
from datetime import datetime, timedelta
from typing import Optional

import pandas as pd

logger = logging.getLogger(__name__)

try:
    import akshare as ak
    HAS_AKSHARE = True
except ImportError:
    HAS_AKSHARE = False
    logger.warning("akshare 未安装，A 股/港股数据功能不可用。pip install akshare")

try:
    import yfinance as yf
    HAS_YFINANCE = True
except ImportError:
    HAS_YFINANCE = False


class AKShareClient:
    """AKShare 统一数据客户端"""

    def __init__(self):
        if not HAS_AKSHARE:
            logger.warning("AKShare 未安装，仅 yfinance fallback 可用")

    # ==================== 股票行情 ====================

    def get_stock_price(
        self,
        ticker: str,
        period: str = "daily",
        count: int = 250,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> pd.DataFrame:
        """
        获取股票价格数据

        Args:
            ticker: 股票代码 (如 600519.SH, 00700.HK, AAPL)
            period: daily / weekly / monthly
            count: 返回数据条数（未指定 start_date 时使用）
            start_date: 起始日期 YYYYMMDD
            end_date: 结束日期 YYYYMMDD

        Returns:
            DataFrame with columns: date, open, high, low, close, volume
        """
        from market_router import detect_market
        market = detect_market(ticker)

        if end_date is None:
            end_date = datetime.now().strftime("%Y%m%d")
        if start_date is None:
            days = {"daily": count * 2, "weekly": count * 10, "monthly": count * 35}
            delta = days.get(period, count * 2)
            start_date = (datetime.now() - timedelta(days=delta)).strftime("%Y%m%d")

        if market == "A_SHARE":
            return self._get_a_share_price(ticker, period, start_date, end_date, count)
        elif market == "HK":
            return self._get_hk_price(ticker, period, start_date, end_date, count)
        elif market == "CRYPTO":
            return self._get_crypto_price(ticker, period, count)
        elif market == "COMMODITY":
            return self._get_commodity_price(ticker, period, start_date, end_date, count)
        else:
            return self._get_us_price_fallback(ticker, period, start_date, end_date, count)

    def _get_a_share_price(self, ticker, period, start_date, end_date, count):
        """A 股行情 - 通过 AKShare"""
        if not HAS_AKSHARE:
            raise RuntimeError("获取 A 股数据需要安装 akshare: pip install akshare")

        symbol = ticker.split(".")[0]
        period_map = {"daily": "daily", "weekly": "weekly", "monthly": "monthly"}
        ak_period = period_map.get(period, "daily")

        try:
            df = ak.stock_zh_a_hist(
                symbol=symbol,
                period=ak_period,
                start_date=start_date,
                end_date=end_date,
                adjust="qfq",  # 前复权
            )
            df = df.rename(columns={
                "日期": "date", "开盘": "open", "最高": "high",
                "最低": "low", "收盘": "close", "成交量": "volume",
                "成交额": "amount", "振幅": "amplitude",
                "涨跌幅": "pct_change", "涨跌额": "change",
                "换手率": "turnover",
            })
            df["date"] = pd.to_datetime(df["date"])
            return df.tail(count).reset_index(drop=True)
        except Exception as e:
            logger.error(f"AKShare A 股行情获取失败: {e}")
            raise

    def _get_hk_price(self, ticker, period, start_date, end_date, count):
        """港股行情 - AKShare 优先，yfinance fallback"""
        if HAS_AKSHARE:
            try:
                symbol = ticker.replace(".HK", "")
                df = ak.stock_hk_hist(
                    symbol=symbol,
                    period="daily",
                    start_date=start_date,
                    end_date=end_date,
                    adjust="qfq",
                )
                df = df.rename(columns={
                    "日期": "date", "开盘": "open", "最高": "high",
                    "最低": "low", "收盘": "close", "成交量": "volume",
                })
                df["date"] = pd.to_datetime(df["date"])
                return df.tail(count).reset_index(drop=True)
            except Exception as e:
                logger.warning(f"AKShare 港股获取失败，尝试 yfinance: {e}")

        return self._get_us_price_fallback(ticker, period, start_date, end_date, count)

    def _get_crypto_price(self, ticker, period, count):
        """加密货币行情"""
        if HAS_AKSHARE:
            try:
                symbol = ticker.split("-")[0].split("/")[0].upper()
                df = ak.crypto_hist(symbol=symbol, period="daily")
                df = df.rename(columns={
                    "Date": "date", "Open": "open", "High": "high",
                    "Low": "low", "Close": "close", "Volume": "volume",
                })
                df["date"] = pd.to_datetime(df["date"])
                return df.tail(count).reset_index(drop=True)
            except Exception as e:
                logger.warning(f"AKShare 加密货币获取失败: {e}")

        if HAS_YFINANCE:
            symbol = ticker.split("-")[0].split("/")[0].upper()
            yf_ticker = f"{symbol}-USD"
            data = yf.download(yf_ticker, period=f"{count}d", progress=False)
            if not data.empty:
                data = data.reset_index()
                data.columns = ["date", "open", "high", "low", "close", "adj_close", "volume"]
                return data[["date", "open", "high", "low", "close", "volume"]].tail(count)

        raise RuntimeError(f"无法获取 {ticker} 加密货币数据")

    def _get_commodity_price(self, ticker, period, start_date, end_date, count):
        """贵金属/商品/能源行情"""
        base = ticker.split(".")[0].upper()

        # 商品分类映射
        commodity_map = {
            # 贵金属
            "XAU": ("Au99.99", "precious"), "GLD": ("Au99.99", "precious"), "GC": ("Au99.99", "precious"),
            "XAG": ("Ag99.99", "precious"), "SLV": ("Ag99.99", "precious"), "SI": ("Ag99.99", "precious"),
            # 能源商品
            "CL": ("WTI", "energy"), "WTI": ("WTI", "energy"),
            "BRENT": ("Brent", "energy"), "BZ": ("Brent", "energy"),
            "NG": ("天然气", "energy"),
        }

        category = commodity_map.get(base, (None, None))
        commodity_type = category[1] if category[0] else None

        # 贵金属 — AKShare 现货
        if commodity_type == "precious" and HAS_AKSHARE:
            try:
                sge_symbol = category[0]
                df = ak.spot_hist_sge(symbol=sge_symbol)
                if not df.empty:
                    df = df.rename(columns={
                        "日期": "date", "开盘价": "open", "最高价": "high",
                        "最低价": "low", "收盘价": "close",
                    })
                    df["date"] = pd.to_datetime(df["date"])
                    df["volume"] = 0
                    return df.tail(count).reset_index(drop=True)
            except Exception as e:
                logger.warning(f"AKShare 贵金属数据获取失败: {e}")

        # 能源商品 — 尝试 AKShare 国际期货，fallback yfinance
        if commodity_type == "energy":
            return self._get_energy_price(base, count)

        return self._get_us_price_fallback(ticker, period, start_date, end_date, count)

    def _get_energy_price(self, base, count):
        """能源商品行情 — AKShare 国际期货 → yfinance fallback"""
        # 尝试 AKShare 国际期货
        if HAS_AKSHARE:
            try:
                ak_energy_map = {
                    "CL": "WTI", "WTI": "WTI",
                    "BRENT": "Brent", "BZ": "Brent",
                    "NG": "天然气",
                }
                ak_symbol = ak_energy_map.get(base)
                if ak_symbol:
                    df = ak.futures_foreign_hist(symbol=ak_symbol)
                    if df is not None and not df.empty:
                        df = df.rename(columns={
                            "日期": "date", "开盘价": "open", "最高价": "high",
                            "最低价": "low", "收盘价": "close", "成交量": "volume",
                        })
                        # 兼容不同列名格式
                        for en, zh in [("date", "Date"), ("open", "Open"), ("high", "High"),
                                       ("low", "Low"), ("close", "Close"), ("volume", "Volume")]:
                            if zh in df.columns and en not in df.columns:
                                df = df.rename(columns={zh: en})
                        df["date"] = pd.to_datetime(df["date"])
                        if "volume" not in df.columns:
                            df["volume"] = 0
                        return df[["date", "open", "high", "low", "close", "volume"]].tail(count).reset_index(drop=True)
            except Exception as e:
                logger.warning(f"AKShare 能源期货获取失败，尝试 yfinance: {e}")

        # yfinance fallback
        if HAS_YFINANCE:
            yf_map = {
                "CL": "CL=F", "WTI": "CL=F",
                "BRENT": "BZ=F", "BZ": "BZ=F",
                "NG": "NG=F",
            }
            yf_symbol = yf_map.get(base)
            if yf_symbol:
                try:
                    data = yf.download(yf_symbol, period="1y", progress=False)
                    if not data.empty:
                        data = data.reset_index()
                        if isinstance(data.columns, pd.MultiIndex):
                            data.columns = [c[0].lower() for c in data.columns]
                        else:
                            data.columns = [c.lower() for c in data.columns]
                        return data[["date", "open", "high", "low", "close", "volume"]].tail(count).reset_index(drop=True)
                except Exception as e:
                    logger.error(f"yfinance 能源数据获取失败: {e}")

        raise RuntimeError(f"无法获取能源商品 {base} 数据")

    def _get_us_price_fallback(self, ticker, period, start_date, end_date, count):
        """美股/fallback - 使用 yfinance"""
        if not HAS_YFINANCE:
            raise RuntimeError("获取美股数据需要安装 yfinance: pip install yfinance")
        try:
            data = yf.download(
                ticker.replace(".HK", ""),
                start=f"{start_date[:4]}-{start_date[4:6]}-{start_date[6:]}",
                end=f"{end_date[:4]}-{end_date[4:6]}-{end_date[6:]}",
                progress=False,
            )
            if data.empty:
                raise RuntimeError(f"yfinance 未返回 {ticker} 数据")
            data = data.reset_index()
            # Handle both single and multi-level column names
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = [c[0].lower() for c in data.columns]
            else:
                data.columns = [c.lower() for c in data.columns]
            return data[["date", "open", "high", "low", "close", "volume"]].tail(count).reset_index(drop=True)
        except Exception as e:
            logger.error(f"yfinance 获取失败: {e}")
            raise

    # ==================== 财务数据 ====================

    def get_financials(self, ticker: str) -> dict:
        """
        获取财务报表数据

        Returns:
            dict: {
                "income": DataFrame (利润表),
                "balance": DataFrame (资产负债表),
                "cashflow": DataFrame (现金流量表),
                "source": str
            }
        """
        from market_router import detect_market
        market = detect_market(ticker)

        if market == "A_SHARE" and HAS_AKSHARE:
            return self._get_a_share_financials(ticker)
        elif HAS_YFINANCE:
            return self._get_yfinance_financials(ticker)
        else:
            raise RuntimeError(f"无法获取 {ticker} 财务数据")

    def _get_a_share_financials(self, ticker):
        """A 股财务报表 - AKShare"""
        symbol = ticker.split(".")[0]
        result = {}
        try:
            result["income"] = ak.stock_financial_report_sina(stock=symbol, symbol="利润表")
            result["balance"] = ak.stock_financial_report_sina(stock=symbol, symbol="资产负债表")
            result["cashflow"] = ak.stock_financial_report_sina(stock=symbol, symbol="现金流量表")
            result["source"] = "akshare_sina"
        except Exception as e:
            logger.error(f"A 股财务数据获取失败: {e}")
            raise
        return result

    def _get_yfinance_financials(self, ticker):
        """美股/港股财务数据 - yfinance"""
        stock = yf.Ticker(ticker)
        return {
            "income": stock.financials.T if stock.financials is not None else pd.DataFrame(),
            "balance": stock.balance_sheet.T if stock.balance_sheet is not None else pd.DataFrame(),
            "cashflow": stock.cashflow.T if stock.cashflow is not None else pd.DataFrame(),
            "source": "yfinance",
        }

    # ==================== 指数数据 ====================

    def get_index_data(self, index_code: str, count: int = 250) -> pd.DataFrame:
        """
        获取指数数据

        Args:
            index_code: 指数代码 (如 000001.SH 上证指数, SPX, HSI)
            count: 数据条数
        """
        if HAS_AKSHARE:
            try:
                if ".SH" in index_code or ".SZ" in index_code:
                    symbol = index_code.split(".")[0]
                    df = ak.stock_zh_index_daily(symbol=f"sh{symbol}" if ".SH" in index_code else f"sz{symbol}")
                    df = df.rename(columns={"date": "date", "open": "open", "high": "high", "low": "low", "close": "close", "volume": "volume"})
                    df["date"] = pd.to_datetime(df["date"])
                    return df.tail(count).reset_index(drop=True)
            except Exception as e:
                logger.warning(f"AKShare 指数数据获取失败: {e}")

        if HAS_YFINANCE:
            index_map = {"000001.SH": "000001.SS", "399001.SZ": "399001.SZ", "HSI": "^HSI", "SPX": "^GSPC"}
            yf_symbol = index_map.get(index_code, index_code)
            data = yf.download(yf_symbol, period="1y", progress=False)
            if not data.empty:
                data = data.reset_index()
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = [c[0].lower() for c in data.columns]
                else:
                    data.columns = [c.lower() for c in data.columns]
                return data[["date", "open", "high", "low", "close", "volume"]].tail(count).reset_index(drop=True)

        raise RuntimeError(f"无法获取指数 {index_code} 数据")

    # ==================== 宏观数据 ====================

    def get_macro_data(self, indicator: str) -> pd.DataFrame:
        """
        获取中国宏观经济数据

        Args:
            indicator: cpi / ppi / pmi / gdp / m2 / shibor
        """
        if not HAS_AKSHARE:
            raise RuntimeError("宏观数据需要安装 akshare")

        indicator_map = {
            "cpi": lambda: ak.macro_china_cpi(),
            "ppi": lambda: ak.macro_china_ppi(),
            "pmi": lambda: ak.macro_china_pmi(),
            "gdp": lambda: ak.macro_china_gdp(),
            "m2": lambda: ak.macro_china_money_supply(),
            "shibor": lambda: ak.rate_interbank(market="上海银行间同业拆放利率(Shibor)", indicator="3月", need_page=""),
        }

        func = indicator_map.get(indicator.lower())
        if func is None:
            raise ValueError(f"不支持的宏观指标: {indicator}，可选: {list(indicator_map.keys())}")

        try:
            return func()
        except Exception as e:
            logger.error(f"宏观数据 {indicator} 获取失败: {e}")
            raise

    # ==================== A 股特色数据 ====================

    def get_north_flow(self, count: int = 30) -> pd.DataFrame:
        """获取北向资金流向数据"""
        if not HAS_AKSHARE:
            raise RuntimeError("需要安装 akshare")
        try:
            df = ak.stock_hsgt_north_net_flow_in_em(symbol="北上")
            return df.tail(count).reset_index(drop=True)
        except Exception as e:
            logger.error(f"北向资金数据获取失败: {e}")
            raise

    def get_sector_data(self, sector_type: str = "industry") -> pd.DataFrame:
        """
        获取行业/概念板块数据

        Args:
            sector_type: industry (申万行业) / concept (概念板块)
        """
        if not HAS_AKSHARE:
            raise RuntimeError("需要安装 akshare")
        try:
            if sector_type == "industry":
                return ak.stock_board_industry_name_em()
            elif sector_type == "concept":
                return ak.stock_board_concept_name_em()
            else:
                raise ValueError(f"不支持的板块类型: {sector_type}")
        except Exception as e:
            logger.error(f"板块数据获取失败: {e}")
            raise

    def get_dragon_tiger(self, date: Optional[str] = None) -> pd.DataFrame:
        """获取龙虎榜数据"""
        if not HAS_AKSHARE:
            raise RuntimeError("需要安装 akshare")
        try:
            if date is None:
                date = datetime.now().strftime("%Y%m%d")
            return ak.stock_lhb_detail_em(start_date=date, end_date=date)
        except Exception as e:
            logger.error(f"龙虎榜数据获取失败: {e}")
            raise

    def get_block_trade(self, count: int = 30) -> pd.DataFrame:
        """获取大宗交易数据"""
        if not HAS_AKSHARE:
            raise RuntimeError("需要安装 akshare")
        try:
            return ak.stock_dzjy_summary_em().head(count)
        except Exception as e:
            logger.error(f"大宗交易数据获取失败: {e}")
            raise
