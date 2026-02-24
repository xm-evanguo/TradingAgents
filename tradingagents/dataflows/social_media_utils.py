"""
Social Media Utilities for TradingAgents

Fetches social media sentiment using Grok API for X/Twitter analysis.
Grok has native access to real-time X/Twitter data, making it ideal
for social media sentiment analysis.

Requires XAI_API_KEY environment variable to be set.
"""

import json
import os
from datetime import datetime
from typing import Union

import requests
from dateutil.relativedelta import relativedelta

# Import prompt manager for template rendering
from tradingagents.prompts import get_social_media_prompt


class SocialMediaUtils:
    """
    Utility class for fetching social media sentiment using Grok API.
    
    Uses Grok's native X/Twitter access for real-time sentiment analysis.
    """
    
    def __init__(self):
        self.grok_api_key = os.getenv('XAI_API_KEY')
        self.grok_base_url = "https://api.x.ai/v1"
        
        if not self.grok_api_key:
            print("Warning: XAI_API_KEY environment variable not found. Social media analysis will be disabled.")
    
    def get_x_twitter_sentiment(self, ticker: str, curr_date: str) -> Union[dict, str]:
        """
        Fetch X/Twitter sentiment using Grok API.
        
        Args:
            ticker: Stock ticker symbol
            curr_date: Current date in yyyy-mm-dd format
            
        Returns:
            Structured dict with analysis data, or string with error/fallback
        """
        if not self.grok_api_key:
            return f"## {ticker} X/Twitter Analysis Error:\n\nGrok API key not configured (set XAI_API_KEY)"
            
        try:
            # Calculate 7 days before current date
            curr_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
            before_date_obj = curr_date_obj - relativedelta(days=7)
            before_date = before_date_obj.strftime("%Y-%m-%d")
            
            # Generate prompt using template system
            prompt = get_social_media_prompt(
                'x_twitter_analysis',
                ticker,
                before_date,
                curr_date
            )
            
            # Make API call to Grok
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {
                        "role": "system",
                        "content": get_social_media_prompt(
                            'system_prompt', ticker, before_date, curr_date,
                            platform="X/Twitter"
                        )
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "model": "grok-4-1-fast-non-reasoning",
                "stream": False,
                "temperature": 0.2,
                "max_tokens": 2000
            }
            
            response = requests.post(
                f"{self.grok_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Try to parse JSON response for structured data
                try:
                    json_content = json.loads(content)
                    return {
                        "platform": "X/Twitter",
                        "data_type": "structured_json",
                        "analysis": json_content
                    }
                except json.JSONDecodeError:
                    # Fallback to text format if not valid JSON
                    return f"### X/Twitter Analysis (via Grok):\n\n{content}\n"
            else:
                error_msg = f"Grok API error {response.status_code}: {response.text}"
                return f"### X/Twitter Analysis Error:\n\n{error_msg}\n"
                
        except Exception as e:
            error_msg = f"Error in Grok X/Twitter analysis: {str(e)}"
            return f"### X/Twitter Analysis Error:\n\n{error_msg}\n"
    
    def get_social_media_analysis(self, ticker: str, curr_date: str) -> str:
        """
        Get social media analysis for a stock ticker.
        
        This is the main entry point used by the vendor routing system.
        Returns a formatted string suitable for LLM consumption.
        
        Args:
            ticker: Stock ticker symbol
            curr_date: Current date in yyyy-mm-dd format
            
        Returns:
            Formatted string with social media analysis
        """
        curr_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
        before_date_obj = curr_date_obj - relativedelta(days=7)
        before_date = before_date_obj.strftime("%Y-%m-%d")
        
        # Get analysis from X/Twitter via Grok
        twitter_analysis = self.get_x_twitter_sentiment(ticker, curr_date)
        
        # Format the result
        if isinstance(twitter_analysis, dict) and twitter_analysis.get("data_type") == "structured_json":
            # Return structured JSON as formatted string for the LLM agent to process
            return json.dumps({
                "data_type": "social_media_analysis",
                "symbol": ticker,
                "analysis_period": f"{before_date} to {curr_date}",
                "twitter": twitter_analysis["analysis"],
                "source": "Grok AI with real-time X/Twitter access"
            }, indent=2)
        elif isinstance(twitter_analysis, str):
            return f"""## {ticker} Social Media Analysis from {before_date} to {curr_date}:

{twitter_analysis}

---
*Analysis generated using Grok AI with real-time X/Twitter access*
"""
        else:
            return str(twitter_analysis)


def get_social_media_sentiment(ticker: str, curr_date: str) -> str:
    """
    Standalone function to get social media sentiment using Grok for X/Twitter.
    
    This function is registered as a vendor implementation in the dataflows
    interface routing system.
    
    Args:
        ticker: Stock ticker symbol
        curr_date: Current date in yyyy-mm-dd format
        
    Returns:
        str: Social media analysis and sentiment report
    """
    try:
        social_media_utils = SocialMediaUtils()
        return social_media_utils.get_social_media_analysis(ticker, curr_date)
    except Exception as e:
        error_msg = f"Failed to initialize social media utilities: {str(e)}"
        print(error_msg)
        return f"## {ticker} Social Media Analysis Error:\n\n{error_msg}"
