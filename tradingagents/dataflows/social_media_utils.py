import os
import requests
from typing import Annotated
from datetime import datetime
from dateutil.relativedelta import relativedelta


class SocialMediaUtils:
    """
    Utility class for fetching social media news using Grok API (X/Twitter) and Perplexity API (Reddit)
    
    Note: Perplexity Reddit analysis is currently disabled in production.
    To enable it, set self.enable_perplexity = True in __init__
    """
    
    def __init__(self):
        self.grok_api_key = os.getenv('XAI_API_KEY')  # Grok API key for X/Twitter
        self.perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')  # Perplexity API key for Reddit (currently disabled)
        self.grok_base_url = "https://api.x.ai/v1"
        self.perplexity_base_url = "https://api.perplexity.ai"
        
        # Production configuration
        self.enable_perplexity = False  # Disabled in production
        
        if not self.grok_api_key:
            print("Warning: XAI_API_KEY environment variable not found. X/Twitter analysis will be disabled.")
        
        if not self.perplexity_api_key and self.enable_perplexity:
            print("Warning: PERPLEXITY_API_KEY environment variable not found. Reddit analysis will be disabled.")
        
        if not self.enable_perplexity:
            print("Info: Perplexity Reddit analysis is currently disabled in production.")
    
    def get_x_twitter_sentiment(self, ticker: str, curr_date: str) -> str:
        """
        Fetch X/Twitter sentiment using Grok
        """
        if not self.grok_api_key:
            return f"## {ticker} X/Twitter Analysis Error:\n\nGrok API key not configured"
            
        try:
            # Calculate 7 days before current date
            curr_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
            before_date_obj = curr_date_obj - relativedelta(days=7)
            before_date = before_date_obj.strftime("%Y-%m-%d")
            
            # Prepare the prompt for Grok
            prompt = f"""
            Search and analyze X/Twitter sentiment and discussions about {ticker} stock from {before_date} to {curr_date}.
            
            Please provide:
            1. Recent tweets and discussions about {ticker} on X/Twitter
            2. Overall sentiment analysis (bullish, bearish, neutral) from X/Twitter
            3. Key themes and topics being discussed on X/Twitter
            4. Notable influencer opinions or viral tweets about {ticker}
            5. Engagement metrics and trending patterns on X/Twitter
            6. Any trending hashtags related to {ticker} on X/Twitter
            
            Focus specifically on X/Twitter platform discussions about {ticker}.
            
            Format the response as a comprehensive report with clear sections and bullet points.
            Include specific examples of tweets or discussions when possible.
            """
            
            # Make API call to Grok
            headers = {
                "Authorization": f"Bearer {self.grok_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial social media analyst with access to real-time X/Twitter data. Provide comprehensive analysis of X/Twitter sentiment and discussions about stocks."
                    },
                    {
                        "role": "user", 
                        "content": prompt
                    }
                ],
                "model": "grok-beta",
                "stream": False,
                "temperature": 0.7,
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
                return f"### X/Twitter Analysis (via Grok):\n\n{content}\n"
            else:
                error_msg = f"Grok API error {response.status_code}: {response.text}"
                return f"### X/Twitter Analysis Error:\n\n{error_msg}\n"
                
        except Exception as e:
            error_msg = f"Error in Grok X/Twitter analysis: {str(e)}"
            return f"### X/Twitter Analysis Error:\n\n{error_msg}\n"
    
    def get_reddit_sentiment(self, ticker: str, curr_date: str) -> str:
        """
        Fetch Reddit sentiment using Perplexity (currently disabled in production)
        """
        if not self.enable_perplexity:
            return f"### Reddit Analysis (via Perplexity):\n\n*Reddit analysis via Perplexity is currently disabled in production.*\n"
            
        if not self.perplexity_api_key:
            return f"## {ticker} Reddit Analysis Error:\n\nPerplexity API key not configured"
            
        try:
            # Calculate 7 days before current date
            curr_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
            before_date_obj = curr_date_obj - relativedelta(days=7)
            before_date = before_date_obj.strftime("%Y-%m-%d")
            
            # Prepare the prompt for Perplexity
            prompt = f"""
            Search and analyze Reddit discussions and sentiment about {ticker} stock from {before_date} to {curr_date}.
            
            Please focus on Reddit and provide:
            1. Recent Reddit posts and discussions about {ticker} from relevant subreddits (r/stocks, r/investing, r/wallstreetbets, etc.)
            2. Overall sentiment analysis (bullish, bearish, neutral) from Reddit communities
            3. Key themes, DD (due diligence), and discussions trending on Reddit about {ticker}
            4. Notable Reddit posts or comments that gained significant upvotes/attention
            5. Community consensus and contrarian viewpoints on Reddit
            6. Any memes, trends, or Reddit-specific discussions about {ticker}
            
            Focus specifically on Reddit platform discussions about {ticker}.
            
            Format the response as a comprehensive report with clear sections and bullet points.
            Include specific examples of Reddit posts or discussions when possible.
            """
            
            # Make API call to Perplexity
            headers = {
                "Authorization": f"Bearer {self.perplexity_api_key}",
                "Content-Type": "application/json"
            }
            
            data = {
                "model": "llama-3.1-sonar-small-128k-online",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are a financial social media analyst with access to real-time Reddit data. Provide comprehensive analysis of Reddit sentiment and discussions about stocks."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": 2000,
                "temperature": 0.7,
                "top_p": 0.9,
                "return_citations": True,
                "search_domain_filter": ["reddit.com"],
                "return_images": False,
                "return_related_questions": False,
                "search_recency_filter": "week"
            }
            
            response = requests.post(
                f"{self.perplexity_base_url}/chat/completions",
                headers=headers,
                json=data,
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result['choices'][0]['message']['content']
                
                # Add citations if available
                citations_text = ""
                if 'citations' in result and result['citations']:
                    citations_text = "\n\n**Sources:**\n"
                    for i, citation in enumerate(result['citations'][:5], 1):
                        citations_text += f"{i}. {citation}\n"
                
                return f"### Reddit Analysis (via Perplexity):\n\n{content}{citations_text}\n"
            else:
                error_msg = f"Perplexity API error {response.status_code}: {response.text}"
                return f"### Reddit Analysis Error:\n\n{error_msg}\n"
                
        except Exception as e:
            error_msg = f"Error in Perplexity Reddit analysis: {str(e)}"
            return f"### Reddit Analysis Error:\n\n{error_msg}\n"
    
    def get_combined_social_media_analysis(self, ticker: str, curr_date: str) -> str:
        """
        Get combined social media analysis from both X/Twitter (Grok) and Reddit (Perplexity)
        Note: Perplexity is currently disabled in production
        """
        curr_date_obj = datetime.strptime(curr_date, "%Y-%m-%d")
        before_date_obj = curr_date_obj - relativedelta(days=7)
        before_date = before_date_obj.strftime("%Y-%m-%d")
        
        # Get analysis from X/Twitter via Grok
        twitter_analysis = self.get_x_twitter_sentiment(ticker, curr_date)
        
        # Perplexity Reddit analysis is disabled in production for now
        # reddit_analysis = self.get_reddit_sentiment(ticker, curr_date)
        reddit_analysis = "### Reddit Analysis (via Perplexity):\n\n*Reddit analysis via Perplexity is currently disabled in production.*\n"
        
        # Combine the results
        combined_analysis = f"""## {ticker} Social Media Analysis from {before_date} to {curr_date}:

{twitter_analysis}

{reddit_analysis}

### Summary:
This analysis provides real-time social media sentiment from X/Twitter (via Grok AI). Reddit analysis via Perplexity is currently disabled in production but can be enabled by updating the social_media_utils configuration.

---
*Analysis generated using Grok AI (X/Twitter) with real-time social media access*
"""
        
        return combined_analysis


def get_stock_news(ticker: str, curr_date: str) -> str:
    """
    Standalone function to get social media stock news using Grok (X/Twitter)
    
    Note: Perplexity Reddit analysis is currently disabled in production.
    
    Args:
        ticker (str): Stock ticker symbol
        curr_date (str): Current date in yyyy-mm-dd format
        
    Returns:
        str: Social media analysis and sentiment report from X/Twitter (Reddit disabled in production)
    """
    try:
        social_media_utils = SocialMediaUtils()
        return social_media_utils.get_combined_social_media_analysis(ticker, curr_date)
    except Exception as e:
        error_msg = f"Failed to initialize social media utilities: {str(e)}"
        print(error_msg)
        return f"## {ticker} Social Media Analysis Error:\n\n{error_msg}"


# Backward compatibility functions
def get_stock_news_grok(ticker: str, curr_date: str) -> str:
    """
    Backward compatibility function - now calls the combined analysis
    """
    return get_stock_news(ticker, curr_date)
