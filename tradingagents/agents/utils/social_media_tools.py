from langchain_core.tools import tool
from typing import Annotated
from tradingagents.dataflows.interface import route_to_vendor

@tool
def get_social_media_sentiment(
    ticker: Annotated[str, "Ticker symbol"],
    curr_date: Annotated[str, "Current date in yyyy-mm-dd format"],
) -> str:
    """
    Retrieve social media sentiment analysis for a given ticker symbol.
    Uses Grok AI to analyze X/Twitter discussions and sentiment in real-time.
    Args:
        ticker (str): Ticker symbol
        curr_date (str): Current date in yyyy-mm-dd format
    Returns:
        str: A formatted string containing social media sentiment analysis
    """
    return route_to_vendor("get_social_media_sentiment", ticker, curr_date)
