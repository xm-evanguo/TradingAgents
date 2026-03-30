from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor
from tradingagents.dataflows.composite_signals import get_composite_signals as _compute_composite_signals

@tool
def get_indicators(
    symbol: Annotated[str, "ticker symbol of the company"],
    indicator: Annotated[str, "technical indicator to get the analysis and report of"],
    curr_date: Annotated[str, "The current trading date you are trading on, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 30,
) -> str:
    """
    Retrieve technical indicators for a given ticker symbol.
    Uses the configured technical_indicators vendor.
    Args:
        symbol (str): Ticker symbol of the company, e.g. AAPL, TSM
        indicator (str): Technical indicator to get the analysis and report of
        curr_date (str): The current trading date you are trading on, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 30
    Returns:
        str: A formatted dataframe containing the technical indicators for the specified ticker symbol and indicator.
    """
    return route_to_vendor("get_indicators", symbol, indicator, curr_date, look_back_days)


@tool
def get_composite_signals(
    symbol: Annotated[str, "ticker symbol of the company"],
    curr_date: Annotated[str, "The current trading date, YYYY-mm-dd"],
    look_back_days: Annotated[int, "how many days to look back"] = 60,
) -> str:
    """
    Compute pre-built composite trading signals from raw OHLCV data.
    Returns a structured report with:
    - Golden/Death Cross status (50 SMA vs 200 SMA)
    - Bollinger Band Width squeeze detection
    - Volume surge detection (current vs 20-day average)
    - RSI-Price divergence detection
    - Multi-timeframe trend alignment (price vs 10 EMA, 20/50/200 SMA)

    Call this FIRST before individual indicators to get a quick market regime overview.

    Args:
        symbol (str): Ticker symbol of the company
        curr_date (str): The current trading date, YYYY-mm-dd
        look_back_days (int): How many days to look back, default is 60
    Returns:
        str: A structured report containing composite trading signals
    """
    return _compute_composite_signals(symbol, curr_date, look_back_days)